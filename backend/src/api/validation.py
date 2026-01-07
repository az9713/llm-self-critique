"""API endpoints for PDDL validation."""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.pddl import (
    validate_domain_string,
    validate_problem_string,
    ValidationSeverity,
)


router = APIRouter(prefix="/api/validation", tags=["validation"])


class ValidationIssueResponse(BaseModel):
    severity: str
    message: str
    location: Optional[str] = None


class ValidationResponse(BaseModel):
    valid: bool
    issues: List[ValidationIssueResponse]
    error_count: int
    warning_count: int


class DomainValidationRequest(BaseModel):
    domain_pddl: str


class ProblemValidationRequest(BaseModel):
    problem_pddl: str
    domain_pddl: Optional[str] = None


class FullValidationRequest(BaseModel):
    domain_pddl: str
    problem_pddl: str


class FullValidationResponse(BaseModel):
    domain_valid: bool
    problem_valid: bool
    overall_valid: bool
    domain_issues: List[ValidationIssueResponse]
    problem_issues: List[ValidationIssueResponse]
    total_errors: int
    total_warnings: int


def _convert_result_to_response(result) -> ValidationResponse:
    """Convert a ValidationResult to ValidationResponse."""
    issues = [
        ValidationIssueResponse(
            severity=issue.severity.value,
            message=issue.message,
            location=issue.location,
        )
        for issue in result.issues
    ]
    return ValidationResponse(
        valid=result.valid,
        issues=issues,
        error_count=len(result.errors),
        warning_count=len(result.warnings),
    )


@router.post("/domain", response_model=ValidationResponse)
async def validate_domain(request: DomainValidationRequest) -> ValidationResponse:
    """Validate a PDDL domain definition.

    Returns validation result with any errors or warnings found.
    """
    if not request.domain_pddl.strip():
        raise HTTPException(status_code=400, detail="Domain PDDL cannot be empty")

    result = validate_domain_string(request.domain_pddl)
    return _convert_result_to_response(result)


@router.post("/problem", response_model=ValidationResponse)
async def validate_problem(request: ProblemValidationRequest) -> ValidationResponse:
    """Validate a PDDL problem definition.

    Optionally validates against a domain if provided.
    """
    if not request.problem_pddl.strip():
        raise HTTPException(status_code=400, detail="Problem PDDL cannot be empty")

    result = validate_problem_string(
        request.problem_pddl,
        request.domain_pddl,
    )
    return _convert_result_to_response(result)


@router.post("/full", response_model=FullValidationResponse)
async def validate_full(request: FullValidationRequest) -> FullValidationResponse:
    """Validate both domain and problem together.

    Performs cross-validation to ensure problem is compatible with domain.
    """
    if not request.domain_pddl.strip():
        raise HTTPException(status_code=400, detail="Domain PDDL cannot be empty")
    if not request.problem_pddl.strip():
        raise HTTPException(status_code=400, detail="Problem PDDL cannot be empty")

    # Validate domain
    domain_result = validate_domain_string(request.domain_pddl)

    # Validate problem against domain
    problem_result = validate_problem_string(
        request.problem_pddl,
        request.domain_pddl,
    )

    domain_issues = [
        ValidationIssueResponse(
            severity=issue.severity.value,
            message=issue.message,
            location=issue.location,
        )
        for issue in domain_result.issues
    ]

    problem_issues = [
        ValidationIssueResponse(
            severity=issue.severity.value,
            message=issue.message,
            location=issue.location,
        )
        for issue in problem_result.issues
    ]

    total_errors = len(domain_result.errors) + len(problem_result.errors)
    total_warnings = len(domain_result.warnings) + len(problem_result.warnings)

    return FullValidationResponse(
        domain_valid=domain_result.valid,
        problem_valid=problem_result.valid,
        overall_valid=domain_result.valid and problem_result.valid,
        domain_issues=domain_issues,
        problem_issues=problem_issues,
        total_errors=total_errors,
        total_warnings=total_warnings,
    )


@router.get("/health")
async def validation_health():
    """Health check for validation service."""
    return {"status": "healthy", "service": "pddl-validation"}
