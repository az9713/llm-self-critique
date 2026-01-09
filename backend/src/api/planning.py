from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import PlanningSession, PlanIteration, Domain
from src.models.planning import SessionStatus, Verdict
from src.schemas.planning import (
    PlanningSessionCreate,
    PlanningSessionResponse,
    PlanIterationResponse,
    PlanGenerationRequest,
    PlanGenerationResponse,
)
from src.critique.orchestrator import SelfCritiqueOrchestrator
from src.llm.base import LLMProvider
from src.llm.router import LLMRouter

router = APIRouter()


@router.post("", response_model=PlanningSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: PlanningSessionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new planning session."""
    # Verify domain exists
    result = await db.execute(select(Domain).where(Domain.id == session_data.domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    db_session = PlanningSession(
        domain_id=session_data.domain_id,
        problem_description=session_data.problem_description,
        status=SessionStatus.ELICITING,
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session


@router.get("", response_model=list[PlanningSessionResponse])
async def list_sessions(
    domain_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List all planning sessions, optionally filtered by domain."""
    query = select(PlanningSession)
    if domain_id:
        query = query.where(PlanningSession.domain_id == domain_id)
    query = query.order_by(PlanningSession.created_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{session_id}", response_model=PlanningSessionResponse)
async def get_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a specific planning session."""
    result = await db.execute(
        select(PlanningSession).where(PlanningSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/{session_id}/iterations", response_model=list[PlanIterationResponse])
async def get_iterations(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get all iterations for a planning session."""
    result = await db.execute(
        select(PlanIteration)
        .where(PlanIteration.session_id == session_id)
        .order_by(PlanIteration.iteration_number)
    )
    iterations = result.scalars().all()

    return [
        PlanIterationResponse(
            iteration=it.iteration_number,
            plan=it.plan,
            verdict=it.verdict,
            confidence=it.confidence,
            critique_summary=it.critique_summary,
        )
        for it in iterations
    ]


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a planning session."""
    result = await db.execute(
        select(PlanningSession).where(PlanningSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.delete(session)
    await db.commit()


@router.post("/{session_id}/generate", response_model=PlanGenerationResponse)
async def generate_plan(
    session_id: UUID,
    request: PlanGenerationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate and critique a plan for the session."""
    # Get session
    result = await db.execute(
        select(PlanningSession).where(PlanningSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update session status
    session.status = SessionStatus.PLANNING
    session.domain_pddl = request.domain_pddl
    session.problem_pddl = request.problem_pddl
    await db.commit()

    # Run self-critique orchestrator
    try:
        # In production, get API keys from config/environment
        router_instance = LLMRouter()  # Loads API keys from environment
        orchestrator = SelfCritiqueOrchestrator(
            llm_router=router_instance,
            provider=LLMProvider.CLAUDE,
            max_iterations=request.max_iterations,
            num_critique_samples=request.num_critique_samples,
        )

        plan_result = await orchestrator.run(
            domain_pddl=request.domain_pddl,
            problem_pddl=request.problem_pddl,
        )

        # Save iterations to database
        iteration_responses = []
        for hist in plan_result.iteration_history:
            iteration = PlanIteration(
                session_id=session_id,
                iteration_number=hist["iteration"],
                plan=hist["plan"],
                verdict=hist["vote_result"].majority_verdict,
                confidence=hist["vote_result"].confidence,
                critique_summary=hist["vote_result"].best_critique.error_reason,
            )
            db.add(iteration)

            iteration_responses.append(PlanIterationResponse(
                iteration=hist["iteration"],
                plan=hist["plan"],
                verdict=hist["vote_result"].majority_verdict,
                confidence=hist["vote_result"].confidence,
                critique_summary=hist["vote_result"].best_critique.error_reason,
            ))

        # Update session with final result
        session.status = SessionStatus.COMPLETE if plan_result.status == "valid" else SessionStatus.FAILED
        session.current_plan = plan_result.plan
        session.final_verdict = plan_result.final_verdict
        session.iteration_count = plan_result.iterations
        await db.commit()

        return PlanGenerationResponse(
            session_id=session_id,
            status=plan_result.status,
            plan=plan_result.plan,
            verdict=plan_result.final_verdict,
            iterations=plan_result.iterations,
            iteration_history=iteration_responses,
        )

    except Exception as e:
        session.status = SessionStatus.FAILED
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Plan generation failed: {str(e)}",
        )
