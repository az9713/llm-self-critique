from enum import Enum


class SessionStatus(str, Enum):
    ELICITING = "eliciting"
    PLANNING = "planning"
    CRITIQUING = "critiquing"
    COMPLETE = "complete"
    FAILED = "failed"


class Verdict(str, Enum):
    CORRECT = "correct"
    WRONG = "wrong"
    GOAL_NOT_REACHED = "goal_not_reached"
