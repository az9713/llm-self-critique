from dataclasses import dataclass, field

from src.elicitation.state_machine import ElicitationState, ElicitationPhase


@dataclass
class CompletenessReport:
    """Report on the completeness of elicitation state."""
    is_complete: bool
    missing: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    completion_percentage: float = 0.0


class CompletenessChecker:
    """Check if enough information has been collected for PDDL generation."""

    REQUIRED_FIELDS = [
        ("domain_name", "Domain name is required"),
        ("objects", "At least one object/entity must be defined"),
        ("predicates", "At least one predicate (property/relationship) must be defined"),
        ("actions", "At least one action must be defined"),
        ("initial_state", "Initial state must be defined"),
        ("goal_state", "Goal state must be defined"),
    ]

    SUGGESTIONS = {
        "domain_name": "What would you like to name this planning domain?",
        "objects": "What are the objects or entities in your domain? (e.g., blocks, rooms, items)",
        "predicates": "What properties or relationships exist? (e.g., 'block is on table', 'room is clean')",
        "actions": "What actions can be performed? (e.g., 'pick up block', 'move to room')",
        "initial_state": "What is the starting situation?",
        "goal_state": "What is your desired end goal?",
    }

    @classmethod
    def check(cls, state: ElicitationState) -> CompletenessReport:
        """Check the completeness of the elicitation state."""
        missing = []
        suggestions = []

        for field_name, description in cls.REQUIRED_FIELDS:
            value = getattr(state, field_name, None)
            if not value:
                missing.append(field_name)
                if field_name in cls.SUGGESTIONS:
                    suggestions.append(cls.SUGGESTIONS[field_name])

        total_fields = len(cls.REQUIRED_FIELDS)
        completed_fields = total_fields - len(missing)
        completion_percentage = (completed_fields / total_fields) * 100 if total_fields > 0 else 0

        return CompletenessReport(
            is_complete=len(missing) == 0,
            missing=missing,
            suggestions=suggestions,
            completion_percentage=completion_percentage,
        )

    @classmethod
    def get_next_phase(cls, state: ElicitationState) -> ElicitationPhase:
        """Determine the next phase based on current state and completeness."""
        report = cls.check(state)

        # Phase progression based on what's missing
        if state.phase == ElicitationPhase.INTRO:
            return ElicitationPhase.OBJECTS

        if state.phase == ElicitationPhase.OBJECTS:
            if state.objects:
                return ElicitationPhase.PREDICATES
            return ElicitationPhase.OBJECTS

        if state.phase == ElicitationPhase.PREDICATES:
            if state.predicates:
                return ElicitationPhase.ACTIONS
            return ElicitationPhase.PREDICATES

        if state.phase == ElicitationPhase.ACTIONS:
            if state.actions:
                return ElicitationPhase.INITIAL
            return ElicitationPhase.ACTIONS

        if state.phase == ElicitationPhase.INITIAL:
            if state.initial_state:
                return ElicitationPhase.GOAL
            return ElicitationPhase.INITIAL

        if state.phase == ElicitationPhase.GOAL:
            if state.goal_state:
                return ElicitationPhase.REVIEW
            return ElicitationPhase.GOAL

        if state.phase == ElicitationPhase.REVIEW:
            if report.is_complete:
                return ElicitationPhase.COMPLETE
            # Go back to fix missing info
            if "objects" in report.missing:
                return ElicitationPhase.OBJECTS
            if "predicates" in report.missing:
                return ElicitationPhase.PREDICATES
            if "actions" in report.missing:
                return ElicitationPhase.ACTIONS

        return state.phase
