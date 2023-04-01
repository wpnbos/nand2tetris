import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

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


def handle_class_token(
    tokens: list[Token], xml: Optional[list[str]] = None
) -> list[str]:
    if xml is None:
        xml = []
    xml.append("<class>")
    class_keyword, name_identifier, opening_bracket, *tokens = tokens
    for token in (class_keyword, name_identifier, opening_bracket):
        xml.append(format_token(token))
    token = tokens[0]
    while token.text != "}":
        if token.text in ("static", "field"):
            # Class var declaration
            tokens, xml = handle_class_var_dec(tokens, xml)
            token = tokens[0]
        elif token.text in ("constructor", "function", "method"):
            # Subroutine (method) declaration
            tokens, xml = handle_subroutine_dec(tokens, xml)
            token = tokens[0]

    closing_bracket_token, *tokens = tokens
    xml.append(format_token(closing_bracket_token))
    xml.append("</class>")
    return xml


def handle_class_var_dec(
    tokens: list[Token], xml: list[str]
) -> tuple[list[Token], list[str]]:
    xml.append("<classVarDec>")
    var_keyword, type_keyword, name_identifier, *tokens = tokens
    for token in (var_keyword, type_keyword, name_identifier):
        xml.append(format_token(token))
    token = tokens[0]
    while token.text != ";":
        comma_symbol, name_identifier, *tokens = tokens
        for token in (comma_symbol, name_identifier):
            xml.append(format_token(token))
        token = tokens[0]
    semi_colon_token, *tokens = tokens
    xml.append(format_token(semi_colon_token))
    xml.append("</classVarDec>")
    return tokens, xml


def handle_subroutine_dec(
    tokens: list[Token], xml: list[str]
) -> tuple[list[Token], list[str]]:
    xml.append("<subroutineDec>")
    method_keyword, type_keyword, name_identifier, opening_bracket, *tokens = tokens
    for token in (method_keyword, type_keyword, name_identifier, opening_bracket):
        xml.append(format_token(token))

    # Handle parameter list
    xml.append("<parameterList>")
    token = tokens[0]
    while token.text != ")":
        if token.text == ",":
            comma_token, *tokens = tokens
            xml.append(format_token(comma_token))
        else:
            type_keyword, name_identifier, *tokens = tokens
            for token in (type_keyword, name_identifier):
                xml.append(format_token(token))
        token = tokens[0]
    # Closing bracket
    xml.append("</parameterList>")
    closing_bracket_token, *tokens = tokens
    xml.append(format_token(closing_bracket_token))
    # Handle subroutine body
    tokens, xml = handle_subroutine_body(tokens, xml)
    xml.append("</subroutineDec>")
    return tokens, xml


def handle_subroutine_body(
    tokens: list[Token], xml: list[str]
) -> tuple[list[Token], list[str]]:
    xml.append("<subroutineBody>")
    opening_bracket, *tokens = tokens
    xml.append(format_token(opening_bracket))
    token = tokens[0]
    if not token.text == "}":
        while token.text == "var":
            # Variable declaration
            tokens, xml = handle_var_dec(tokens, xml)
            token = tokens[0]
    # The rest are statements
    xml.append("<statements>")
    while token.text != "}":
        tokens, xml = handle_statement(tokens, xml)
        token = tokens[0]
    closing_bracket_symbol, *tokens = tokens
    xml.append("</statements>")
    xml.append(format_token(closing_bracket_symbol))
    xml.append("</subroutineBody>")
    return tokens, xml


def handle_statement(
    tokens: list[Token], xml: list[str]
) -> tuple[list[Token], list[str]]:
    statement_token, *tokens = tokens
    if statement_token.text == "let":
        xml.append("<letStatement>")
        name_identifier, *tokens = tokens
        for token in (statement_token, name_identifier):
            xml.append(format_token(token))
        if tokens[0].text == "[":
            opening_bracket, *tokens = tokens
            xml.append(format_token(opening_bracket))
            tokens, xml = handle_expression(tokens, xml)
            closing_bracket, *tokens = tokens
            xml.append(format_token(closing_bracket))
        eq_symbol, *tokens = tokens
        xml.append(
            f"<{eq_symbol.type_.name}> {eq_symbol.text} </{eq_symbol.type_.name}>"
        )
        # Handle expression
        tokens, xml = handle_expression(tokens, xml)
        semicolon_token, *tokens = tokens
        xml.append(format_token(semicolon_token))
        xml.append("</letStatement>")
    elif statement_token.text == "if":
        xml.append("<ifStatement>")
        opening_bracket_symbol, *tokens = tokens
        for token in (statement_token, opening_bracket_symbol):
            xml.append(format_token(token))
        # Handle expression
        tokens, xml = handle_expression(tokens, xml)
        closing_bracket_symbol, *tokens = tokens
        xml.append(format_token(closing_bracket_symbol))
        opening_bracket_symbol, *tokens = tokens
        xml.append(format_token(opening_bracket_symbol))
        # Handle statements
        token = tokens[0]
        xml.append("<statements>")
        while token.text != "}":
            tokens, xml = handle_statement(tokens, xml)
            token = tokens[0]
        xml.append("</statements>")
        closing_bracket_symbol, *tokens = tokens
        xml.append(format_token(closing_bracket_symbol))
        if tokens[0].text == "else":
            # Else statement
            else_keyword, opening_bracket, *tokens = tokens
            for token in (else_keyword, opening_bracket):
                xml.append(format_token(token))
            # Handle statements
            token = tokens[0]
            xml.append("<statements>")
            while token.text != "}":
                tokens, xml = handle_statement(tokens, xml)
                token = tokens[0]
            xml.append("</statements>")
            closing_bracket_symbol, *tokens = tokens
            xml.append(format_token(closing_bracket_symbol))
        xml.append("</ifStatement>")
    elif statement_token.text == "while":
        xml.append("<whileStatement>")
        opening_bracket_symbol, *tokens = tokens
        for token in (statement_token, opening_bracket_symbol):
            xml.append(format_token(token))
        # Handle expression
        tokens, xml = handle_expression(tokens, xml)
        closing_bracket_symbol, *tokens = tokens
        xml.append(format_token(closing_bracket_symbol))
        opening_bracket_symbol, *tokens = tokens
        xml.append(format_token(opening_bracket_symbol))
        # Handle statements
        token = tokens[0]
        xml.append("<statements>")
        while token.text != "}":
            tokens, xml = handle_statement(tokens, xml)
            token = tokens[0]
        xml.append("</statements>")
        closing_bracket_symbol, *tokens = tokens
        xml.append(format_token(closing_bracket_symbol))
        xml.append("</whileStatement>")
    elif statement_token.text == "do":
        xml.append("<doStatement>")
        xml.append(format_token(statement_token))
        # Handle subroutine call
        identifier_token, *tokens = tokens
        if tokens[0].text == ".":
            dot_symbol, method_identifier, *tokens = tokens
            for token in (identifier_token, dot_symbol, method_identifier):
                xml.append(format_token(token))
        else:
            xml.append(format_token(identifier_token))
        # Handle expression list
        opening_bracket_symbol, *tokens = tokens
        xml.append(format_token(opening_bracket_symbol))
        xml.append("<expressionList>")
        token = tokens[0]
        while token.text != ")":
            if token.text == ",":
                comma_symbol, *tokens = tokens
                xml.append(format_token(comma_symbol))
            tokens, xml = handle_expression(tokens, xml)
            token = tokens[0]
        xml.append("</expressionList>")
        closing_bracket_symbol, *tokens = tokens
        xml.append(format_token(closing_bracket_symbol))
        semicolon_token, *tokens = tokens
        xml.append(format_token(semicolon_token))
        xml.append("</doStatement>")
    elif statement_token.text == "return":
        xml.append("<returnStatement>")
        xml.append(format_token(statement_token))
        if not tokens[0].text == ";":
            tokens, xml = handle_expression(tokens, xml)
        semicolon_token, *tokens = tokens
        xml.append(format_token(semicolon_token))
        xml.append("</returnStatement>")
    else:
        raise ValueError(f"{statement_token.text} is not a valid statement token")

    return tokens, xml


def handle_subroutine_call(
    tokens: list[Token], xml: list[str]
) -> tuple[list[Token], list[str]]:
    identifier_token, *tokens = tokens
    if tokens[0].text == ".":
        dot_symbol, method_identifier, *tokens = tokens
        for token in (identifier_token, dot_symbol, method_identifier):
            xml.append(format_token(token))
    else:
        xml.append(format_token(identifier_token))
    # Handle expression list
    opening_bracket_symbol, *tokens = tokens
    xml.append(format_token(opening_bracket_symbol))
    xml.append("<expressionList>")
    token = tokens[0]
    while token.text != ")":
        if token.text == ",":
            comma_symbol, *tokens = tokens
            xml.append(format_token(comma_symbol))
        tokens, xml = handle_expression(tokens, xml)
        token = tokens[0]
    xml.append("</expressionList>")
    closing_bracket_symbol, *tokens = tokens
    xml.append(format_token(closing_bracket_symbol))
    return tokens, xml


def handle_term(tokens: list[Token], xml: list[str]) -> tuple[list[Token], list[str]]:
    xml.append("<term>")
    token, *tokens = tokens
    if token.type_ == TokenType.integerConstant:
        # Integer constant
        xml.append(f"<integerConstant> {token.text} </integerConstant>")
    elif token.type_ == TokenType.stringConstant:
        # String constant
        xml.append(f"<stringConstant> {token.text} </stringConstant>")
    elif token.type_ == TokenType.keyword:
        # Keyword constant
        xml.append(f"<keyword> {token.text} </keyword>")
    elif token.type_ == TokenType.identifier:
        # Must be a var, array element, or subroutine call
        next_token = tokens[0]
        if next_token.text in (".", "("):
            tokens, xml = handle_subroutine_call([token] + tokens, xml)
        elif next_token.text == "[":
            # Array
            # let a[1] = a[2];
            opening_bracket, *tokens = tokens
            for token_ in (token, opening_bracket):
                xml.append(format_token(token_))
            tokens, xml = handle_expression(tokens, xml)
            closing_bracket, *tokens = tokens
            xml.append(format_token(closing_bracket))
        else:
            # Just a var
            xml.append(format_token(token))
    elif token.text == "(":
        xml.append(format_token(token))
        tokens, xml = handle_expression(tokens, xml)
        closing_bracket, *tokens = tokens
        xml.append(format_token(closing_bracket))
    elif token.text in ("-", "~"):  # Unary ops
        xml.append(format_token(token))
        tokens, xml = handle_term(tokens, xml)
    else:
        xml.append(format_token(token))
    token = tokens[0]
    ops = ["+", "-", "*", "/", "&", "|", "<", ">", "=", "&amp;", "&gt;", "&lt;"]
    xml.append("</term>")
    if token.text in ops:
        op_token, *tokens = tokens
        xml.append(format_token(op_token))
        tokens, xml = handle_term(tokens, xml)
    return tokens, xml


def handle_expression(
    tokens: list[Token], xml: list[str]
) -> tuple[list[Token], list[str]]:
    xml.append("<expression>")
    # Handle term
    tokens, xml = handle_term(tokens, xml)
    xml.append("</expression>")
    return tokens, xml


def handle_var_dec(
    tokens: list[Token], xml: list[str]
) -> tuple[list[Token], list[str]]:
    xml.append("<varDec>")
    var_keyword, type_keyword, name_identifier, *tokens = tokens
    for token in (var_keyword, type_keyword, name_identifier):
        xml.append(format_token(token))
    token = tokens[0]
    while token.text != ";":
        comma_symbol, name_identifier, *tokens = tokens
        for token in (comma_symbol, name_identifier):
            xml.append(format_token(token))
        token = tokens[0]
    semi_colon_token, *tokens = tokens
    xml.append(format_token(semi_colon_token))
    xml.append("</varDec>")
    return tokens, xml


def compile_(program: str) -> str:
    result = handle_class_token(tokenize(program))
    return "\n".join(result)


def format_token(token: Token) -> str:
    return f"<{token.type_.name}> {token.text} </{token.type_.name}>"


if __name__ == "__main__":
    import sys
    from pathlib import Path

    target_file = Path.cwd() / sys.argv[1]
    if not target_file.suffix == ".jack":
        raise ValueError(f"File type {repr(target_file.suffix)} not supported")
    target_file.with_suffix(".vm").write_text(compile_(target_file.read_text()))
