"""PDDL Parser for tokenizing and parsing PDDL syntax."""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


class TokenType(Enum):
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    KEYWORD = "KEYWORD"
    NAME = "NAME"
    VARIABLE = "VARIABLE"
    DASH = "DASH"
    COMMENT = "COMMENT"
    EOF = "EOF"


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int


@dataclass
class PDDLRequirement:
    name: str


@dataclass
class PDDLType:
    name: str
    parent: Optional[str] = None


@dataclass
class PDDLPredicate:
    name: str
    parameters: List[Tuple[str, Optional[str]]]  # (name, type)


@dataclass
class PDDLAction:
    name: str
    parameters: List[Tuple[str, Optional[str]]]
    precondition: Optional[str] = None
    effect: Optional[str] = None


@dataclass
class PDDLDomain:
    name: str
    requirements: List[PDDLRequirement] = field(default_factory=list)
    types: List[PDDLType] = field(default_factory=list)
    predicates: List[PDDLPredicate] = field(default_factory=list)
    actions: List[PDDLAction] = field(default_factory=list)
    raw_content: str = ""


@dataclass
class PDDLObject:
    name: str
    type: Optional[str] = None


@dataclass
class PDDLProblem:
    name: str
    domain: str
    objects: List[PDDLObject] = field(default_factory=list)
    init: List[str] = field(default_factory=list)
    goal: Optional[str] = None
    raw_content: str = ""


class PDDLLexer:
    """Tokenizer for PDDL syntax."""

    KEYWORDS = {
        "define", "domain", "problem",
        ":requirements", ":types", ":predicates", ":action",
        ":parameters", ":precondition", ":effect",
        ":objects", ":init", ":goal", ":domain",
        ":strips", ":typing", ":equality", ":negative-preconditions",
        ":disjunctive-preconditions", ":existential-preconditions",
        ":universal-preconditions", ":quantified-preconditions",
        ":conditional-effects", ":fluents", ":adl",
        "and", "or", "not", "forall", "exists", "when",
    }

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> List[Token]:
        tokens = []
        while self.pos < len(self.text):
            token = self._next_token()
            if token:
                if token.type != TokenType.COMMENT:
                    tokens.append(token)
        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens

    def _next_token(self) -> Optional[Token]:
        self._skip_whitespace()

        if self.pos >= len(self.text):
            return None

        char = self.text[self.pos]

        # Comments
        if char == ";":
            return self._read_comment()

        # Parentheses
        if char == "(":
            token = Token(TokenType.LPAREN, "(", self.line, self.column)
            self._advance()
            return token

        if char == ")":
            token = Token(TokenType.RPAREN, ")", self.line, self.column)
            self._advance()
            return token

        # Dash (for type declarations) - only if followed by whitespace then alpha
        if char == "-":
            # Check if it's a standalone dash (type separator) vs part of a name
            next_char = self._peek_next()
            if next_char.isspace() or next_char == "":
                token = Token(TokenType.DASH, "-", self.line, self.column)
                self._advance()
                return token

        # Variables
        if char == "?":
            return self._read_variable()

        # Keywords and names
        if char.isalpha() or char == ":" or char == "-":
            return self._read_name_or_keyword()

        # Skip unknown characters
        self._advance()
        return None

    def _read_comment(self) -> Token:
        start_col = self.column
        value = ""
        while self.pos < len(self.text) and self.text[self.pos] != "\n":
            value += self.text[self.pos]
            self._advance()
        return Token(TokenType.COMMENT, value, self.line, start_col)

    def _read_variable(self) -> Token:
        start_col = self.column
        value = ""
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] in "?_-"):
            value += self.text[self.pos]
            self._advance()
        return Token(TokenType.VARIABLE, value, self.line, start_col)

    def _read_name_or_keyword(self) -> Token:
        start_col = self.column
        value = ""
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] in ":_-"):
            value += self.text[self.pos]
            self._advance()

        lower_value = value.lower()
        if lower_value in self.KEYWORDS:
            return Token(TokenType.KEYWORD, lower_value, self.line, start_col)
        return Token(TokenType.NAME, value, self.line, start_col)

    def _skip_whitespace(self):
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            if self.text[self.pos] == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1

    def _advance(self):
        if self.pos < len(self.text):
            if self.text[self.pos] == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1

    def _peek_next(self) -> str:
        if self.pos + 1 < len(self.text):
            return self.text[self.pos + 1]
        return ""


class PDDLParser:
    """Parser for PDDL domain and problem files."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse_domain(self) -> PDDLDomain:
        """Parse a PDDL domain definition."""
        self._expect(TokenType.LPAREN)
        self._expect_keyword("define")

        # Domain name
        self._expect(TokenType.LPAREN)
        self._expect_keyword("domain")
        name = self._expect(TokenType.NAME).value
        self._expect(TokenType.RPAREN)

        domain = PDDLDomain(name=name)

        # Parse sections
        while self._current().type != TokenType.RPAREN:
            self._expect(TokenType.LPAREN)
            keyword = self._current()

            if keyword.value == ":requirements":
                self._advance()
                domain.requirements = self._parse_requirements()
            elif keyword.value == ":types":
                self._advance()
                domain.types = self._parse_types()
            elif keyword.value == ":predicates":
                self._advance()
                domain.predicates = self._parse_predicates()
            elif keyword.value == ":action":
                self._advance()
                domain.actions.append(self._parse_action())
            else:
                # Skip unknown section
                self._skip_until_rparen()

            self._expect(TokenType.RPAREN)

        self._expect(TokenType.RPAREN)
        return domain

    def parse_problem(self) -> PDDLProblem:
        """Parse a PDDL problem definition."""
        self._expect(TokenType.LPAREN)
        self._expect_keyword("define")

        # Problem name
        self._expect(TokenType.LPAREN)
        self._expect_keyword("problem")
        name = self._expect(TokenType.NAME).value
        self._expect(TokenType.RPAREN)

        problem = PDDLProblem(name=name, domain="")

        # Parse sections
        while self._current().type != TokenType.RPAREN:
            self._expect(TokenType.LPAREN)
            keyword = self._current()

            if keyword.value == ":domain":
                self._advance()
                problem.domain = self._expect(TokenType.NAME).value
            elif keyword.value == ":objects":
                self._advance()
                problem.objects = self._parse_objects()
            elif keyword.value == ":init":
                self._advance()
                problem.init = self._parse_init()
            elif keyword.value == ":goal":
                self._advance()
                problem.goal = self._parse_expression_string()
            else:
                # Skip unknown section
                self._skip_until_rparen()

            self._expect(TokenType.RPAREN)

        self._expect(TokenType.RPAREN)
        return problem

    def _parse_requirements(self) -> List[PDDLRequirement]:
        requirements = []
        while self._current().type == TokenType.KEYWORD and self._current().value.startswith(":"):
            requirements.append(PDDLRequirement(self._current().value))
            self._advance()
        return requirements

    def _parse_types(self) -> List[PDDLType]:
        types = []
        current_names = []

        while self._current().type not in (TokenType.RPAREN, TokenType.EOF):
            if self._current().type == TokenType.DASH:
                self._advance()
                parent = self._expect(TokenType.NAME).value
                for name in current_names:
                    types.append(PDDLType(name=name, parent=parent))
                current_names = []
            elif self._current().type == TokenType.NAME:
                current_names.append(self._current().value)
                self._advance()
            else:
                break

        # Any remaining names without parent
        for name in current_names:
            types.append(PDDLType(name=name))

        return types

    def _parse_predicates(self) -> List[PDDLPredicate]:
        predicates = []
        while self._current().type == TokenType.LPAREN:
            self._advance()
            name = self._expect(TokenType.NAME).value
            parameters = self._parse_parameters()
            self._expect(TokenType.RPAREN)
            predicates.append(PDDLPredicate(name=name, parameters=parameters))
        return predicates

    def _parse_parameters(self) -> List[Tuple[str, Optional[str]]]:
        params = []
        current_vars = []

        while self._current().type not in (TokenType.RPAREN, TokenType.EOF):
            if self._current().type == TokenType.VARIABLE:
                current_vars.append(self._current().value)
                self._advance()
            elif self._current().type == TokenType.DASH:
                self._advance()
                param_type = self._expect(TokenType.NAME).value
                for var in current_vars:
                    params.append((var, param_type))
                current_vars = []
            else:
                break

        # Any remaining vars without type
        for var in current_vars:
            params.append((var, None))

        return params

    def _parse_action(self) -> PDDLAction:
        name = self._expect(TokenType.NAME).value
        parameters = []
        precondition = None
        effect = None

        while self._current().type == TokenType.KEYWORD:
            keyword = self._current().value

            if keyword == ":parameters":
                self._advance()
                self._expect(TokenType.LPAREN)
                parameters = self._parse_parameters()
                self._expect(TokenType.RPAREN)
            elif keyword == ":precondition":
                self._advance()
                precondition = self._parse_expression_string()
            elif keyword == ":effect":
                self._advance()
                effect = self._parse_expression_string()
            else:
                break

        return PDDLAction(
            name=name,
            parameters=parameters,
            precondition=precondition,
            effect=effect,
        )

    def _parse_objects(self) -> List[PDDLObject]:
        objects = []
        current_names = []

        while self._current().type not in (TokenType.RPAREN, TokenType.EOF):
            if self._current().type == TokenType.DASH:
                self._advance()
                obj_type = self._expect(TokenType.NAME).value
                for name in current_names:
                    objects.append(PDDLObject(name=name, type=obj_type))
                current_names = []
            elif self._current().type == TokenType.NAME:
                current_names.append(self._current().value)
                self._advance()
            else:
                break

        # Any remaining names without type
        for name in current_names:
            objects.append(PDDLObject(name=name))

        return objects

    def _parse_init(self) -> List[str]:
        init_facts = []
        while self._current().type == TokenType.LPAREN:
            init_facts.append(self._parse_expression_string())
        return init_facts

    def _parse_expression_string(self) -> str:
        """Parse an expression and return it as a string."""
        if self._current().type != TokenType.LPAREN:
            return ""

        depth = 0
        parts = []
        start_pos = self.pos

        while self.pos < len(self.tokens):
            token = self._current()
            if token.type == TokenType.LPAREN:
                depth += 1
                parts.append("(")
            elif token.type == TokenType.RPAREN:
                depth -= 1
                parts.append(")")
                if depth == 0:
                    self._advance()
                    break
            else:
                parts.append(token.value)
            self._advance()

        return " ".join(parts)

    def _skip_until_rparen(self):
        depth = 1
        while depth > 0 and self._current().type != TokenType.EOF:
            if self._current().type == TokenType.LPAREN:
                depth += 1
            elif self._current().type == TokenType.RPAREN:
                depth -= 1
                if depth == 0:
                    return
            self._advance()

    def _current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, "", 0, 0)

    def _advance(self):
        self.pos += 1

    def _expect(self, token_type: TokenType) -> Token:
        token = self._current()
        if token.type != token_type:
            raise PDDLParseError(
                f"Expected {token_type.value}, got {token.type.value} at line {token.line}, column {token.column}"
            )
        self._advance()
        return token

    def _expect_keyword(self, keyword: str) -> Token:
        token = self._current()
        if token.type != TokenType.KEYWORD or token.value != keyword:
            raise PDDLParseError(
                f"Expected keyword '{keyword}', got '{token.value}' at line {token.line}, column {token.column}"
            )
        self._advance()
        return token


class PDDLParseError(Exception):
    """Exception raised for PDDL parsing errors."""
    pass


def parse_domain(pddl_text: str) -> PDDLDomain:
    """Parse a PDDL domain string."""
    lexer = PDDLLexer(pddl_text)
    tokens = lexer.tokenize()
    parser = PDDLParser(tokens)
    domain = parser.parse_domain()
    domain.raw_content = pddl_text
    return domain


def parse_problem(pddl_text: str) -> PDDLProblem:
    """Parse a PDDL problem string."""
    lexer = PDDLLexer(pddl_text)
    tokens = lexer.tokenize()
    parser = PDDLParser(tokens)
    problem = parser.parse_problem()
    problem.raw_content = pddl_text
    return problem
