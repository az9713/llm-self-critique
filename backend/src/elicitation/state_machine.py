from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class ElicitationPhase(str, Enum):
    """Phases of the domain elicitation conversation."""
    INTRO = "intro"           # Initial greeting, understand the domain
    OBJECTS = "objects"       # Identify objects/entities in the domain
    PREDICATES = "predicates" # Identify properties and relationships
    ACTIONS = "actions"       # Identify possible actions
    INITIAL = "initial"       # Define the initial state
    GOAL = "goal"             # Define the goal state
    REVIEW = "review"         # Review and confirm the domain
    COMPLETE = "complete"     # Elicitation complete


@dataclass
class ElicitationState:
    """State of the domain elicitation conversation."""
    phase: ElicitationPhase = ElicitationPhase.INTRO
    domain_name: str | None = None
    domain_description: str | None = None
    objects: list[str] = field(default_factory=list)
    predicates: list[str] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    initial_state: list[str] = field(default_factory=list)
    goal_state: list[str] = field(default_factory=list)
    messages: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Serialize state to dictionary."""
        return {
            "phase": self.phase.value,
            "domain_name": self.domain_name,
            "domain_description": self.domain_description,
            "objects": self.objects,
            "predicates": self.predicates,
            "actions": self.actions,
            "initial_state": self.initial_state,
            "goal_state": self.goal_state,
            "messages": self.messages,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ElicitationState":
        """Deserialize state from dictionary."""
        return cls(
            phase=ElicitationPhase(data.get("phase", "intro")),
            domain_name=data.get("domain_name"),
            domain_description=data.get("domain_description"),
            objects=data.get("objects", []),
            predicates=data.get("predicates", []),
            actions=data.get("actions", []),
            initial_state=data.get("initial_state", []),
            goal_state=data.get("goal_state", []),
            messages=data.get("messages", []),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.utcnow(),
        )


class ElicitationStateMachine:
    """State machine for managing elicitation conversation flow."""

    # Valid phase transitions
    TRANSITIONS = {
        ElicitationPhase.INTRO: [ElicitationPhase.OBJECTS],
        ElicitationPhase.OBJECTS: [ElicitationPhase.PREDICATES, ElicitationPhase.INTRO],
        ElicitationPhase.PREDICATES: [ElicitationPhase.ACTIONS, ElicitationPhase.OBJECTS],
        ElicitationPhase.ACTIONS: [ElicitationPhase.INITIAL, ElicitationPhase.PREDICATES],
        ElicitationPhase.INITIAL: [ElicitationPhase.GOAL, ElicitationPhase.ACTIONS],
        ElicitationPhase.GOAL: [ElicitationPhase.REVIEW, ElicitationPhase.INITIAL],
        ElicitationPhase.REVIEW: [ElicitationPhase.COMPLETE, ElicitationPhase.INTRO],
        ElicitationPhase.COMPLETE: [],
    }

    def transition(self, state: ElicitationState, target_phase: ElicitationPhase) -> ElicitationState:
        """Transition to a new phase if valid."""
        valid_targets = self.TRANSITIONS.get(state.phase, [])

        if target_phase not in valid_targets and target_phase != state.phase:
            raise ValueError(
                f"Invalid transition from {state.phase.value} to {target_phase.value}. "
                f"Valid targets: {[p.value for p in valid_targets]}"
            )

        state.phase = target_phase
        state.updated_at = datetime.utcnow()
        return state

    def can_transition(self, state: ElicitationState, target_phase: ElicitationPhase) -> bool:
        """Check if a transition is valid."""
        valid_targets = self.TRANSITIONS.get(state.phase, [])
        return target_phase in valid_targets or target_phase == state.phase
