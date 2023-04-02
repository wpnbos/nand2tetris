from pathlib import Path

import compiler
from compiler import Symbol, SymbolTable


def test_creates_correct_symbol_table_for_class():
    tokens = compiler.tokenize(
        Path(__file__).parent.joinpath("Pong", "PongGame.jack").read_text()
    )
    expected_table = {
        "instance": Symbol(
            name="instance",
            type_="PongGame",
            kind="static",
            index=0,
        ),
        "bat": Symbol(
            name="bat",
            type_="Bat",
            kind="field",
            index=0,
        ),
        "ball": Symbol(
            name="ball",
            type_="Ball",
            kind="field",
            index=1,
        ),
        "wall": Symbol(
            name="wall",
            type_="int",
            kind="field",
            index=2,
        ),
        "exit": Symbol(
            name="exit",
            type_="boolean",
            kind="field",
            index=3,
        ),
        "score": Symbol(
            name="score",
            type_="int",
            kind="field",
            index=4,
        ),
        "lastWall": Symbol(
            name="lastWall",
            type_="int",
            kind="field",
            index=5,
        ),
        "batWidth": Symbol(
            name="batWidth",
            type_="int",
            kind="field",
            index=6,
        ),
    }
    assert compiler.generate_symbol_table("PongGame", tokens).table == expected_table


def test_creates_correct_symbol_table_for_subroutine():
    subroutine = """
    constructor Square new(int Ax, int Ay, int Asize) {
        var char key;
        var boolean juice;
        let x = Ax;
        let y = Ay;
        let size = Asize;
        do draw();
        return this;
   }
"""
    expected_table = {
        "this": Symbol(
            name="this",
            type_="Square",
            kind="arg",
            index=0,
        ),
        "Ax": Symbol(
            name="Ax",
            type_="int",
            kind="arg",
            index=1,
        ),
        "Ay": Symbol(
            name="Ay",
            type_="int",
            kind="arg",
            index=2,
        ),
        "Asize": Symbol(
            name="Asize",
            type_="int",
            kind="arg",
            index=3,
        ),
        "key": Symbol(
            name="key",
            type_="char",
            kind="local",
            index=0,
        ),
        "juice": Symbol(
            name="juice",
            type_="boolean",
            kind="local",
            index=1,
        ),
    }
    tokens = compiler.tokenize(subroutine)
    parent_table = SymbolTable(
        class_name="Square",
        table={
            "x": Symbol(
                name="x",
                type_="int",
                kind="field",
                index=0,
            ),
            "y": Symbol(
                name="y",
                type_="int",
                kind="field",
                index=1,
            ),
            "size": Symbol(
                name="size",
                type_="int",
                kind="field",
                index=2,
            ),
        },
    )
    assert (
        compiler.generate_subroutine_symbol_table(tokens[3:], parent_table).table
        == expected_table
    )
