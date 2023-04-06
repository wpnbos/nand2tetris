from __future__ import annotations

from typing import Optional

from symbol_table import SubroutineTable, SymbolTable
from tokenizer import Token, TokenType, tokenize


def handle_class_token(
    tokens: list[Token],
    xml: Optional[list[str]] = None,
    symbol_table: Optional[SymbolTable] = None,
) -> list[str]:
    if xml is None:
        xml = []
    xml.append("// <class>")
    class_keyword, name_identifier, opening_bracket, *tokens = tokens
    if symbol_table is None:
        symbol_table = SymbolTable(class_name=name_identifier.text)
    for token in (class_keyword, name_identifier, opening_bracket):
        xml.append(format_token(token))
    token = tokens[0]
    while token.text != "}":
        if token.text in ("static", "field"):
            # Class var declaration
            tokens, xml = handle_class_var_dec(tokens, xml, symbol_table)
            token = tokens[0]
        elif token.text in ("constructor", "function", "method"):
            # Subroutine (method) declaration
            tokens, xml = handle_subroutine_dec(
                tokens, xml, symbol_table, is_method=(token.text != "function")
            )
            token = tokens[0]

    closing_bracket_token, *tokens = tokens
    xml.append(format_token(closing_bracket_token))
    xml.append("// </class>")
    print(symbol_table)
    return xml


def handle_class_var_dec(
    tokens: list[Token], xml: list[str], symbol_table: SymbolTable
) -> tuple[list[Token], list[str]]:
    xml.append("// <classVarDec>")
    var_keyword, type_keyword, name_identifier, *tokens = tokens
    for token in (var_keyword, type_keyword, name_identifier):
        xml.append(format_token(token))
    symbol_table.add_symbol(
        name=name_identifier.text,
        type_=type_keyword.text,
        kind=var_keyword.text,
    )
    token = tokens[0]
    while token.text != ";":
        comma_symbol, name_identifier, *tokens = tokens
        for token in (comma_symbol, name_identifier):
            xml.append(format_token(token))
        symbol_table.add_symbol(
            name=name_identifier.text,
            type_=type_keyword.text,
            kind=var_keyword.text,
        )
        token = tokens[0]
    semi_colon_token, *tokens = tokens
    xml.append(format_token(semi_colon_token))
    xml.append("// </classVarDec>")
    return tokens, xml


def handle_subroutine_dec(
    tokens: list[Token],
    xml: list[str],
    symbol_table: SymbolTable,
    is_method: bool = True,
) -> tuple[list[Token], list[str]]:
    xml.append("// <subroutineDec>")
    method_keyword, type_keyword, name_identifier, opening_bracket, *tokens = tokens
    for token in (method_keyword, type_keyword, name_identifier, opening_bracket):
        xml.append(format_token(token))

    subroutine_table = SubroutineTable(
        parent_table=symbol_table,
        subroutine_name=name_identifier.text,
        is_method=is_method,
        is_void=(type_keyword.text == "void"),
        is_constructor=method_keyword.text == "constructor",
    )
    # Handle parameter list
    xml.append("// <parameterList>")
    token = tokens[0]
    while token.text != ")":
        if token.text == ",":
            comma_token, *tokens = tokens
            xml.append(format_token(comma_token))
        else:
            type_keyword, name_identifier, *tokens = tokens
            for token in (type_keyword, name_identifier):
                xml.append(format_token(token))
            subroutine_table.add_symbol(
                name=name_identifier.text,
                type_=type_keyword.text,
                kind="argument",
            )
        token = tokens[0]
    # Closing bracket
    xml.append("// </parameterList>")
    closing_bracket_token, *tokens = tokens
    xml.append(format_token(closing_bracket_token))
    # Handle subroutine body
    tokens, xml, subroutine_table = handle_subroutine_body(
        tokens, xml, subroutine_table
    )
    xml.append("// </subroutineDec>")
    print(subroutine_table)
    return tokens, xml


def handle_subroutine_body(
    tokens: list[Token], xml: list[str], subroutine_table: SubroutineTable
) -> tuple[list[Token], list[str], SubroutineTable]:
    xml.append("// <subroutineBody>")
    opening_bracket, *tokens = tokens
    xml.append(format_token(opening_bracket))
    token = tokens[0]
    if not token.text == "}":
        while token.text == "var":
            # Variable declaration
            tokens, xml, subroutine_table = handle_var_dec(
                tokens, xml, subroutine_table
            )
            token = tokens[0]
    xml.append(
        f"function {subroutine_table.parent.class_name}.{subroutine_table.subroutine_name} {subroutine_table.var_count}"
    )
    if subroutine_table.is_method and not subroutine_table.is_constructor:
        xml.append("push argument 0")
        xml.append("pop pointer 0")
    # Constructor memory allocation
    if subroutine_table.is_constructor:
        xml.append(f"push constant {subroutine_table.field_count}")
        xml.append("call Memory.alloc 1")
        xml.append("pop pointer 0")
    # The rest are statements
    xml.append("// <statements>")
    while token.text != "}":
        tokens, xml = handle_statement(tokens, xml, subroutine_table)
        token = tokens[0]
    closing_bracket_symbol, *tokens = tokens
    xml.append("// </statements>")
    xml.append(format_token(closing_bracket_symbol))
    xml.append("// </subroutineBody>")
    return tokens, xml, subroutine_table


def handle_statement(
    tokens: list[Token], xml: list[str], subroutine_table: SubroutineTable
) -> tuple[list[Token], list[str]]:
    statement_token, *tokens = tokens
    if statement_token.text == "let":
        xml.append("// <letStatement>")
        name_identifier, *tokens = tokens
        for token in (statement_token, name_identifier):
            xml.append(format_token(token))
        if tokens[0].text == "[":
            opening_bracket, *tokens = tokens
            xml.append(format_token(opening_bracket))
            tokens, xml = handle_expression(tokens, xml, subroutine_table)
            closing_bracket, *tokens = tokens
            xml.append(format_token(closing_bracket))
        eq_symbol, *tokens = tokens
        xml.append(
            f"// <{eq_symbol.type_.name}> {eq_symbol.text} </{eq_symbol.type_.name}>"
        )
        # Handle expression
        tokens, xml = handle_expression(tokens, xml, subroutine_table)
        semicolon_token, *tokens = tokens
        xml.append(format_token(semicolon_token))
        xml.append(f"pop {subroutine_table[name_identifier.text]}")
        xml.append("// </letStatement>")
    elif statement_token.text == "if":
        if_label = subroutine_table.parent.label_generator.generate_label()
        else_label = subroutine_table.parent.label_generator.generate_label()
        xml.append("// <ifStatement>")
        opening_bracket_symbol, *tokens = tokens
        for token in (statement_token, opening_bracket_symbol):
            xml.append(format_token(token))
        # Handle expression
        tokens, xml = handle_expression(tokens, xml, subroutine_table)
        closing_bracket_symbol, *tokens = tokens
        xml.append(format_token(closing_bracket_symbol))
        xml.append("not")
        xml.append(f"if-goto {else_label}")
        opening_bracket_symbol, *tokens = tokens
        xml.append(format_token(opening_bracket_symbol))
        # Handle statements
        token = tokens[0]
        xml.append("// <statements>")
        while token.text != "}":
            tokens, xml = handle_statement(tokens, xml, subroutine_table)
            token = tokens[0]
        xml.append("// </statements>")
        closing_bracket_symbol, *tokens = tokens
        xml.append(f"goto {if_label}")
        xml.append(format_token(closing_bracket_symbol))
        if tokens[0].text == "else":
            # Else statement
            else_keyword, opening_bracket, *tokens = tokens
            for token in (else_keyword, opening_bracket):
                xml.append(format_token(token))
            xml.append(f"label {else_label}")
            # Handle statements
            token = tokens[0]
            xml.append("// <statements>")
            while token.text != "}":
                tokens, xml = handle_statement(tokens, xml, subroutine_table)
                token = tokens[0]
            xml.append("// </statements>")
            closing_bracket_symbol, *tokens = tokens
            xml.append(f"label {if_label}")
            xml.append(format_token(closing_bracket_symbol))
        else:
            xml.append(f"label {else_label}")
            xml.append(f"label {if_label}")
        xml.append("// </ifStatement>")
    elif statement_token.text == "while":
        check_label = subroutine_table.parent.label_generator.generate_label()
        complete_label = subroutine_table.parent.label_generator.generate_label()
        xml.append("// <whileStatement>")
        xml.append(f"label {check_label}")
        opening_bracket_symbol, *tokens = tokens
        for token in (statement_token, opening_bracket_symbol):
            xml.append(format_token(token))
        # Handle expression
        tokens, xml = handle_expression(tokens, xml, subroutine_table)
        closing_bracket_symbol, *tokens = tokens
        xml.append(format_token(closing_bracket_symbol))
        xml.append("not")
        xml.append(f"if-goto {complete_label}")
        opening_bracket_symbol, *tokens = tokens
        xml.append(format_token(opening_bracket_symbol))
        # Handle statements
        token = tokens[0]
        xml.append("// <statements>")
        while token.text != "}":
            tokens, xml = handle_statement(tokens, xml, subroutine_table)
            token = tokens[0]
        xml.append("// </statements>")
        closing_bracket_symbol, *tokens = tokens
        xml.append(format_token(closing_bracket_symbol))
        xml.append(f"goto {check_label}")
        xml.append(f"label {complete_label}")
        xml.append("// </whileStatement>")
    elif statement_token.text == "do":
        xml.append("// <doStatement>")
        xml.append(format_token(statement_token))
        # Handle subroutine call
        identifier_token, *tokens = tokens
        dot_symbol, method_identifier = None, None
        if tokens[0].text == ".":
            dot_symbol, method_identifier, *tokens = tokens
            for token in (identifier_token, dot_symbol, method_identifier):
                xml.append(format_token(token))
        else:
            xml.append(format_token(identifier_token))
        # Handle expression list
        opening_bracket_symbol, *tokens = tokens
        xml.append(format_token(opening_bracket_symbol))
        xml.append("// <expressionList>")
        token = tokens[0]
        n_expressions = 0

        if method_identifier is None:
            # Method call on this
            n_expressions += 1
            xml.append(f"push {subroutine_table['this']}")
            subroutine_name = f"{subroutine_table.class_name}.{identifier_token.text}"
        elif identifier_token.text in subroutine_table:
            # Method call on variable
            n_expressions += 1
            xml.append(f"push {subroutine_table[identifier_token.text]}")
            var_type = subroutine_table.get_symbol(identifier_token.text).type_
            subroutine_name = f"{var_type}.{method_identifier.text}"
        else:
            # Function call?
            subroutine_name = f"{identifier_token.text}.{method_identifier.text}"
        while token.text != ")":
            if token.text == ",":
                comma_symbol, *tokens = tokens
                xml.append(format_token(comma_symbol))
            tokens, xml = handle_expression(tokens, xml, subroutine_table)
            n_expressions += 1
            token = tokens[0]
        xml.append("// </expressionList>")

        xml.append(f"call {subroutine_name} {n_expressions}")

        closing_bracket_symbol, *tokens = tokens
        xml.append(format_token(closing_bracket_symbol))
        semicolon_token, *tokens = tokens
        xml.append(format_token(semicolon_token))
        xml.append("// </doStatement>")
    elif statement_token.text == "return":
        xml.append("// <returnStatement>")
        xml.append(format_token(statement_token))
        if not tokens[0].text == ";":
            tokens, xml = handle_expression(tokens, xml, subroutine_table)
        semicolon_token, *tokens = tokens
        if subroutine_table.is_void:
            xml.append("push constant 0")
        xml.append("return")
        xml.append(format_token(semicolon_token))
        xml.append("// </returnStatement>")
    else:
        raise ValueError(f"{statement_token.text} is not a valid statement token")

    return tokens, xml


def handle_subroutine_call(
    tokens: list[Token], xml: list[str], subroutine_table: SubroutineTable
) -> tuple[list[Token], list[str]]:
    identifier_token, *tokens = tokens
    dot_symbol, method_identifier = None, None
    if tokens[0].text == ".":
        dot_symbol, method_identifier, *tokens = tokens
        for token in (identifier_token, dot_symbol, method_identifier):
            xml.append(format_token(token))
    else:
        xml.append(format_token(identifier_token))
    # Handle expression list
    opening_bracket_symbol, *tokens = tokens
    xml.append(format_token(opening_bracket_symbol))
    n_expressions = 0

    if method_identifier is None:
        # Method call on this
        n_expressions += 1
        xml.append(f"push {subroutine_table['this']}")
        subroutine_name = f"{subroutine_table.class_name}.{identifier_token.text}"
    elif identifier_token.text in subroutine_table:
        # Method call on variable
        n_expressions += 1
        xml.append(f"push {subroutine_table[identifier_token.text]}")
        var_type = subroutine_table.get_symbol(identifier_token.text).type_
        subroutine_name = f"{var_type}.{method_identifier.text}"
    else:
        # Function call?
        subroutine_name = f"{identifier_token.text}.{method_identifier.text}"
    xml.append("// <expressionList>")
    token = tokens[0]
    while token.text != ")":
        if token.text == ",":
            comma_symbol, *tokens = tokens
            xml.append(format_token(comma_symbol))
        tokens, xml = handle_expression(tokens, xml, subroutine_table)
        n_expressions += 1
        token = tokens[0]
    xml.append("// </expressionList>")
    closing_bracket_symbol, *tokens = tokens
    xml.append(format_token(closing_bracket_symbol))
    xml.append(f"call {subroutine_name} {n_expressions}")
    return tokens, xml


def handle_term(
    tokens: list[Token], xml: list[str], subroutine_table: SubroutineTable
) -> tuple[list[Token], list[str]]:
    xml.append("// <term>")
    token, *tokens = tokens
    if token.type_ == TokenType.integerConstant:
        # Integer constant
        xml.append(f"// <integerConstant> {token.text} </integerConstant>")
        xml.append(f"push constant {token.text}")
    elif token.type_ == TokenType.stringConstant:
        # String constant
        xml.append(f"// <stringConstant> {token.text} </stringConstant>")
        xml.append("// STRING")
        n_chars = len(token.text)
        xml.append(f"push constant {n_chars}")
        xml.append("call String.new 1")
        for char in token.text:
            xml.append(f"push constant {ord(char)}")
            xml.append("call String.appendChar 2")
    elif token.type_ == TokenType.keyword:
        # Keyword constant
        xml.append(f"// <keyword> {token.text} </keyword>")
        if token.text == "true":
            command = "push constant 1\nneg"
        elif token.text == "false":
            command = "push constant 0"
        elif token.text == "this":
            command = f"push {subroutine_table['this']}"
        xml.append(command)
    elif token.type_ == TokenType.identifier:
        # Must be a var, array element, or subroutine call
        next_token = tokens[0]
        if next_token.text in (".", "("):
            tokens, xml = handle_subroutine_call(
                [token] + tokens, xml, subroutine_table
            )
        elif next_token.text == "[":
            # Array
            # let a[1] = a[2];
            opening_bracket, *tokens = tokens
            for token_ in (token, opening_bracket):
                xml.append(format_token(token_))
            tokens, xml = handle_expression(tokens, xml, subroutine_table)
            closing_bracket, *tokens = tokens
            xml.append(format_token(closing_bracket))
        else:
            # Just a var
            xml.append(format_token(token))
            loc = subroutine_table[token.text]
            xml.append(f"push {loc}")
    elif token.text == "(":
        xml.append(format_token(token))
        tokens, xml = handle_expression(tokens, xml, subroutine_table)
        closing_bracket, *tokens = tokens
        xml.append(format_token(closing_bracket))
    elif token.text in ("-", "~"):  # Unary ops
        xml.append(format_token(token))
        tokens, xml = handle_term(tokens, xml, subroutine_table)
        op = "neg" if token.text == "-" else "not"
        xml.append(op)
    else:
        xml.append(format_token(token))
    token = tokens[0]
    ops = ["+", "-", "*", "/", "&", "|", "// <", ">", "=", "&amp;", "&gt;", "&lt;"]
    xml.append("// </term>")
    if token.text in ops:
        op_token, *tokens = tokens
        xml.append(format_token(op_token))
        tokens, xml = handle_term(tokens, xml, subroutine_table)
        xml.append(operations[op_token.text])
    return tokens, xml


operations = {
    "+": "add",
    "-": "sub",
    "*": "call Math.multiply 2",
    "/": "call Math.divide 2",
    "&": "and",
    "|": "or",
    "// <": "lt",
    ">": "gt",
    "=": "eq",
    "&amp;": "and",
    "&gt;": "gt",
    "&lt;": "lt",
}


def handle_expression(
    tokens: list[Token], xml: list[str], subroutine_table: SubroutineTable
) -> tuple[list[Token], list[str]]:
    xml.append("// <expression>")
    # Handle term
    tokens, xml = handle_term(tokens, xml, subroutine_table)
    xml.append("// </expression>")
    return tokens, xml


def handle_var_dec(
    tokens: list[Token], xml: list[str], subroutine_table: SubroutineTable
) -> tuple[list[Token], list[str], SubroutineTable]:
    xml.append("// <varDec>")
    var_keyword, type_keyword, name_identifier, *tokens = tokens
    for token in (var_keyword, type_keyword, name_identifier):
        xml.append(format_token(token))
    subroutine_table.add_symbol(
        name=name_identifier.text, type_=type_keyword.text, kind=var_keyword.text
    )
    token = tokens[0]
    while token.text != ";":
        comma_symbol, name_identifier, *tokens = tokens
        for token in (comma_symbol, name_identifier):
            xml.append(format_token(token))
        subroutine_table.add_symbol(
            name=name_identifier.text,
            type_=type_keyword.text,
            kind=var_keyword.text,
        )
        token = tokens[0]
    semi_colon_token, *tokens = tokens
    xml.append(format_token(semi_colon_token))
    xml.append("// </varDec>")
    return tokens, xml, subroutine_table


def compile_(program: str) -> str:
    result = handle_class_token(tokenize(program))
    return "\n".join([line for line in result if "// <" not in line])


def format_token(token: Token) -> str:
    return f"// <{token.type_.name}> {token.text} </{token.type_.name}>"


if __name__ == "__main__":
    import sys
    from pathlib import Path

    target_path = Path.cwd() / sys.argv[1]
    if not target_path.suffix == ".jack" and not target_path.is_dir():
        raise ValueError(f"File type {repr(target_path.suffix)} not supported")
    files = list(target_path.glob("*.jack")) if target_path.is_dir() else [target_path]
    for jack_file in files:
        jack_file.with_suffix(".vm").write_text(compile_(jack_file.read_text()))
