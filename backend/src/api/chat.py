from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from src.database import get_db
from src.models import Domain, ChatSession
from src.elicitation.state_machine import ElicitationState, ElicitationPhase
from src.elicitation.chat_handler import ElicitationChatHandler
from src.elicitation.completeness import CompletenessChecker
from src.elicitation.pddl_generator import PDDLGenerator
from src.llm.base import LLMProvider
from src.llm.router import LLMRouter

router = APIRouter()


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


def db_session_to_state(db_session: ChatSession) -> ElicitationState:
    """Convert a ChatSession database model to ElicitationState."""
    state = ElicitationState()
    state.phase = ElicitationPhase(db_session.phase)
    state.domain_name = db_session.domain_name
    state.domain_description = db_session.domain_description
    state.objects = db_session.objects or []
    state.predicates = db_session.predicates or []
    state.actions = db_session.actions or []
    state.initial_state = db_session.initial_state or []
    state.goal_state = db_session.goal_state or []
    state.messages = db_session.messages or []
    return state


def state_to_db_updates(state: ElicitationState) -> dict:
    """Convert ElicitationState to a dict of database column updates."""
    return {
        "phase": state.phase.value,
        "domain_name": state.domain_name,
        "domain_description": state.domain_description,
        "objects": state.objects,
        "predicates": state.predicates,
        "actions": state.actions,
        "initial_state": state.initial_state,
        "goal_state": state.goal_state,
        "messages": state.messages,
    }


async def get_chat_session_by_id(
    session_id: str, db: AsyncSession
) -> ChatSession | None:
    """Load a ChatSession from database by ID, returning None if not found."""
    try:
        session_uuid = UUID(session_id)
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_uuid)
        )
        return result.scalar_one_or_none()
    except ValueError:
        return None


@router.post("/start", response_model=SessionInfo)
async def start_session(
    request: StartSessionRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Start a new elicitation session, optionally linked to a domain.

    If a domain_id is provided and a session already exists for that domain,
    returns the existing session instead of creating a new one.
    """
    domain_id = request.domain_id if request else None

    # Check for existing session by domain_id
    if domain_id:
        try:
            domain_uuid = UUID(domain_id)
            result = await db.execute(
                select(ChatSession).where(ChatSession.domain_id == domain_uuid)
            )
            existing_session = result.scalar_one_or_none()

            if existing_session:
                # Return existing session
                state = db_session_to_state(existing_session)
                report = CompletenessChecker.check(state)
                return SessionInfo(
                    session_id=str(existing_session.id),
                    phase=state.phase.value,
                    domain_name=state.domain_name,
                    domain_id=str(existing_session.domain_id) if existing_session.domain_id else None,
                    completion_percentage=report.completion_percentage,
                    is_complete=report.is_complete,
                    messages=[MessageInfo(**m) for m in state.messages],
                    elicitation_state=state.to_dict(),
                )
        except (ValueError, Exception):
            pass  # Invalid UUID, create new session

    # Create new session
    state = ElicitationState()

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

    # Create database session
    db_session = ChatSession(
        domain_id=UUID(domain_id) if domain_id else None,
        phase=state.phase.value,
        domain_name=state.domain_name,
        domain_description=state.domain_description,
        objects=state.objects,
        predicates=state.predicates,
        actions=state.actions,
        initial_state=state.initial_state,
        goal_state=state.goal_state,
        messages=state.messages,
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)

    report = CompletenessChecker.check(state)

    return SessionInfo(
        session_id=str(db_session.id),
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

    db_session = await get_chat_session_by_id(request.session_id, db)
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    state = db_session_to_state(db_session)
    domain_id = str(db_session.domain_id) if db_session.domain_id else None
    domain_pddl = None
    problem_pddl = None

    # Try to use real LLM, fall back to mock if not configured
    try:
        router_instance = LLMRouter()  # Loads API keys from environment
        handler = ElicitationChatHandler(router_instance, LLMProvider.CLAUDE)
        response_message, state = await handler.handle_message(request.message, state)

        # If elicitation is complete, generate PDDL and save to domain
        if state.phase == ElicitationPhase.COMPLETE and domain_id:
            try:
                generator = PDDLGenerator(router_instance, LLMProvider.CLAUDE)
                domain_pddl, problem_pddl = await generator.generate_full(state)

                # Save PDDL to the domain in database
                domain_uuid = UUID(domain_id)
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

    # Update database session
    updates = state_to_db_updates(state)
    for key, value in updates.items():
        setattr(db_session, key, value)
    await db.commit()

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
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get session information including messages."""
    db_session = await get_chat_session_by_id(session_id, db)
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    state = db_session_to_state(db_session)
    report = CompletenessChecker.check(state)

    return SessionInfo(
        session_id=session_id,
        phase=state.phase.value,
        domain_name=state.domain_name,
        domain_id=str(db_session.domain_id) if db_session.domain_id else None,
        completion_percentage=report.completion_percentage,
        is_complete=report.is_complete,
        messages=[MessageInfo(**m) for m in state.messages],
        elicitation_state=state.to_dict(),
    )


@router.delete("/session/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an elicitation session."""
    db_session = await get_chat_session_by_id(session_id, db)
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    await db.delete(db_session)
    await db.commit()
    return {"status": "deleted"}


@router.post("/session/{session_id}/generate-pddl")
async def generate_pddl(session_id: str, db: AsyncSession = Depends(get_db)):
    """Manually trigger PDDL generation for a session."""
    db_session = await get_chat_session_by_id(session_id, db)
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    state = db_session_to_state(db_session)
    domain_id = str(db_session.domain_id) if db_session.domain_id else None

    try:
        router_instance = LLMRouter()
        generator = PDDLGenerator(router_instance, LLMProvider.CLAUDE)
        domain_pddl, problem_pddl = await generator.generate_full(state)

        # If linked to a domain, save the PDDL
        if domain_id:
            domain_uuid = UUID(domain_id)
            result = await db.execute(select(Domain).where(Domain.id == domain_uuid))
            domain = result.scalar_one_or_none()
            if domain:
                domain.domain_pddl = domain_pddl
                domain.problem_pddl = problem_pddl
                await db.commit()

        return {
            "domain_pddl": domain_pddl,
            "problem_pddl": problem_pddl,
            "saved_to_domain": domain_id is not None,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDDL: {str(e)}",
        )
