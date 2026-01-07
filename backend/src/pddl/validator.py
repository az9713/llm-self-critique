"""PDDL Validators for domain and problem validation."""

from dataclasses import dataclass, field
from typing import List, Optional, Set
from enum import Enum

from .parser import PDDLDomain, PDDLProblem, PDDLParseError, parse_domain, parse_problem


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    severity: ValidationSeverity
    message: str
    location: Optional[str] = None  # e.g., "action:pick-up", "predicate:on"


@dataclass
class ValidationResult:
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)

    def add_error(self, message: str, location: Optional[str] = None):
        self.issues.append(ValidationIssue(ValidationSeverity.ERROR, message, location))
        self.valid = False

    def add_warning(self, message: str, location: Optional[str] = None):
        self.issues.append(ValidationIssue(ValidationSeverity.WARNING, message, location))

    def add_info(self, message: str, location: Optional[str] = None):
        self.issues.append(ValidationIssue(ValidationSeverity.INFO, message, location))

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]


class DomainValidator:
    """Validates a PDDL domain for structural and semantic correctness."""

    def validate(self, domain: PDDLDomain) -> ValidationResult:
        """Validate a parsed PDDL domain."""
        result = ValidationResult(valid=True)

        # Check domain name
        if not domain.name:
            result.add_error("Domain must have a name")

        # Collect defined types
        defined_types = self._get_defined_types(domain)

        # Validate predicates
        self._validate_predicates(domain, defined_types, result)

        # Validate actions
        self._validate_actions(domain, defined_types, result)

        # Check for common issues
        self._check_common_issues(domain, result)

        return result

    def _get_defined_types(self, domain: PDDLDomain) -> Set[str]:
        """Get all defined types including 'object' as base type."""
        types = {"object"}  # 'object' is always implicitly defined
        for t in domain.types:
            types.add(t.name)
        return types

    def _validate_predicates(
        self,
        domain: PDDLDomain,
        defined_types: Set[str],
        result: ValidationResult,
    ):
        """Validate predicate definitions."""
        predicate_names = set()

        for pred in domain.predicates:
            # Check for duplicate predicates
            if pred.name in predicate_names:
                result.add_error(
                    f"Duplicate predicate definition: {pred.name}",
                    f"predicate:{pred.name}",
                )
            predicate_names.add(pred.name)

            # Validate parameter types
            for param_name, param_type in pred.parameters:
                if param_type and param_type not in defined_types:
                    result.add_error(
                        f"Predicate '{pred.name}' uses undefined type: {param_type}",
                        f"predicate:{pred.name}",
                    )

                # Check parameter naming convention
                if not param_name.startswith("?"):
                    result.add_warning(
                        f"Predicate '{pred.name}' parameter '{param_name}' should start with '?'",
                        f"predicate:{pred.name}",
                    )

    def _validate_actions(
        self,
        domain: PDDLDomain,
        defined_types: Set[str],
        result: ValidationResult,
    ):
        """Validate action definitions."""
        action_names = set()
        predicate_names = {p.name for p in domain.predicates}

        for action in domain.actions:
            # Check for duplicate actions
            if action.name in action_names:
                result.add_error(
                    f"Duplicate action definition: {action.name}",
                    f"action:{action.name}",
                )
            action_names.add(action.name)

            # Validate parameter types
            param_names = set()
            for param_name, param_type in action.parameters:
                if param_type and param_type not in defined_types:
                    result.add_error(
                        f"Action '{action.name}' uses undefined type: {param_type}",
                        f"action:{action.name}",
                    )

                # Check for duplicate parameters
                if param_name in param_names:
                    result.add_error(
                        f"Action '{action.name}' has duplicate parameter: {param_name}",
                        f"action:{action.name}",
                    )
                param_names.add(param_name)

            # Check that action has precondition and effect
            if not action.precondition:
                result.add_warning(
                    f"Action '{action.name}' has no precondition",
                    f"action:{action.name}",
                )

            if not action.effect:
                result.add_warning(
                    f"Action '{action.name}' has no effect",
                    f"action:{action.name}",
                )

            # Check that predicates used in action exist
            if action.precondition:
                self._check_predicates_in_expression(
                    action.precondition,
                    predicate_names,
                    f"action:{action.name}:precondition",
                    result,
                )

            if action.effect:
                self._check_predicates_in_expression(
                    action.effect,
                    predicate_names,
                    f"action:{action.name}:effect",
                    result,
                )

    def _check_predicates_in_expression(
        self,
        expression: str,
        predicate_names: Set[str],
        location: str,
        result: ValidationResult,
    ):
        """Check that predicates used in an expression are defined."""
        # Simple heuristic: look for words after '(' that aren't keywords
        import re

        keywords = {"and", "or", "not", "forall", "exists", "when", "imply"}
        # Find all words that appear after '('
        matches = re.findall(r"\(\s*([a-zA-Z][a-zA-Z0-9_-]*)", expression)

        for match in matches:
            if match.lower() not in keywords and match not in predicate_names:
                result.add_warning(
                    f"Possibly undefined predicate '{match}' used in {location}",
                    location,
                )

    def _check_common_issues(self, domain: PDDLDomain, result: ValidationResult):
        """Check for common domain definition issues."""
        # Check if typing requirement matches usage
        has_typing_requirement = any(
            r.name == ":typing" for r in domain.requirements
        )
        uses_types = len(domain.types) > 0 or any(
            any(p[1] is not None for p in pred.parameters)
            for pred in domain.predicates
        )

        if uses_types and not has_typing_requirement:
            result.add_warning(
                "Domain uses types but :typing requirement is not declared",
            )

        if has_typing_requirement and not uses_types:
            result.add_info(
                ":typing requirement declared but no types are used",
            )

        # Check for empty domain
        if not domain.predicates:
            result.add_warning("Domain has no predicates defined")

        if not domain.actions:
            result.add_warning("Domain has no actions defined")


class ProblemValidator:
    """Validates a PDDL problem against its domain."""

    def validate(
        self,
        problem: PDDLProblem,
        domain: Optional[PDDLDomain] = None,
    ) -> ValidationResult:
        """Validate a parsed PDDL problem."""
        result = ValidationResult(valid=True)

        # Check problem name
        if not problem.name:
            result.add_error("Problem must have a name")

        # Check domain reference
        if not problem.domain:
            result.add_error("Problem must reference a domain")

        # If domain is provided, validate against it
        if domain:
            self._validate_against_domain(problem, domain, result)
        else:
            result.add_info(
                "Domain not provided, skipping cross-validation"
            )

        # Validate objects
        self._validate_objects(problem, domain, result)

        # Check goal
        if not problem.goal:
            result.add_warning("Problem has no goal defined")

        return result

    def _validate_against_domain(
        self,
        problem: PDDLProblem,
        domain: PDDLDomain,
        result: ValidationResult,
    ):
        """Validate problem against its domain."""
        # Check domain name matches
        if problem.domain != domain.name:
            result.add_error(
                f"Problem references domain '{problem.domain}' but validating against '{domain.name}'"
            )

        # Get valid types from domain
        valid_types = {"object"}
        for t in domain.types:
            valid_types.add(t.name)

        # Check object types
        for obj in problem.objects:
            if obj.type and obj.type not in valid_types:
                result.add_error(
                    f"Object '{obj.name}' has undefined type: {obj.type}",
                    f"object:{obj.name}",
                )

        # Get predicate signatures
        predicates = {p.name: p for p in domain.predicates}

        # Check init facts use valid predicates
        for init_fact in problem.init:
            self._check_fact_validity(init_fact, predicates, "init", result)

        # Check goal uses valid predicates
        if problem.goal:
            self._check_fact_validity(problem.goal, predicates, "goal", result)

    def _validate_objects(
        self,
        problem: PDDLProblem,
        domain: Optional[PDDLDomain],
        result: ValidationResult,
    ):
        """Validate object definitions."""
        object_names = set()

        for obj in problem.objects:
            # Check for duplicate objects
            if obj.name in object_names:
                result.add_error(
                    f"Duplicate object definition: {obj.name}",
                    f"object:{obj.name}",
                )
            object_names.add(obj.name)

    def _check_fact_validity(
        self,
        expression: str,
        predicates: dict,
        location: str,
        result: ValidationResult,
    ):
        """Check that a fact uses valid predicates."""
        import re

        keywords = {"and", "or", "not", "forall", "exists", "when", "imply"}
        matches = re.findall(r"\(\s*([a-zA-Z][a-zA-Z0-9_-]*)", expression)

        for match in matches:
            if match.lower() not in keywords and match not in predicates:
                result.add_warning(
                    f"Possibly undefined predicate '{match}' used in {location}",
                    location,
                )


def validate_domain_string(pddl_text: str) -> ValidationResult:
    """Validate a PDDL domain string."""
    result = ValidationResult(valid=True)

    try:
        domain = parse_domain(pddl_text)
        validator = DomainValidator()
        return validator.validate(domain)
    except PDDLParseError as e:
        result.add_error(f"Parse error: {str(e)}")
        return result


def validate_problem_string(
    problem_text: str,
    domain_text: Optional[str] = None,
) -> ValidationResult:
    """Validate a PDDL problem string."""
    result = ValidationResult(valid=True)
    domain_warning = None

    try:
        problem = parse_problem(problem_text)

        domain = None
        if domain_text:
            try:
                domain = parse_domain(domain_text)
            except PDDLParseError as e:
                domain_warning = f"Could not parse domain: {str(e)}"

        validator = ProblemValidator()
        validation_result = validator.validate(problem, domain)

        # Add domain warning if present
        if domain_warning:
            validation_result.add_warning(domain_warning)

        return validation_result
    except PDDLParseError as e:
        result.add_error(f"Parse error: {str(e)}")
        return result
