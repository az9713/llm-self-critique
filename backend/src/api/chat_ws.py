"""WebSocket endpoint for real-time chat with streaming responses."""

import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from src.database import async_session_maker
from src.models import Domain
from src.elicitation.chat_handler import ElicitationChatHandler
from src.elicitation.state_machine import ElicitationState, ElicitationStateMachine
from src.websocket import manager
from src.llm.router import LLMRouter
from src.llm.base import LLMProvider

router = APIRouter()


class StreamingChatHandler:
    """Chat handler that streams responses via WebSocket."""

    def __init__(
        self,
        websocket: WebSocket,
        session_id: str,
        llm_router: LLMRouter,
        provider: LLMProvider = LLMProvider.CLAUDE,
    ):
        self.ws = websocket
        self.session_id = session_id
        self.router = llm_router
        self.provider = provider
        self.state_machine = ElicitationStateMachine()

    async def send_event(self, event_type: str, data: dict):
        """Send an event to the client."""
        await self.ws.send_json({
            "type": event_type,
            "data": data,
        })

    async def handle_message(self, content: str) -> None:
        """Process a user message and stream the response."""
        # Add user message to state
        self.state_machine.add_message("user", content)

        await self.send_event("message_received", {
            "role": "user",
            "content": content,
        })

        # Indicate we're generating a response
        await self.send_event("generating", {})

        # Generate response (in production, this would stream tokens)
        response = await self._generate_response(content)

        # Update state based on response
        self.state_machine.add_message("assistant", response)

        # Send complete response
        await self.send_event("message", {
            "role": "assistant",
            "content": response,
        })

        # Send updated state
        await self.send_event("state_updated", {
            "phase": self.state_machine.state.phase.value,
            "domain_name": self.state_machine.state.domain_name,
            "objects": self.state_machine.state.objects,
            "predicates": self.state_machine.state.predicates,
            "actions": self.state_machine.state.actions,
        })

    async def _generate_response(self, user_message: str) -> str:
        """Generate a response based on the current state and user message."""
        from src.llm.base import LLMRequest

        state = self.state_machine.state
        phase = state.phase.value

        prompt = f"""You are helping a user define a planning domain for an AI planner.
Current phase: {phase}

Domain info gathered so far:
- Domain name: {state.domain_name or 'Not set'}
- Objects: {', '.join(state.objects) if state.objects else 'None'}
- Predicates: {', '.join(state.predicates) if state.predicates else 'None'}
- Actions: {', '.join(state.actions) if state.actions else 'None'}
- Initial state: {', '.join(state.initial_state) if state.initial_state else 'None'}
- Goal: {', '.join(state.goal_state) if state.goal_state else 'None'}

User message: {user_message}

Respond helpfully to guide the user through defining their planning domain.
Ask one question at a time about the current phase."""

        response = await self.router.complete(LLMRequest(
            prompt=prompt,
            provider=self.provider,
        ))

        return response.content

    def get_state(self) -> dict:
        """Get the current elicitation state."""
        state = self.state_machine.state
        return {
            "phase": state.phase.value,
            "domain_name": state.domain_name,
            "objects": state.objects,
            "predicates": state.predicates,
            "actions": state.actions,
            "initial_state": state.initial_state,
            "goal_state": state.goal_state,
            "messages": [
                {"role": m.role, "content": m.content}
                for m in state.messages
            ],
        }


# Store active chat sessions
_chat_sessions: dict[str, StreamingChatHandler] = {}


@router.websocket("/ws/chat/{domain_id}")
async def chat_websocket(websocket: WebSocket, domain_id: str):
    """WebSocket endpoint for real-time chat."""
    session_id = str(uuid.uuid4())

    await manager.connect(websocket, session_id)
    await manager.subscribe(session_id, f"domain:{domain_id}")

    try:
        # Verify domain exists
        async with async_session_maker() as db:
            result = await db.execute(
                select(Domain).where(Domain.id == domain_id)
            )
            domain = result.scalar_one_or_none()

            if not domain:
                await websocket.send_json({
                    "type": "error",
                    "message": "Domain not found",
                })
                return

        # Create chat handler (using mock key for now)
        try:
            llm_router = LLMRouter(api_keys={"claude": "mock-key"})
        except ValueError:
            llm_router = None

        handler = StreamingChatHandler(
            websocket=websocket,
            session_id=session_id,
            llm_router=llm_router,
            provider=LLMProvider.CLAUDE,
        )
        _chat_sessions[session_id] = handler

        # Send initial state
        await websocket.send_json({
            "type": "connected",
            "data": {
                "session_id": session_id,
                "domain_id": domain_id,
                "state": handler.get_state(),
            },
        })

        # Send welcome message
        await websocket.send_json({
            "type": "message",
            "data": {
                "role": "assistant",
                "content": f"Welcome! Let's define the planning domain for '{domain.name}'. "
                          f"Can you describe what kind of problem you're trying to solve?",
            },
        })

        # Message loop
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "message":
                content = data.get("content", "").strip()
                if content:
                    await handler.handle_message(content)

            elif data.get("type") == "get_state":
                await websocket.send_json({
                    "type": "state",
                    "data": handler.get_state(),
                })

            elif data.get("type") == "reset":
                handler.state_machine = ElicitationStateMachine()
                await websocket.send_json({
                    "type": "state_reset",
                    "data": handler.get_state(),
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except:
            pass
    finally:
        await manager.disconnect(session_id)
        if session_id in _chat_sessions:
            del _chat_sessions[session_id]
