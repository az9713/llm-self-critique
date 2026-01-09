from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from src.models.planning import Verdict, SessionStatus


class PlanningSessionCreate(BaseModel):
    domain_id: UUID
    problem_description: str
    provider: str = "claude"


class PlanningSessionResponse(BaseModel):
    id: UUID
    domain_id: UUID
    status: SessionStatus
    problem_description: str
    current_plan: str | None
    final_verdict: Verdict | None
    iteration_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlanIterationResponse(BaseModel):
    iteration: int
    plan: str
    verdict: Verdict
    confidence: float
    critique_summary: str | None


class PlanGenerationRequest(BaseModel):
    domain_pddl: str
    problem_pddl: str
    max_iterations: int = 5
    num_critique_samples: int = 5


class PlanGenerationResponse(BaseModel):
    session_id: UUID
    status: str
    plan: str
    verdict: Verdict
    iterations: int
    iteration_history: list[PlanIterationResponse]
