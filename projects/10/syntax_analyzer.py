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


@dataclass
class Statement:
    statement_token: Token


@dataclass
class IfStatement(Statement):
    pass


@dataclass
class letStatement(Statement):
    pass


@dataclass
class whileStatement(Statement):
    pass


@dataclass
class doStatement(Statement):
    pass


@dataclass
class returnStatement(Statement):
    pass


@dataclass
class VariableDeclaration:
    init_token: Token
    type_token: Token
    name_tokens: list[Token]
    closing_token: Token


@dataclass
class SubroutineBody:
    variable_declarations: list[VariableDeclaration]
    statements: list[Statement]


@dataclass
class ClassVarDeclaration:
    init_token: Token
    type_token: Token
    name_tokens: list[Token]
    closing_token: Token


@dataclass
class SubroutineDeclaration:
    init_token: Token
    type_token: Token
    name_token: Token
    parameter_list: list[Token]
    body: SubroutineBody


@dataclass
class Class_:
    init_token: Token
    name_token: Token
    opening_token: Token
    class_var_declarations: list[ClassVarDeclaration]
    subroutine_declarations: list[SubroutineDeclaration]
    closing_token: Token


def handle_class_var_declaration(tokens: list[Token]) -> ClassVarDeclaration:
    remaining_tokens = tokens[2:]
    name_tokens = []
    closing_token = None
    for token in remaining_tokens:
        if token.text == ";":
            closing_token = token
            break
        name_tokens.append(token)
    return ClassVarDeclaration(
        init_token=tokens[0],
        type_token=tokens[1],
        name_tokens=name_tokens,
        closing_token=closing_token,
    )


def handle_variable_declaration(tokens: list[Token]) -> VariableDeclaration:
    remaining_tokens = tokens[2:]
    name_tokens = []
    closing_token = None
    for token in remaining_tokens:
        if token.text == ";":
            closing_token = token
            break
        name_tokens.append(token)
    return VariableDeclaration(
        init_token=tokens[0],
        type_token=tokens[1],
        name_tokens=name_tokens,
        closing_token=closing_token,
    )


def handle_statement(tokens: list[Token]) -> Statement:
    pass


def handle_subroutine_body(tokens: list[Token]) -> SubroutineBody:
    variable_declarations = []
    statements = []
    for i, token in enumerate(tokens):
        if token.text == "var":
            variable_declarations.append(handle_variable_declaration(tokens[i:]))
        elif token.text in ("let", "if", "while", "do", "return"):
            # TODO: handle_* functions should also return remaining tokens
            pass
        statements.append(handle_statement(tokens[i:]))
    return SubroutineBody(
        variable_declarations=variable_declarations,
        statements=statements,
    )


def handle_subroutine_declaration(tokens: list[Token]) -> SubroutineDeclaration:
    remaining_tokens = tokens[3:]
    parameters: list[Token] = []
    parameter_opening_token = None
    parameter_closing_token = None
    for i, token in enumerate(remaining_tokens):
        if token.text == "(":
            parameter_opening_token = token
        elif token.text == ")":
            parameter_closing_token = token
            remaining_tokens = remaining_tokens[i:]
            break
        parameters.append(token)
    body = handle_subroutine_body(remaining_tokens)
    return SubroutineDeclaration(
        init_token=tokens[0],
        type_token=tokens[1],
        name_token=tokens[2],
        parameter_list=parameters,
        body=body,
    )


def handle_class_token(tokens: list[Token]) -> Class_:
    class_var_declarations = []
    subroutine_declarations = []
    remaining_tokens = tokens[3:]
    closing_token = None
    for i, token in enumerate(remaining_tokens):
        if token.text in ("static", "field"):
            # Class variable declaration
            class_var_declarations.append(
                handle_class_var_declaration(remaining_tokens[i:])
            )
        elif token.text in ("constructor", "function", "method"):
            # Subroutine declaration
            subroutine_declarations.append(
                hande_subroutine_declaration(remaining_tokens[i:])
            )
        elif token.text == "}":
            closing_token = token
            break
    return Class_(
        init_token=tokens[0],
        name_token=tokens[1],
        opening_token=tokens[2],
        class_var_declarations=class_var_declarations,
        subroutine_declarations=subroutine_declarations,
        closing_token=closing_token,
    )


def generate_xml(program: str) -> str:
    result = process_tokens(tokenize(program))
    return result


if __name__ == "__main__":
    import sys
    from pathlib import Path

    target_file = Path.cwd() / sys.argv[1]
    if not target_file.suffix == ".jack":
        raise ValueError(f"File type {repr(target_file.suffix)} not supported")
    program = target_file.read_text()
    print(tokenize(program))
