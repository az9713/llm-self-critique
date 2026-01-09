from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.elicitation.state_machine import ElicitationState
from src.elicitation.chat_handler import ElicitationChatHandler
from src.elicitation.completeness import CompletenessChecker
from src.llm.base import LLMProvider
from src.llm.router import LLMRouter

router = APIRouter()

# In-memory session storage (would use Redis in production)
_sessions: dict[str, ElicitationState] = {}


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    message: str
    phase: str
    completion_percentage: float
    is_complete: bool


class SessionInfo(BaseModel):
    session_id: str
    phase: str
    domain_name: str | None
    completion_percentage: float
    is_complete: bool


@router.post("/start", response_model=SessionInfo)
async def start_session():
    """Start a new elicitation session."""
    session_id = str(uuid4())
    state = ElicitationState()
    _sessions[session_id] = state

    report = CompletenessChecker.check(state)

    return SessionInfo(
        session_id=session_id,
        phase=state.phase.value,
        domain_name=state.domain_name,
        completion_percentage=report.completion_percentage,
        is_complete=report.is_complete,
    )


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Send a message in an elicitation session."""
    if not request.session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id is required",
        )

    if request.session_id not in _sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    state = _sessions[request.session_id]

    # Try to use real LLM, fall back to mock if not configured
    try:
        router_instance = LLMRouter()  # Loads API keys from environment
        handler = ElicitationChatHandler(router_instance, LLMProvider.CLAUDE)
        response_message, state = await handler.handle_message(request.message, state)
    except (ValueError, Exception) as e:
        # No LLM configured or error, use simple mock response
        state.add_message("user", request.message)
        response_message = f"I received your message about: {request.message[:50]}... Let me help you define your planning domain. (Note: Set ANTHROPIC_API_KEY in .env for AI responses)"
        state.add_message("assistant", response_message)

    _sessions[request.session_id] = state
    report = CompletenessChecker.check(state)

    return ChatResponse(
        session_id=request.session_id,
        message=response_message,
        phase=state.phase.value,
        completion_percentage=report.completion_percentage,
        is_complete=report.is_complete,
    )


@router.get("/session/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """Get session information."""
    if session_id not in _sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    state = _sessions[session_id]
    report = CompletenessChecker.check(state)

    return SessionInfo(
        session_id=session_id,
        phase=state.phase.value,
        domain_name=state.domain_name,
        completion_percentage=report.completion_percentage,
        is_complete=report.is_complete,
    )


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete an elicitation session."""
    if session_id not in _sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    del _sessions[session_id]
    return {"status": "deleted"}
