from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from src.database import get_db
from src.models import Domain
from src.elicitation.state_machine import ElicitationState, ElicitationPhase
from src.elicitation.chat_handler import ElicitationChatHandler
from src.elicitation.completeness import CompletenessChecker
from src.elicitation.pddl_generator import PDDLGenerator
from src.llm.base import LLMProvider
from src.llm.router import LLMRouter

router = APIRouter()


# Session data structure to store state and domain_id
class SessionData:
    def __init__(self, state: ElicitationState, domain_id: str | None = None):
        self.state = state
        self.domain_id = domain_id


# In-memory session storage (would use Redis in production)
_sessions: dict[str, SessionData] = {}


class StartSessionRequest(BaseModel):
    domain_id: str | None = None


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


class MessageInfo(BaseModel):
    role: str
    content: str
    timestamp: str


class ChatResponse(BaseModel):
    session_id: str
    message: str
    phase: str
    completion_percentage: float
    is_complete: bool
    domain_pddl: str | None = None
    problem_pddl: str | None = None


class SessionInfo(BaseModel):
    session_id: str
    phase: str
    domain_name: str | None
    domain_id: str | None
    completion_percentage: float
    is_complete: bool
    messages: list[MessageInfo]
    elicitation_state: dict[str, Any] | None = None


@router.post("/start", response_model=SessionInfo)
async def start_session(
    request: StartSessionRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Start a new elicitation session, optionally linked to a domain."""
    session_id = str(uuid4())
    state = ElicitationState()
    domain_id = request.domain_id if request else None

    # If domain_id provided, load domain info
    if domain_id:
        try:
            domain_uuid = UUID(domain_id)
            result = await db.execute(select(Domain).where(Domain.id == domain_uuid))
            domain = result.scalar_one_or_none()
            if domain:
                state.domain_name = domain.name
                state.domain_description = domain.description
        except (ValueError, Exception):
            pass  # Invalid UUID or database error, ignore

    _sessions[session_id] = SessionData(state, domain_id)

    report = CompletenessChecker.check(state)

    return SessionInfo(
        session_id=session_id,
        phase=state.phase.value,
        domain_name=state.domain_name,
        domain_id=domain_id,
        completion_percentage=report.completion_percentage,
        is_complete=report.is_complete,
        messages=[MessageInfo(**m) for m in state.messages],
        elicitation_state=state.to_dict(),
    )


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest, db: AsyncSession = Depends(get_db)):
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

    session_data = _sessions[request.session_id]
    state = session_data.state
    domain_pddl = None
    problem_pddl = None

    # Try to use real LLM, fall back to mock if not configured
    try:
        router_instance = LLMRouter()  # Loads API keys from environment
        handler = ElicitationChatHandler(router_instance, LLMProvider.CLAUDE)
        response_message, state = await handler.handle_message(request.message, state)

        # If elicitation is complete, generate PDDL and save to domain
        if state.phase == ElicitationPhase.COMPLETE and session_data.domain_id:
            try:
                generator = PDDLGenerator(router_instance, LLMProvider.CLAUDE)
                domain_pddl, problem_pddl = await generator.generate_full(state)

                # Save PDDL to the domain in database
                domain_uuid = UUID(session_data.domain_id)
                result = await db.execute(select(Domain).where(Domain.id == domain_uuid))
                domain = result.scalar_one_or_none()
                if domain:
                    domain.domain_pddl = domain_pddl
                    domain.problem_pddl = problem_pddl
                    await db.commit()
            except Exception as e:
                # Log but don't fail the message response
                print(f"Failed to generate/save PDDL: {e}")

    except (ValueError, Exception) as e:
        # No LLM configured or error, use simple mock response
        state.add_message("user", request.message)
        response_message = f"I received your message about: {request.message[:50]}... Let me help you define your planning domain. (Note: Set ANTHROPIC_API_KEY in .env for AI responses)"
        state.add_message("assistant", response_message)

    session_data.state = state
    _sessions[request.session_id] = session_data
    report = CompletenessChecker.check(state)

    return ChatResponse(
        session_id=request.session_id,
        message=response_message,
        phase=state.phase.value,
        completion_percentage=report.completion_percentage,
        is_complete=report.is_complete,
        domain_pddl=domain_pddl,
        problem_pddl=problem_pddl,
    )


@router.get("/session/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """Get session information including messages."""
    if session_id not in _sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    session_data = _sessions[session_id]
    state = session_data.state
    report = CompletenessChecker.check(state)

    return SessionInfo(
        session_id=session_id,
        phase=state.phase.value,
        domain_name=state.domain_name,
        domain_id=session_data.domain_id,
        completion_percentage=report.completion_percentage,
        is_complete=report.is_complete,
        messages=[MessageInfo(**m) for m in state.messages],
        elicitation_state=state.to_dict(),
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


@router.post("/session/{session_id}/generate-pddl")
async def generate_pddl(session_id: str, db: AsyncSession = Depends(get_db)):
    """Manually trigger PDDL generation for a session."""
    if session_id not in _sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    session_data = _sessions[session_id]
    state = session_data.state

    try:
        router_instance = LLMRouter()
        generator = PDDLGenerator(router_instance, LLMProvider.CLAUDE)
        domain_pddl, problem_pddl = await generator.generate_full(state)

        # If linked to a domain, save the PDDL
        if session_data.domain_id:
            domain_uuid = UUID(session_data.domain_id)
            result = await db.execute(select(Domain).where(Domain.id == domain_uuid))
            domain = result.scalar_one_or_none()
            if domain:
                domain.domain_pddl = domain_pddl
                domain.problem_pddl = problem_pddl
                await db.commit()

        return {
            "domain_pddl": domain_pddl,
            "problem_pddl": problem_pddl,
            "saved_to_domain": session_data.domain_id is not None,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDDL: {str(e)}",
        )
