"""
Boolean Query Parser for Elasticsearch

This module provides a parser for boolean search queries that converts natural
language queries with boolean operators into Elasticsearch query DSL.

Features:
- Boolean operators: AND, OR, NOT (case-insensitive)
- Parentheses for grouping expressions
- Quoted strings for exact phrase matching
- Field-specific queries (e.g., 'skills:Python', 'location:Remote')
- Converts parsed query into Elasticsearch bool query DSL
- Comprehensive error handling with helpful error messages

The parser uses a recursive descent approach to build an abstract syntax tree
(AST) from the query string, then transforms the AST into Elasticsearch query DSL.

Example:
    >>> parser = QueryParser()
    >>> result = parser.parse('Python AND (Django OR Flask) NOT Java')
    >>> # Returns Elasticsearch query DSL with bool clauses
"""
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class TokenType(Enum):
    """Token types for query lexer."""

    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    LPAREN = "("
    RPAREN = ")"
    QUOTED = "QUOTED"
    WORD = "WORD"
    FIELD = "FIELD"
    EOF = "EOF"


@dataclass
class Token:
    """
    A token from the query lexer.

    Attributes:
        type: The token type
        value: The token value
        position: Position in the original query string
    """

    type: TokenType
    value: str
    position: int


class QueryLexer:
    """
    Lexical analyzer for boolean queries.

    Tokenizes the input query string into a stream of tokens that can be
    parsed by the QueryParser.
    """

    def __init__(self, query: str):
        """
        Initialize the lexer.

        Args:
            query: The query string to tokenize
        """
        self.query = query
        self.position = 0
        self.length = len(query)

    def tokenize(self) -> List[Token]:
        """
        Tokenize the query string.

        Returns:
            List of tokens

        Raises:
            ValueError: If the query contains invalid syntax
        """
        tokens = []

        while self.position < self.length:
            # Skip whitespace
            if self.query[self.position].isspace():
                self.position += 1
                continue

            # Parentheses
            if self.query[self.position] == '(':
                tokens.append(Token(TokenType.LPAREN, '(', self.position))
                self.position += 1
                continue

            if self.query[self.position] == ')':
                tokens.append(Token(TokenType.RPAREN, ')', self.position))
                self.position += 1
                continue

            # Quoted string
            if self.query[self.position] == '"':
                quoted_value = self._read_quoted_string()
                tokens.append(Token(TokenType.QUOTED, quoted_value, self.position))
                continue

            # Word or operator
            word = self._read_word()
            word_upper = word.upper()

            # Check for boolean operators
            if word_upper == 'AND':
                tokens.append(Token(TokenType.AND, word, self.position - len(word)))
            elif word_upper == 'OR':
                tokens.append(Token(TokenType.OR, word, self.position - len(word)))
            elif word_upper == 'NOT':
                tokens.append(Token(TokenType.NOT, word, self.position - len(word)))
            # Check for field-specific query (e.g., 'skills:Python')
            elif ':' in word:
                tokens.append(Token(TokenType.FIELD, word, self.position - len(word)))
            else:
                tokens.append(Token(TokenType.WORD, word, self.position - len(word)))

        # Add EOF token
        tokens.append(Token(TokenType.EOF, '', self.position))

        return tokens

    def _read_quoted_string(self) -> str:
        """
        Read a quoted string from the query.

        Returns:
            The quoted string content (without quotes)

        Raises:
            ValueError: If the quoted string is not properly closed
        """
        start_pos = self.position
        self.position += 1  # Skip opening quote

        value = []
        while self.position < self.length:
            if self.query[self.position] == '"':
                self.position += 1  # Skip closing quote
                return ''.join(value)

            if self.query[self.position] == '\\' and self.position + 1 < self.length:
                # Handle escaped characters
                self.position += 1
                value.append(self.query[self.position])
            else:
                value.append(self.query[self.position])

            self.position += 1

        raise ValueError(
            f"Unclosed quoted string at position {start_pos}: "
            f"missing closing quote"
        )

    def _read_word(self) -> str:
        """
        Read a word from the query.

        Returns:
            The word string
        """
        word = []

        while self.position < self.length:
            char = self.query[self.position]

            # Stop at whitespace or parentheses
            if char.isspace() or char in '()':
                break

            # Stop at unescaped quotes
            if char == '"':
                break

            word.append(char)
            self.position += 1

        return ''.join(word)


class ASTNode:
    """Base class for abstract syntax tree nodes."""

    def to_elasticsearch(self) -> Dict[str, Any]:
        """
        Convert this AST node to Elasticsearch query DSL.

        Returns:
            Elasticsearch query DSL dictionary
        """
        raise NotImplementedError


class TermNode(ASTNode):
    """AST node for a single search term."""

    def __init__(self, term: str, is_quoted: bool = False, field: Optional[str] = None):
        """
        Initialize a term node.

        Args:
            term: The search term
            is_quoted: Whether this is an exact phrase (quoted)
            field: Optional field name for field-specific search
        """
        self.term = term
        self.is_quoted = is_quoted
        self.field = field

    def to_elasticsearch(self) -> Dict[str, Any]:
        """Convert term to Elasticsearch query."""
        if self.field:
            # Field-specific query
            if self.is_quoted:
                return {"match_phrase": {self.field: self.term}}
            else:
                return {"match": {self.field: self.term}}
        else:
            # Multi-field query
            if self.is_quoted:
                return {
                    "multi_match": {
                        "query": self.term,
                        "type": "phrase",
                        "fields": ["raw_text^2", "skills^3", "education", "location"]
                    }
                }
            else:
                return {
                    "multi_match": {
                        "query": self.term,
                        "type": "best_fields",
                        "fields": ["raw_text^2", "skills^3", "education", "location"],
                        "operator": "or"
                    }
                }


class BoolNode(ASTNode):
    """AST node for boolean operations (AND, OR, NOT)."""

    def __init__(self, operator: str, operands: List[ASTNode]):
        """
        Initialize a bool node.

        Args:
            operator: The boolean operator (AND, OR, NOT)
            operands: List of child nodes
        """
        self.operator = operator.upper()
        self.operands = operands

    def to_elasticsearch(self) -> Dict[str, Any]:
        """Convert boolean operation to Elasticsearch query."""
        if self.operator == "AND":
            # All operands must match
            return {
                "bool": {
                    "must": [op.to_elasticsearch() for op in self.operands]
                }
            }
        elif self.operator == "OR":
            # At least one operand must match
            return {
                "bool": {
                    "should": [op.to_elasticsearch() for op in self.operands],
                    "minimum_should_match": 1
                }
            }
        elif self.operator == "NOT":
            # Operands must not match
            return {
                "bool": {
                    "must_not": [op.to_elasticsearch() for op in self.operands]
                }
            }
        else:
            raise ValueError(f"Unknown operator: {self.operator}")


class QueryParser:
    """
    Parser for boolean search queries.

    Converts natural language queries with boolean operators into
    Elasticsearch query DSL using recursive descent parsing.

    Grammar:
        expression  := or_expr
        or_expr     := and_expr ('OR' and_expr)*
        and_expr    := not_expr ('AND' not_expr)*
        not_expr    := 'NOT' not_expr | primary
        primary     := '(' expression ')' | term
        term        := QUOTED | FIELD | WORD

    Example:
        >>> parser = QueryParser()
        >>> query_dsl = parser.parse('Python AND (Django OR Flask) NOT Java')
        >>> # Returns Elasticsearch bool query DSL
    """

    def __init__(self):
        """Initialize the query parser."""
        self.tokens: List[Token] = []
        self.position = 0

    def parse(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Parse a query string and convert to Elasticsearch query DSL.

        Args:
            query: The query string to parse

        Returns:
            Elasticsearch query DSL dictionary, or None for empty queries

        Raises:
            ValueError: If the query syntax is invalid
        """
        if not query or not query.strip():
            logger.debug("Empty query provided")
            return None

        try:
            # Tokenize the query
            lexer = QueryLexer(query)
            self.tokens = lexer.tokenize()
            self.position = 0

            # Parse the expression
            ast = self._parse_expression()

            # Check for unexpected tokens
            if not self._is_at_end():
                token = self._current_token()
                raise ValueError(
                    f"Unexpected token '{token.value}' at position {token.position}"
                )

            # Convert AST to Elasticsearch query DSL
            if ast is None:
                return None

            query_dsl = ast.to_elasticsearch()

            logger.debug(f"Parsed query: {query} -> {query_dsl}")

            return {"query": query_dsl}

        except Exception as e:
            logger.error(f"Failed to parse query '{query}': {e}")
            raise ValueError(f"Query parsing failed: {str(e)}") from e

    def _parse_expression(self) -> Optional[ASTNode]:
        """Parse an expression (top level)."""
        return self._parse_or_expr()

    def _parse_or_expr(self) -> Optional[ASTNode]:
        """Parse OR expression."""
        left = self._parse_and_expr()

        if left is None:
            return None

        or_operands = [left]

        while self._match(TokenType.OR):
            right = self._parse_and_expr()
            if right is None:
                raise ValueError("Expected expression after OR operator")
            or_operands.append(right)

        if len(or_operands) == 1:
            return or_operands[0]

        return BoolNode("OR", or_operands)

    def _parse_and_expr(self) -> Optional[ASTNode]:
        """Parse AND expression."""
        left = self._parse_not_expr()

        if left is None:
            return None

        and_operands = [left]

        # Handle explicit AND operators
        while self._match(TokenType.AND):
            right = self._parse_not_expr()
            if right is None:
                raise ValueError("Expected expression after AND operator")
            and_operands.append(right)

        # Handle implicit AND (consecutive terms without operator)
        while (not self._is_at_end() and
               self._current_token().type not in [TokenType.OR, TokenType.RPAREN, TokenType.EOF]):
            # Check if next token is a term or open paren
            if self._current_token().type in [TokenType.WORD, TokenType.QUOTED,
                                               TokenType.FIELD, TokenType.LPAREN, TokenType.NOT]:
                right = self._parse_not_expr()
                if right is None:
                    break
                and_operands.append(right)
            else:
                break

        if len(and_operands) == 1:
            return and_operands[0]

        return BoolNode("AND", and_operands)

    def _parse_not_expr(self) -> Optional[ASTNode]:
        """Parse NOT expression."""
        if self._match(TokenType.NOT):
            operand = self._parse_not_expr()
            if operand is None:
                raise ValueError("Expected expression after NOT operator")
            return BoolNode("NOT", [operand])

        return self._parse_primary()

    def _parse_primary(self) -> Optional[ASTNode]:
        """Parse primary expression (parentheses or term)."""
        # Parenthesized expression
        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            if expr is None:
                raise ValueError("Empty parenthesized expression")
            if not self._match(TokenType.RPAREN):
                raise ValueError("Expected closing parenthesis ')'")
            return expr

        # Quoted term
        if self._check(TokenType.QUOTED):
            token = self._advance()
            return TermNode(token.value, is_quoted=True)

        # Field-specific term
        if self._check(TokenType.FIELD):
            token = self._advance()
            field, term = token.value.split(':', 1)
            return TermNode(term, field=field)

        # Regular word
        if self._check(TokenType.WORD):
            token = self._advance()
            return TermNode(token.value)

        return None

    def _match(self, *types: TokenType) -> bool:
        """Check if current token matches any of the given types and advance."""
        for token_type in types:
            if self._check(token_type):
                self._advance()
                return True
        return False

    def _check(self, token_type: TokenType) -> bool:
        """Check if current token is of given type."""
        if self._is_at_end():
            return False
        return self._current_token().type == token_type

    def _advance(self) -> Token:
        """Consume and return current token."""
        if not self._is_at_end():
            self.position += 1
        return self._previous_token()

    def _is_at_end(self) -> bool:
        """Check if we've reached the end of tokens."""
        return self.position >= len(self.tokens) or self._current_token().type == TokenType.EOF

    def _current_token(self) -> Token:
        """Get current token."""
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return self.tokens[-1]  # Return EOF token

    def _previous_token(self) -> Token:
        """Get previous token."""
        return self.tokens[self.position - 1]


def parse_query(query: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to parse a query string.

    Args:
        query: The query string to parse

    Returns:
        Elasticsearch query DSL dictionary, or None for empty queries

    Raises:
        ValueError: If the query syntax is invalid
    """
    parser = QueryParser()
    return parser.parse(query)
