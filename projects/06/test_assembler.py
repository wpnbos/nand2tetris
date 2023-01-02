import pytest
from pathlib import Path

from assembler import assemble


hack_files_dir = Path(__file__).parent.joinpath("test").glob("*.hack")
hack_files = list(hack_files_dir)


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
