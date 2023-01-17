from pathlib import Path

import pytest

import vm_translator

asm_files_dir = Path(__file__).parent.joinpath("test")
asm_files = list(asm_files_dir.glob("*.asm"))
vm_files = Path(__file__).parent.parent.rglob("*.vm")


@pytest.mark.parametrize(
    "asm_file",
    asm_files,
    ids=[file_.stem for file_ in asm_files],
)
def test_translates_vm_to_assembly_correctly(asm_file: Path):
    expected_code = asm_file.read_text()
    [vm_file] = [file_ for file_ in vm_files if file_.stem == asm_file.stem]
    assert vm_translator.translate(vm_file.read_text()) == expected_code


@pytest.mark.parametrize("value", [7, 8])
def test_generate_push(value: int):
    expected_code = "\n".join(
        [
            f"// push constant {value}",
            f"@{value}",
            "D=A",
            "@SP",
            "A=M",
            "M=D",
            "@SP",
            "M=M+1",
        ]
    )
    assert vm_translator.generate_push(value) == expected_code


def test_generate_add():
    expected_code = "\n".join(
        [
            "// add",
            "@SP",
            "M=M-1",
            "A=M",
            "D=M",
            "@SP",
            "M=M-1",
            "A=M",
            "M=M+D",
            "@SP",
            "M=M+1",
        ]
    )
    assert vm_translator.generate_add() == expected_code


def test_generate_end():
    expected_code = "\n".join(
        [
            "// end",
            "(END)",
            "@END",
            "0;JEQ",
        ]
    )
    assert vm_translator.generate_end() == expected_code


def test_generate_and():
    expected_code = "\n".join(
        [
            "// eq",
            "@SP",
            "M=M-1",
            "A=M",
            "D=M",
            "@SP",
            "M=M-1",
            "A=M",
            "M=M&D",
            "@SP",
            "M=M+1",
        ]
    )
    assert vm_translator.generate_and() == expected_code


def test_generate_eq():
    expected_code = "\n".join(
        [
            "// eq",
            "@SP",
            "M=M-1",
            "A=M",
            "D=M",
            "@SP",
            "M=M-1",
            "A=M",
            "D=M-D",
            "@EQUAL1",
            "D;JEQ",
            "@SP",
            "A=M",
            "M=0",
            "@CONT1",
            "0;JEQ",
            "(EQUAL1)",
            "@SP",
            "A=M",
            "M=1",
            "(CONT1)",
        ]
    )
    assert vm_translator.generate_eq(1) == expected_code


def test_generate_lt():
    expected_code = "\n".join(
        [
            "// lt",
            "@SP",
            "M=M-1",
            "A=M",
            "D=M",
            "@SP",
            "M=M-1",
            "A=M",
            "D=D-M",
            "@LT1",
            "D;JLT",
            "@SP",
            "A=M",
            "M=0",
            "@CONT1",
            "0;JEQ",
            "(LT1)",
            "M=1",
            "(CONT1)",
        ]
    )
    assert vm_translator.generate_lt(1) == expected_code


def test_generate_gt():
    expected_code = "\n".join(
        [
            "// gt",
            "@SP",
            "M=M-1",
            "A=M",
            "D=M",
            "@SP",
            "M=M-1",
            "A=M",
            "D=M-D",
            "@GT1",
            "D;JGT",
            "@SP",
            "A=M",
            "M=0",
            "@CONT1",
            "0;JEQ",
            "(GT1)",
            "M=1",
            "(CONT1)",
        ]
    )
    assert vm_translator.generate_gt(1) == expected_code


def test_generate_or():
    expected_code = "\n".join(
        [
            "// or",
            "@SP",
            "M=M-1",
            "A=M",
            "D=M",
            "@SP",
            "M=M-1",
            "A=M",
            "M=M|D",
            "@SP",
            "M=M+1",
        ]
    )
    assert vm_translator.generate_or() == expected_code


def test_generate_sub():
    expected_code = "\n".join(
        [
            "// sub",
            "@SP",
            "M=M-1",
            "A=M",
            "D=M",
            "@SP",
            "M=M-1",
            "A=M",
            "M=M-D",
            "@SP",
            "M=M+1",
        ]
    )
    assert vm_translator.generate_sub() == expected_code


def test_generate_neg():
    expected_code = "\n".join(
        [
            "// neg",
            "@SP",
            "M=M-1",
            "A=M",
            "M=-M",
            "@SP",
            "M=M+1",
        ]
    )
    assert vm_translator.generate_neg() == expected_code


def test_generate_not():
    expected_code = "\n".join(
        [
            "// not",
            "@SP",
            "M=M-1",
            "A=M",
            "M=!M",
            "@SP",
            "M=M+1",
        ]
    )
    assert vm_translator.generate_not() == expected_code
