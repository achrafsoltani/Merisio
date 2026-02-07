from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .errors import MSDError
from .lexer import MSDLexer, Token, TokenType

# Valid data types (uppercase canonical forms)
DATA_TYPES = {
    "INT", "BIGINT", "SMALLINT",
    "VARCHAR", "CHAR", "TEXT",
    "BOOLEAN",
    "DATE", "TIME", "TIMESTAMP",
    "DECIMAL", "FLOAT", "DOUBLE",
}

# Types that accept a size parameter
SIZED_TYPES = {"VARCHAR", "CHAR", "DECIMAL"}


@dataclass
class ParsedAttribute:
    name: str
    data_type: str
    size: Optional[int] = None
    is_primary_key: bool = False
    line: int = 0
    column: int = 0


@dataclass
class ParsedEntity:
    name: str
    attributes: List[ParsedAttribute] = field(default_factory=list)
    line: int = 0
    column: int = 0


@dataclass
class ParsedAssociation:
    name: str
    attributes: List[ParsedAttribute] = field(default_factory=list)
    line: int = 0
    column: int = 0


@dataclass
class ParsedLink:
    entity_name: str
    cardinality_min: str = "0"
    cardinality_max: str = "N"
    association_name: str = ""
    line: int = 0
    column: int = 0


@dataclass
class ParsedMetadata:
    name: str = ""
    author: str = ""
    description: str = ""


@dataclass
class ParseResult:
    entities: List[ParsedEntity] = field(default_factory=list)
    associations: List[ParsedAssociation] = field(default_factory=list)
    links: List[ParsedLink] = field(default_factory=list)
    metadata: Optional[ParsedMetadata] = None
    errors: List[MSDError] = field(default_factory=list)
    filename: str = ""

    @property
    def has_errors(self) -> bool:
        return any(e.severity == "error" for e in self.errors)


class MSDParser:
    """Recursive descent parser for MSD files."""

    def parse(self, source: str, filename: str = "") -> ParseResult:
        lexer = MSDLexer()
        tokens, lex_errors = lexer.tokenize(source, filename)

        self._tokens = tokens
        self._pos = 0
        self._filename = filename
        self._result = ParseResult(filename=filename)
        self._result.errors.extend(lex_errors)

        self._skip_newlines()

        while not self._at_end():
            try:
                self._parse_top_level()
            except _ParsePanic:
                self._recover_to_top_level()

        return self._result

    def _parse_top_level(self):
        """Parse a top-level declaration."""
        self._skip_newlines()
        if self._at_end():
            return

        tok = self._peek()

        if tok.type == TokenType.PROJECT:
            self._parse_project_block()
        elif tok.type == TokenType.ENTITY:
            self._parse_entity_block()
        elif tok.type == TokenType.ASSOCIATION:
            self._parse_association_block()
        elif tok.type == TokenType.LINK:
            self._parse_link_statement()
        else:
            self._error(f"expected 'entity', 'association', 'link', or 'project', got '{tok.value}'", tok)
            raise _ParsePanic()

    def _parse_project_block(self):
        """Parse: project { key: value ... }"""
        self._expect(TokenType.PROJECT)
        self._skip_newlines()
        self._expect(TokenType.LBRACE)
        self._skip_newlines()

        metadata = ParsedMetadata()

        while not self._check(TokenType.RBRACE) and not self._at_end():
            self._skip_newlines()
            if self._check(TokenType.RBRACE):
                break

            key_tok = self._expect(TokenType.IDENTIFIER)
            self._expect(TokenType.COLON)

            # Value is captured as STRING_VALUE by the lexer
            if self._check(TokenType.STRING_VALUE):
                val_tok = self._advance()
                value = val_tok.value
            else:
                value = ""

            key = key_tok.value.lower()
            if key == "name":
                metadata.name = value
            elif key == "author":
                metadata.author = value
            elif key == "description":
                metadata.description = value
            else:
                self._error(f"unknown project property: '{key_tok.value}'", key_tok, severity="warning")

            self._skip_newlines()

        self._expect(TokenType.RBRACE)
        self._result.metadata = metadata

    def _parse_entity_block(self):
        """Parse: entity Name { attributes... }"""
        kw_tok = self._expect(TokenType.ENTITY)
        name_tok = self._expect(TokenType.IDENTIFIER)
        self._skip_newlines()
        self._expect(TokenType.LBRACE)
        self._skip_newlines()

        entity = ParsedEntity(name=name_tok.value, line=name_tok.line, column=name_tok.column)

        while not self._check(TokenType.RBRACE) and not self._at_end():
            self._skip_newlines()
            if self._check(TokenType.RBRACE):
                break
            try:
                attr = self._parse_attribute()
                entity.attributes.append(attr)
            except _ParsePanic:
                self._recover_to_brace_or_keyword()
                if self._check(TokenType.RBRACE):
                    break

            self._skip_newlines()

        self._expect(TokenType.RBRACE)
        self._result.entities.append(entity)

    def _parse_association_block(self):
        """Parse: association Name { attributes... }"""
        kw_tok = self._expect(TokenType.ASSOCIATION)
        name_tok = self._expect(TokenType.IDENTIFIER)
        self._skip_newlines()
        self._expect(TokenType.LBRACE)
        self._skip_newlines()

        assoc = ParsedAssociation(name=name_tok.value, line=name_tok.line, column=name_tok.column)

        while not self._check(TokenType.RBRACE) and not self._at_end():
            self._skip_newlines()
            if self._check(TokenType.RBRACE):
                break
            try:
                attr = self._parse_attribute()
                assoc.attributes.append(attr)
            except _ParsePanic:
                self._recover_to_brace_or_keyword()
                if self._check(TokenType.RBRACE):
                    break

            self._skip_newlines()

        self._expect(TokenType.RBRACE)
        self._result.associations.append(assoc)

    def _parse_attribute(self) -> ParsedAttribute:
        """Parse: [*]name: TYPE[(size)]"""
        is_pk = False
        if self._check(TokenType.STAR):
            self._advance()
            is_pk = True

        name_tok = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.COLON)

        data_type, size = self._parse_type_expr()

        return ParsedAttribute(
            name=name_tok.value,
            data_type=data_type,
            size=size,
            is_primary_key=is_pk,
            line=name_tok.line,
            column=name_tok.column,
        )

    def _parse_type_expr(self) -> Tuple[str, Optional[int]]:
        """Parse: TYPE or TYPE(size)"""
        type_tok = self._expect(TokenType.IDENTIFIER)
        type_name = type_tok.value.upper()

        if type_name not in DATA_TYPES:
            self._error(
                f"unknown data type: '{type_tok.value}' "
                f"(valid types: {', '.join(sorted(DATA_TYPES))})",
                type_tok,
            )
            raise _ParsePanic()

        size = None
        if self._check(TokenType.LPAREN):
            self._advance()
            size_tok = self._expect(TokenType.INTEGER)
            size = int(size_tok.value)
            self._expect(TokenType.RPAREN)

            if type_name not in SIZED_TYPES:
                self._error(
                    f"data type '{type_name}' does not accept a size parameter",
                    type_tok,
                    severity="warning",
                )

        return type_name, size

    def _parse_link_statement(self):
        """Parse: link EntityName (min,max) AssociationName"""
        kw_tok = self._expect(TokenType.LINK)
        entity_tok = self._expect(TokenType.IDENTIFIER)

        card_min, card_max = self._parse_cardinality()

        assoc_tok = self._expect(TokenType.IDENTIFIER)

        link = ParsedLink(
            entity_name=entity_tok.value,
            cardinality_min=card_min,
            cardinality_max=card_max,
            association_name=assoc_tok.value,
            line=kw_tok.line,
            column=kw_tok.column,
        )
        self._result.links.append(link)

    def _parse_cardinality(self) -> Tuple[str, str]:
        """Parse: (min,max) where min in {0,1} and max in {1,N}"""
        self._expect(TokenType.LPAREN)
        min_tok = self._expect(TokenType.INTEGER, TokenType.IDENTIFIER)
        min_val = min_tok.value

        if min_val not in ("0", "1"):
            self._error(
                f"invalid minimum cardinality: '{min_val}' (expected 0 or 1)",
                min_tok,
            )
            raise _ParsePanic()

        self._expect(TokenType.COMMA)
        max_tok = self._expect(TokenType.INTEGER, TokenType.IDENTIFIER)
        max_val = max_tok.value.upper()

        if max_val not in ("1", "N"):
            self._error(
                f"invalid maximum cardinality: '{max_tok.value}' (expected 1 or N)",
                max_tok,
            )
            raise _ParsePanic()

        self._expect(TokenType.RPAREN)
        return min_val, max_val

    # ── Token helpers ──

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _check(self, *types: TokenType) -> bool:
        return self._peek().type in types

    def _at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _skip_newlines(self):
        while not self._at_end() and self._peek().type == TokenType.NEWLINE:
            self._pos += 1

    def _expect(self, *types: TokenType) -> Token:
        self._skip_newlines()
        tok = self._peek()
        if tok.type in types:
            return self._advance()

        expected = " or ".join(t.name for t in types)
        self._error(f"expected {expected}, got {tok.type.name} ('{tok.value}')", tok)
        raise _ParsePanic()

    # ── Error handling ──

    def _error(self, message: str, token: Token, severity: str = "error"):
        self._result.errors.append(MSDError(
            message=message,
            line=token.line,
            column=token.column,
            filename=self._filename,
            severity=severity,
        ))

    def _recover_to_top_level(self):
        """Panic-mode recovery: skip to next top-level keyword or closing brace."""
        while not self._at_end():
            tok = self._peek()
            if tok.type in (TokenType.ENTITY, TokenType.ASSOCIATION, TokenType.LINK, TokenType.PROJECT):
                return
            if tok.type == TokenType.RBRACE:
                self._advance()
                return
            self._advance()

    def _recover_to_brace_or_keyword(self):
        """Skip to next closing brace or top-level keyword."""
        while not self._at_end():
            tok = self._peek()
            if tok.type == TokenType.RBRACE:
                return
            if tok.type in (TokenType.ENTITY, TokenType.ASSOCIATION, TokenType.LINK, TokenType.PROJECT):
                return
            if tok.type == TokenType.STAR:
                return
            # Stop at identifier followed by colon (next attribute)
            if tok.type == TokenType.IDENTIFIER and self._pos + 1 < len(self._tokens):
                next_tok = self._tokens[self._pos + 1]
                if next_tok.type == TokenType.COLON:
                    return
            self._advance()


class _ParsePanic(Exception):
    """Internal exception for panic-mode error recovery."""
    pass
