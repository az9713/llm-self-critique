"""Tests for PDDL parser."""

import pytest
from src.pddl.parser import (
    PDDLLexer,
    PDDLParser,
    PDDLParseError,
    parse_domain,
    parse_problem,
    TokenType,
)


SAMPLE_DOMAIN = """
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

SAMPLE_PROBLEM = """
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


class TestLexer:
    def test_tokenize_simple(self):
        lexer = PDDLLexer("(define)")
        tokens = lexer.tokenize()

        assert len(tokens) == 4  # LPAREN, KEYWORD, RPAREN, EOF
        assert tokens[0].type == TokenType.LPAREN
        assert tokens[1].type == TokenType.KEYWORD
        assert tokens[1].value == "define"
        assert tokens[2].type == TokenType.RPAREN

    def test_tokenize_variable(self):
        lexer = PDDLLexer("?x ?var-name")
        tokens = lexer.tokenize()

        assert tokens[0].type == TokenType.VARIABLE
        assert tokens[0].value == "?x"
        assert tokens[1].type == TokenType.VARIABLE
        assert tokens[1].value == "?var-name"

    def test_tokenize_with_comments(self):
        lexer = PDDLLexer("; comment\n(define)")
        tokens = lexer.tokenize()

        # Comments are skipped
        assert tokens[0].type == TokenType.LPAREN

    def test_tokenize_types(self):
        lexer = PDDLLexer("block - object")
        tokens = lexer.tokenize()

        assert tokens[0].type == TokenType.NAME
        assert tokens[0].value == "block"
        assert tokens[1].type == TokenType.DASH
        assert tokens[2].type == TokenType.NAME
        assert tokens[2].value == "object"

    def test_tokenize_hyphenated_name(self):
        lexer = PDDLLexer("arm-empty")
        tokens = lexer.tokenize()

        # Hyphenated names should be single tokens
        assert tokens[0].type == TokenType.NAME
        assert tokens[0].value == "arm-empty"


class TestDomainParser:
    def test_parse_domain_name(self):
        domain = parse_domain(SAMPLE_DOMAIN)

        assert domain.name == "blocksworld"

    def test_parse_requirements(self):
        domain = parse_domain(SAMPLE_DOMAIN)

        assert len(domain.requirements) == 2
        req_names = [r.name for r in domain.requirements]
        assert ":strips" in req_names
        assert ":typing" in req_names

    def test_parse_types(self):
        domain = parse_domain(SAMPLE_DOMAIN)

        assert len(domain.types) == 1
        assert domain.types[0].name == "block"

    def test_parse_predicates(self):
        domain = parse_domain(SAMPLE_DOMAIN)

        assert len(domain.predicates) == 5
        pred_names = [p.name for p in domain.predicates]
        assert "on" in pred_names
        assert "ontable" in pred_names
        assert "clear" in pred_names
        assert "holding" in pred_names
        assert "arm-empty" in pred_names

    def test_parse_predicate_parameters(self):
        domain = parse_domain(SAMPLE_DOMAIN)

        on_pred = next(p for p in domain.predicates if p.name == "on")
        assert len(on_pred.parameters) == 2
        assert on_pred.parameters[0] == ("?x", "block")
        assert on_pred.parameters[1] == ("?y", "block")

    def test_parse_actions(self):
        domain = parse_domain(SAMPLE_DOMAIN)

        assert len(domain.actions) == 2
        action_names = [a.name for a in domain.actions]
        assert "pick-up" in action_names
        assert "put-down" in action_names

    def test_parse_action_parameters(self):
        domain = parse_domain(SAMPLE_DOMAIN)

        pick_up = next(a for a in domain.actions if a.name == "pick-up")
        assert len(pick_up.parameters) == 1
        assert pick_up.parameters[0] == ("?x", "block")

    def test_parse_action_precondition(self):
        domain = parse_domain(SAMPLE_DOMAIN)

        pick_up = next(a for a in domain.actions if a.name == "pick-up")
        assert pick_up.precondition is not None
        assert "clear" in pick_up.precondition
        assert "ontable" in pick_up.precondition

    def test_parse_action_effect(self):
        domain = parse_domain(SAMPLE_DOMAIN)

        pick_up = next(a for a in domain.actions if a.name == "pick-up")
        assert pick_up.effect is not None
        assert "holding" in pick_up.effect


class TestProblemParser:
    def test_parse_problem_name(self):
        problem = parse_problem(SAMPLE_PROBLEM)

        assert problem.name == "blocks-4-0"

    def test_parse_problem_domain(self):
        problem = parse_problem(SAMPLE_PROBLEM)

        assert problem.domain == "blocksworld"

    def test_parse_objects(self):
        problem = parse_problem(SAMPLE_PROBLEM)

        assert len(problem.objects) == 4
        obj_names = [o.name for o in problem.objects]
        assert "b1" in obj_names
        assert "b2" in obj_names
        assert "b3" in obj_names
        assert "b4" in obj_names

    def test_parse_objects_with_types(self):
        problem = parse_problem(SAMPLE_PROBLEM)

        for obj in problem.objects:
            assert obj.type == "block"

    def test_parse_init(self):
        problem = parse_problem(SAMPLE_PROBLEM)

        assert len(problem.init) == 7

    def test_parse_goal(self):
        problem = parse_problem(SAMPLE_PROBLEM)

        assert problem.goal is not None
        assert "on" in problem.goal


class TestParseErrors:
    def test_invalid_syntax(self):
        with pytest.raises(PDDLParseError):
            parse_domain("(define (domain test")  # Missing closing parens

    def test_missing_keyword(self):
        with pytest.raises(PDDLParseError):
            parse_domain("(notdefine (domain test))")
