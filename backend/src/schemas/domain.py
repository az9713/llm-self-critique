from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class DomainCreate(BaseModel):
    workspace_id: UUID
    name: str
    description: str


class DomainResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    description: str
    pddl_definition: str | None
    is_public: bool
    is_template: bool
    created_at: datetime

    model_config = {"from_attributes": True}
