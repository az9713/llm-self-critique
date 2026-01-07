"""Tests for PDDL validators."""

import pytest
from src.pddl.parser import parse_domain, parse_problem
from src.pddl.validator import (
    DomainValidator,
    ProblemValidator,
    ValidationResult,
    ValidationSeverity,
    validate_domain_string,
    validate_problem_string,
)


VALID_DOMAIN = """
(define (domain blocksworld)
  (:requirements :strips :typing)
  (:types block)
  (:predicates
    (on ?x - block ?y - block)
    (ontable ?x - block)
    (clear ?x - block)
    (holding ?x - block)
    (arm-empty)
  )
  (:action pick-up
    :parameters (?x - block)
    :precondition (and (clear ?x) (ontable ?x) (arm-empty))
    :effect (and (holding ?x) (not (ontable ?x)) (not (clear ?x)) (not (arm-empty)))
  )
  (:action put-down
    :parameters (?x - block)
    :precondition (holding ?x)
    :effect (and (ontable ?x) (clear ?x) (arm-empty) (not (holding ?x)))
  )
)
"""

VALID_PROBLEM = """
(define (problem blocks-4-0)
  (:domain blocksworld)
  (:objects b1 b2 b3 b4 - block)
  (:init
    (clear b1)
    (clear b4)
    (ontable b2)
    (ontable b3)
    (on b1 b2)
    (on b4 b3)
    (arm-empty)
  )
  (:goal (and (on b1 b2) (on b2 b3) (on b3 b4)))
)
"""


class TestDomainValidator:
    def test_valid_domain(self):
        domain = parse_domain(VALID_DOMAIN)
        validator = DomainValidator()
        result = validator.validate(domain)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_empty_domain_name(self):
        domain = parse_domain(VALID_DOMAIN)
        domain.name = ""
        validator = DomainValidator()
        result = validator.validate(domain)

        assert result.valid is False
        assert any("name" in issue.message.lower() for issue in result.errors)

    def test_duplicate_predicate(self):
        domain = parse_domain(VALID_DOMAIN)
        # Add duplicate predicate
        from src.pddl.parser import PDDLPredicate
        domain.predicates.append(PDDLPredicate(name="clear", parameters=[("?x", "block")]))

        validator = DomainValidator()
        result = validator.validate(domain)

        assert result.valid is False
        assert any("duplicate predicate" in issue.message.lower() for issue in result.errors)

    def test_undefined_type_in_predicate(self):
        domain = parse_domain(VALID_DOMAIN)
        from src.pddl.parser import PDDLPredicate
        domain.predicates.append(PDDLPredicate(name="test", parameters=[("?x", "undefined_type")]))

        validator = DomainValidator()
        result = validator.validate(domain)

        assert result.valid is False
        assert any("undefined type" in issue.message.lower() for issue in result.errors)

    def test_duplicate_action(self):
        domain = parse_domain(VALID_DOMAIN)
        from src.pddl.parser import PDDLAction
        domain.actions.append(PDDLAction(name="pick-up", parameters=[("?x", "block")]))

        validator = DomainValidator()
        result = validator.validate(domain)

        assert result.valid is False
        assert any("duplicate action" in issue.message.lower() for issue in result.errors)

    def test_undefined_type_in_action(self):
        domain = parse_domain(VALID_DOMAIN)
        from src.pddl.parser import PDDLAction
        domain.actions.append(PDDLAction(
            name="test-action",
            parameters=[("?x", "nonexistent_type")],
            precondition="(clear ?x)",
            effect="(holding ?x)"
        ))

        validator = DomainValidator()
        result = validator.validate(domain)

        assert result.valid is False
        assert any("undefined type" in issue.message.lower() for issue in result.errors)

    def test_duplicate_parameter_in_action(self):
        domain = parse_domain(VALID_DOMAIN)
        from src.pddl.parser import PDDLAction
        domain.actions.append(PDDLAction(
            name="bad-action",
            parameters=[("?x", "block"), ("?x", "block")],
            precondition="(clear ?x)",
            effect="(holding ?x)"
        ))

        validator = DomainValidator()
        result = validator.validate(domain)

        assert result.valid is False
        assert any("duplicate parameter" in issue.message.lower() for issue in result.errors)

    def test_action_without_precondition_warning(self):
        domain = parse_domain(VALID_DOMAIN)
        from src.pddl.parser import PDDLAction
        domain.actions.append(PDDLAction(
            name="no-precond",
            parameters=[("?x", "block")],
            precondition=None,
            effect="(holding ?x)"
        ))

        validator = DomainValidator()
        result = validator.validate(domain)

        assert any("no precondition" in issue.message.lower() for issue in result.warnings)

    def test_action_without_effect_warning(self):
        domain = parse_domain(VALID_DOMAIN)
        from src.pddl.parser import PDDLAction
        domain.actions.append(PDDLAction(
            name="no-effect",
            parameters=[("?x", "block")],
            precondition="(clear ?x)",
            effect=None
        ))

        validator = DomainValidator()
        result = validator.validate(domain)

        assert any("no effect" in issue.message.lower() for issue in result.warnings)

    def test_typing_requirement_warning(self):
        """Test warning when types are used but :typing not declared."""
        domain_without_typing = """
        (define (domain test)
          (:requirements :strips)
          (:types block)
          (:predicates (on ?x - block ?y - block))
        )
        """
        domain = parse_domain(domain_without_typing)
        validator = DomainValidator()
        result = validator.validate(domain)

        assert any(":typing" in issue.message for issue in result.warnings)

    def test_empty_predicates_warning(self):
        domain_no_predicates = """
        (define (domain empty)
          (:requirements :strips)
          (:action noop
            :parameters ()
            :precondition (and)
            :effect (and)
          )
        )
        """
        domain = parse_domain(domain_no_predicates)
        validator = DomainValidator()
        result = validator.validate(domain)

        assert any("no predicates" in issue.message.lower() for issue in result.warnings)

    def test_empty_actions_warning(self):
        domain_no_actions = """
        (define (domain empty)
          (:requirements :strips)
          (:predicates (fact))
        )
        """
        domain = parse_domain(domain_no_actions)
        validator = DomainValidator()
        result = validator.validate(domain)

        assert any("no actions" in issue.message.lower() for issue in result.warnings)


class TestProblemValidator:
    def test_valid_problem(self):
        problem = parse_problem(VALID_PROBLEM)
        domain = parse_domain(VALID_DOMAIN)
        validator = ProblemValidator()
        result = validator.validate(problem, domain)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_empty_problem_name(self):
        problem = parse_problem(VALID_PROBLEM)
        problem.name = ""
        validator = ProblemValidator()
        result = validator.validate(problem)

        assert result.valid is False
        assert any("name" in issue.message.lower() for issue in result.errors)

    def test_empty_domain_reference(self):
        problem = parse_problem(VALID_PROBLEM)
        problem.domain = ""
        validator = ProblemValidator()
        result = validator.validate(problem)

        assert result.valid is False
        assert any("domain" in issue.message.lower() for issue in result.errors)

    def test_domain_name_mismatch(self):
        problem = parse_problem(VALID_PROBLEM)
        problem.domain = "wrong_domain"
        domain = parse_domain(VALID_DOMAIN)

        validator = ProblemValidator()
        result = validator.validate(problem, domain)

        assert result.valid is False
        assert any("wrong_domain" in issue.message for issue in result.errors)

    def test_undefined_object_type(self):
        problem = parse_problem(VALID_PROBLEM)
        domain = parse_domain(VALID_DOMAIN)
        from src.pddl.parser import PDDLObject
        problem.objects.append(PDDLObject(name="x", type="undefined_type"))

        validator = ProblemValidator()
        result = validator.validate(problem, domain)

        assert result.valid is False
        assert any("undefined type" in issue.message.lower() for issue in result.errors)

    def test_duplicate_object(self):
        problem = parse_problem(VALID_PROBLEM)
        from src.pddl.parser import PDDLObject
        problem.objects.append(PDDLObject(name="b1", type="block"))

        validator = ProblemValidator()
        result = validator.validate(problem)

        assert result.valid is False
        assert any("duplicate object" in issue.message.lower() for issue in result.errors)

    def test_no_goal_warning(self):
        problem = parse_problem(VALID_PROBLEM)
        problem.goal = None

        validator = ProblemValidator()
        result = validator.validate(problem)

        assert any("no goal" in issue.message.lower() for issue in result.warnings)

    def test_validation_without_domain(self):
        problem = parse_problem(VALID_PROBLEM)
        validator = ProblemValidator()
        result = validator.validate(problem)

        # Should have info message about skipping cross-validation
        assert any("domain not provided" in issue.message.lower() for issue in result.issues)


class TestValidationHelpers:
    def test_validate_domain_string_valid(self):
        result = validate_domain_string(VALID_DOMAIN)
        assert result.valid is True

    def test_validate_domain_string_invalid_syntax(self):
        result = validate_domain_string("(define (domain test")
        assert result.valid is False
        assert any("parse error" in issue.message.lower() for issue in result.errors)

    def test_validate_problem_string_valid(self):
        result = validate_problem_string(VALID_PROBLEM, VALID_DOMAIN)
        assert result.valid is True

    def test_validate_problem_string_without_domain(self):
        result = validate_problem_string(VALID_PROBLEM)
        assert result.valid is True  # Valid problem syntax, just no cross-validation

    def test_validate_problem_string_invalid_syntax(self):
        result = validate_problem_string("(define (problem test")
        assert result.valid is False
        assert any("parse error" in issue.message.lower() for issue in result.errors)

    def test_validate_problem_string_invalid_domain(self):
        result = validate_problem_string(VALID_PROBLEM, "(invalid domain")
        # Should warn about domain parse error but still validate problem
        assert any("could not parse domain" in issue.message.lower() for issue in result.warnings)


class TestValidationResult:
    def test_add_error_sets_valid_false(self):
        result = ValidationResult(valid=True)
        result.add_error("Test error")

        assert result.valid is False
        assert len(result.errors) == 1

    def test_add_warning_keeps_valid_true(self):
        result = ValidationResult(valid=True)
        result.add_warning("Test warning")

        assert result.valid is True
        assert len(result.warnings) == 1

    def test_add_info(self):
        result = ValidationResult(valid=True)
        result.add_info("Test info")

        assert result.valid is True
        assert len([i for i in result.issues if i.severity == ValidationSeverity.INFO]) == 1

    def test_location_tracking(self):
        result = ValidationResult(valid=True)
        result.add_error("Test error", location="action:pick-up")

        assert result.errors[0].location == "action:pick-up"
