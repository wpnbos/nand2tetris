import pytest
from pathlib import Path

from assembler import assemble, parse_assembly


hack_files_dir = Path(__file__).parent.joinpath("test").glob("*.hack")
hack_files = list(hack_files_dir)


def test_parse_assembly_returns_list_of_instruction_strings():
    assembly_code = "@2\nD=A\n@3\nD=D+A\n"
    assert parse_assembly(assembly_code) == ["@2", "D=A", "@3", "D=D+A"]


def test_parse_assembly_strips_preceding_and_trailing_whitespace_from_instructions():
    assembly_code = "\t@2\n\tD=A\n@3  \n\rD=D+A\n"
    assert parse_assembly(assembly_code) == ["@2", "D=A", "@3", "D=D+A"]


@pytest.mark.parametrize(
    "hack_file",
    hack_files,
    ids=[file_.stem for file_ in hack_files],
)
def test_assembles_hack_file_correctly(hack_file: Path):
    expected_code = hack_file.read_text()
    assembly_file = (
        Path(__file__)
        .parent.joinpath(hack_file.stem.replace("L.", "").lower())
        .joinpath(hack_file)
    )
    assert assemble(assembly_file.read_text()) == expected_code
