"""Tests for MSD lexer."""

import pytest
from src.msd.lexer import MSDLexer, TokenType


@pytest.fixture
def lexer():
    return MSDLexer()


def _types(tokens):
    """Extract non-NEWLINE, non-EOF token types."""
    return [t.type for t in tokens if t.type not in (TokenType.NEWLINE, TokenType.EOF)]


def _values(tokens):
    """Extract non-NEWLINE, non-EOF token values."""
    return [t.value for t in tokens if t.type not in (TokenType.NEWLINE, TokenType.EOF)]


class TestEmptyInput:
    def test_empty_string(self, lexer):
        tokens, errors = lexer.tokenize("")
        assert len(errors) == 0
        meaningful = _types(tokens)
        assert meaningful == []

    def test_whitespace_only(self, lexer):
        tokens, errors = lexer.tokenize("   \t  ")
        assert len(errors) == 0
        meaningful = _types(tokens)
        assert meaningful == []


class TestComments:
    def test_hash_comment(self, lexer):
        tokens, errors = lexer.tokenize("# this is a comment")
        assert len(errors) == 0
        assert _types(tokens) == []

    def test_double_slash_comment(self, lexer):
        tokens, errors = lexer.tokenize("// this is a comment")
        assert len(errors) == 0
        assert _types(tokens) == []

    def test_comment_after_code(self, lexer):
        tokens, errors = lexer.tokenize("entity Foo { # comment")
        types = _types(tokens)
        assert TokenType.ENTITY in types
        assert TokenType.IDENTIFIER in types
        assert TokenType.LBRACE in types


class TestKeywords:
    def test_all_keywords(self, lexer):
        tokens, errors = lexer.tokenize("project entity association link")
        types = _types(tokens)
        assert types == [TokenType.PROJECT, TokenType.ENTITY, TokenType.ASSOCIATION, TokenType.LINK]

    def test_case_insensitive_keywords(self, lexer):
        tokens, errors = lexer.tokenize("ENTITY Entity eNtItY")
        types = _types(tokens)
        assert types == [TokenType.ENTITY, TokenType.ENTITY, TokenType.ENTITY]


class TestSymbols:
    def test_all_symbols(self, lexer):
        tokens, errors = lexer.tokenize("{ } ( ) : , *")
        types = _types(tokens)
        assert types == [
            TokenType.LBRACE, TokenType.RBRACE,
            TokenType.LPAREN, TokenType.RPAREN,
            TokenType.COLON, TokenType.COMMA, TokenType.STAR,
        ]


class TestIdentifiersAndIntegers:
    def test_identifiers(self, lexer):
        tokens, errors = lexer.tokenize("foo bar_baz Qux123")
        values = _values(tokens)
        assert values == ["foo", "bar_baz", "Qux123"]

    def test_integers(self, lexer):
        tokens, errors = lexer.tokenize("42 255 0")
        types = _types(tokens)
        assert types == [TokenType.INTEGER, TokenType.INTEGER, TokenType.INTEGER]
        values = _values(tokens)
        assert values == ["42", "255", "0"]


class TestProjectBlock:
    def test_project_string_values(self, lexer):
        source = """project {
    name: Tourism Management System
    author: Achraf SOLTANI
}"""
        tokens, errors = lexer.tokenize(source)
        assert len(errors) == 0

        # Find STRING_VALUE tokens
        string_vals = [t.value for t in tokens if t.type == TokenType.STRING_VALUE]
        assert "Tourism Management System" in string_vals
        assert "Achraf SOLTANI" in string_vals

    def test_project_string_value_with_comment(self, lexer):
        source = "project {\n    name: My Project # a comment\n}"
        tokens, errors = lexer.tokenize(source)
        string_vals = [t.value for t in tokens if t.type == TokenType.STRING_VALUE]
        assert string_vals == ["My Project"]


class TestLineColumnTracking:
    def test_line_numbers(self, lexer):
        source = "entity Foo {\n    *id: INT\n}"
        tokens, errors = lexer.tokenize(source)
        entity_tok = [t for t in tokens if t.type == TokenType.ENTITY][0]
        assert entity_tok.line == 1
        star_tok = [t for t in tokens if t.type == TokenType.STAR][0]
        assert star_tok.line == 2
        rbrace_tok = [t for t in tokens if t.type == TokenType.RBRACE][0]
        assert rbrace_tok.line == 3

    def test_column_numbers(self, lexer):
        tokens, errors = lexer.tokenize("entity Foo")
        entity_tok = [t for t in tokens if t.type == TokenType.ENTITY][0]
        assert entity_tok.column == 1
        foo_tok = [t for t in tokens if t.type == TokenType.IDENTIFIER][0]
        assert foo_tok.column == 8


class TestInvalidCharacters:
    def test_unexpected_char(self, lexer):
        tokens, errors = lexer.tokenize("entity Foo @")
        assert len(errors) == 1
        assert "unexpected character" in errors[0].message
        assert "@" in errors[0].message

    def test_multiple_invalid_chars(self, lexer):
        tokens, errors = lexer.tokenize("$ % ^")
        assert len(errors) == 3


class TestFullEntityBlock:
    def test_entity_tokenization(self, lexer):
        source = """entity Tourist {
    *id: INT
    name: VARCHAR(255)
    email: VARCHAR(255)
}"""
        tokens, errors = lexer.tokenize(source)
        assert len(errors) == 0
        types = _types(tokens)
        assert TokenType.ENTITY in types
        assert TokenType.STAR in types
        assert types.count(TokenType.COLON) == 3


class TestLinkStatement:
    def test_link_tokenization(self, lexer):
        tokens, errors = lexer.tokenize("link Tourist (1,1) user_role")
        assert len(errors) == 0
        types = _types(tokens)
        assert types == [
            TokenType.LINK, TokenType.IDENTIFIER,
            TokenType.LPAREN, TokenType.INTEGER, TokenType.COMMA, TokenType.INTEGER, TokenType.RPAREN,
            TokenType.IDENTIFIER,
        ]
