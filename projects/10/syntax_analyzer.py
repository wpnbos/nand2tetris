import re
from dataclasses import dataclass
from enum import Enum, auto

from lexical_elements import keywords, symbols

STRING_SPACE = "?x?"


class TokenType(Enum):
    keyword = auto()
    symbol = auto()
    identifier = auto()
    stringConstant = auto()
    integerConstant = auto()


@dataclass
class Token:
    text: str
    type_: TokenType


def strip_comments(program: str) -> str:
    program = re.sub(
        pattern=r"/\*\*.*?\*/", string=program, repl="", flags=re.MULTILINE | re.DOTALL
    )
    return "\n".join(
        [
            line.split("//")[0].strip()
            for line in program.splitlines()
            if line.strip() and not line.strip().startswith("//")
        ]
    ).strip()


def tokenize(program: str) -> list[Token]:
    program = strip_comments(program)
    fixed_strings = re.sub(
        pattern=r"(?<=\").+(?=\")",
        string=program,
        repl=lambda match: match.group().replace(" ", STRING_SPACE),
    )
    left_spaced_program = re.sub(
        pattern=rf"(?<! )[{''.join([re.escape(symbol) for symbol in symbols])}]",
        string=fixed_strings,
        repl=lambda match: " " + match.group(),
    )
    spaced_program = re.sub(
        pattern=rf"[{''.join([re.escape(symbol) for symbol in symbols])}](?! )",
        string=left_spaced_program,
        repl=lambda match: match.group() + " ",
    )
    tokenized = [
        token.replace(STRING_SPACE, " ").strip() for token in spaced_program.split()
    ]
    tokens = []
    for token in tokenized:
        if token in keywords:
            type_ = TokenType.keyword
        elif token in symbols:
            type_ = TokenType.symbol
        elif token.startswith('"'):
            type_ = TokenType.stringConstant
        elif token.isnumeric():
            type_ = TokenType.integerConstant
        else:
            type_ = TokenType.identifier
        text = (
            token.replace('"', "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        tokens.append(Token(text=text, type_=type_))
    return tokens


def generate_xml(program: str) -> str:
    return tokenize(program)


if __name__ == "__main__":
    import sys
    from pathlib import Path

    target_file = Path.cwd() / sys.argv[1]
    if not target_file.suffix == ".jack":
        raise ValueError(f"File type {repr(target_file.suffix)} not supported")
    program = target_file.read_text()
    print(tokenize(program))
