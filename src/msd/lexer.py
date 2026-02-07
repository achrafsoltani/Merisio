from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Tuple

from .errors import MSDError


class TokenType(Enum):
    # Keywords
    PROJECT = auto()
    ENTITY = auto()
    ASSOCIATION = auto()
    LINK = auto()

    # Symbols
    LBRACE = auto()
    RBRACE = auto()
    LPAREN = auto()
    RPAREN = auto()
    COLON = auto()
    COMMA = auto()
    STAR = auto()

    # Literals
    IDENTIFIER = auto()
    INTEGER = auto()
    STRING_VALUE = auto()  # Rest-of-line value inside project {}

    # Structural
    NEWLINE = auto()
    EOF = auto()


KEYWORDS = {
    "project": TokenType.PROJECT,
    "entity": TokenType.ENTITY,
    "association": TokenType.ASSOCIATION,
    "link": TokenType.LINK,
}


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int


class MSDLexer:
    """Tokenizes MSD source text."""

    def tokenize(self, source: str, filename: str = "") -> Tuple[List[Token], List[MSDError]]:
        tokens: List[Token] = []
        errors: List[MSDError] = []

        lines = source.split("\n")
        brace_depth = 0
        in_project_block = False

        for line_num, line_text in enumerate(lines, start=1):
            col = 0
            length = len(line_text)

            while col < length:
                ch = line_text[col]

                # Skip whitespace (not newlines)
                if ch in (" ", "\t"):
                    col += 1
                    continue

                # Comments: # or //
                if ch == "#":
                    break  # skip rest of line
                if ch == "/" and col + 1 < length and line_text[col + 1] == "/":
                    break  # skip rest of line

                # Symbols
                if ch == "{":
                    tokens.append(Token(TokenType.LBRACE, "{", line_num, col + 1))
                    brace_depth += 1
                    col += 1
                    continue
                if ch == "}":
                    tokens.append(Token(TokenType.RBRACE, "}", line_num, col + 1))
                    brace_depth -= 1
                    if brace_depth == 0:
                        in_project_block = False
                    col += 1
                    continue
                if ch == "(":
                    tokens.append(Token(TokenType.LPAREN, "(", line_num, col + 1))
                    col += 1
                    continue
                if ch == ")":
                    tokens.append(Token(TokenType.RPAREN, ")", line_num, col + 1))
                    col += 1
                    continue
                if ch == ",":
                    tokens.append(Token(TokenType.COMMA, ",", line_num, col + 1))
                    col += 1
                    continue
                if ch == "*":
                    tokens.append(Token(TokenType.STAR, "*", line_num, col + 1))
                    col += 1
                    continue

                # Colon — context-sensitive in project blocks
                if ch == ":":
                    tokens.append(Token(TokenType.COLON, ":", line_num, col + 1))
                    col += 1

                    if in_project_block:
                        # Capture rest of line as STRING_VALUE (strip leading whitespace)
                        rest = line_text[col:].strip()
                        # Strip trailing comment
                        for comment_start in ("#", "//"):
                            idx = rest.find(comment_start)
                            if idx >= 0:
                                rest = rest[:idx].rstrip()
                        if rest:
                            tokens.append(Token(TokenType.STRING_VALUE, rest, line_num, col + 1))
                        break  # consumed rest of line
                    continue

                # Integer literal
                if ch.isdigit():
                    start = col
                    while col < length and line_text[col].isdigit():
                        col += 1
                    tokens.append(Token(TokenType.INTEGER, line_text[start:col], line_num, start + 1))
                    continue

                # Identifiers and keywords
                if ch.isalpha() or ch == "_":
                    start = col
                    while col < length and (line_text[col].isalnum() or line_text[col] == "_"):
                        col += 1
                    word = line_text[start:col]

                    # Case-insensitive keyword matching
                    keyword_type = KEYWORDS.get(word.lower())
                    if keyword_type:
                        tokens.append(Token(keyword_type, word, line_num, start + 1))
                        if keyword_type == TokenType.PROJECT:
                            in_project_block = True
                    else:
                        tokens.append(Token(TokenType.IDENTIFIER, word, line_num, start + 1))
                    continue

                # Unknown character
                errors.append(MSDError(
                    message=f"unexpected character: '{ch}'",
                    line=line_num,
                    column=col + 1,
                    filename=filename,
                ))
                col += 1

            # Emit newline token after each line (for parser line-awareness)
            tokens.append(Token(TokenType.NEWLINE, "\\n", line_num, length + 1))

        tokens.append(Token(TokenType.EOF, "", len(lines), 0))
        return tokens, errors
