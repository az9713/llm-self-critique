"""Tests for PDDL validation API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


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
)
"""

VALID_PROBLEM = """
(define (problem blocks-4-0)
  (:domain blocksworld)
  (:objects b1 b2 b3 b4 - block)
  (:init
    (clear b1)
    (ontable b2)
    (on b1 b2)
    (arm-empty)
  )
  (:goal (and (on b1 b2)))
)
"""

INVALID_DOMAIN = "(define (domain test"  # Missing closing parens

INVALID_PROBLEM = "(define (problem test"  # Missing closing parens


class TestDomainValidation:
    def test_validate_valid_domain(self):
        response = client.post(
            "/api/validation/domain",
            json={"domain_pddl": VALID_DOMAIN},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["error_count"] == 0

    def test_validate_invalid_domain_syntax(self):
        response = client.post(
            "/api/validation/domain",
            json={"domain_pddl": INVALID_DOMAIN},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["error_count"] > 0
        assert any("parse error" in issue["message"].lower() for issue in data["issues"])

    def test_validate_empty_domain(self):
        response = client.post(
            "/api/validation/domain",
            json={"domain_pddl": ""},
        )
        assert response.status_code == 400

    def test_validate_whitespace_only_domain(self):
        response = client.post(
            "/api/validation/domain",
            json={"domain_pddl": "   "},
        )
        assert response.status_code == 400

    def test_domain_with_semantic_errors(self):
        domain_with_errors = """
        (define (domain test)
          (:requirements :strips)
          (:types block)
          (:predicates (on ?x - undefined_type ?y - block))
        )
        """
        response = client.post(
            "/api/validation/domain",
            json={"domain_pddl": domain_with_errors},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert any("undefined type" in issue["message"].lower() for issue in data["issues"])


class TestProblemValidation:
    def test_validate_valid_problem_without_domain(self):
        response = client.post(
            "/api/validation/problem",
            json={"problem_pddl": VALID_PROBLEM},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_validate_valid_problem_with_domain(self):
        response = client.post(
            "/api/validation/problem",
            json={
                "problem_pddl": VALID_PROBLEM,
                "domain_pddl": VALID_DOMAIN,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_validate_invalid_problem_syntax(self):
        response = client.post(
            "/api/validation/problem",
            json={"problem_pddl": INVALID_PROBLEM},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["error_count"] > 0

    def test_validate_empty_problem(self):
        response = client.post(
            "/api/validation/problem",
            json={"problem_pddl": ""},
        )
        assert response.status_code == 400

    def test_validate_problem_domain_mismatch(self):
        problem_wrong_domain = """
        (define (problem test)
          (:domain wrong_domain)
          (:objects b1 - block)
          (:init (clear b1))
          (:goal (clear b1))
        )
        """
        response = client.post(
            "/api/validation/problem",
            json={
                "problem_pddl": problem_wrong_domain,
                "domain_pddl": VALID_DOMAIN,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert any("wrong_domain" in issue["message"] for issue in data["issues"])


class TestFullValidation:
    def test_validate_full_valid(self):
        response = client.post(
            "/api/validation/full",
            json={
                "domain_pddl": VALID_DOMAIN,
                "problem_pddl": VALID_PROBLEM,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["domain_valid"] is True
        assert data["problem_valid"] is True
        assert data["overall_valid"] is True
        assert data["total_errors"] == 0

    def test_validate_full_invalid_domain(self):
        response = client.post(
            "/api/validation/full",
            json={
                "domain_pddl": INVALID_DOMAIN,
                "problem_pddl": VALID_PROBLEM,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["domain_valid"] is False
        assert data["overall_valid"] is False
        assert len(data["domain_issues"]) > 0

    def test_validate_full_invalid_problem(self):
        response = client.post(
            "/api/validation/full",
            json={
                "domain_pddl": VALID_DOMAIN,
                "problem_pddl": INVALID_PROBLEM,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["problem_valid"] is False
        assert data["overall_valid"] is False
        assert len(data["problem_issues"]) > 0

    def test_validate_full_empty_domain(self):
        response = client.post(
            "/api/validation/full",
            json={
                "domain_pddl": "",
                "problem_pddl": VALID_PROBLEM,
            },
        )
        assert response.status_code == 400

    def test_validate_full_empty_problem(self):
        response = client.post(
            "/api/validation/full",
            json={
                "domain_pddl": VALID_DOMAIN,
                "problem_pddl": "",
            },
        )
        assert response.status_code == 400


class TestValidationHealth:
    def test_health_check(self):
        response = client.get("/api/validation/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "pddl-validation"
