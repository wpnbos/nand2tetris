import pytest
from pathlib import Path
import subprocess

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
    program = hack_file.stem
    assembly_file = (
        Path(__file__)
        .parent.joinpath(program.replace("L", "").lower())
        .joinpath(f"{program}.asm")
    )
    assert assemble(assembly_file.read_text()) == expected_code


@pytest.mark.parametrize(
    "hack_file",
    hack_files,
    ids=[file_.stem for file_ in hack_files],
)
def test_assembler_outputs_code_to_file_in_current_dir(hack_file: Path, tmp_path):
    program = hack_file.stem
    assembly_file = (
        Path(__file__)
        .parent.joinpath(program.replace("L", "").lower())
        .joinpath(f"{program}.asm")
    )
    tmp_script = tmp_path.joinpath(assembly_file.name)
    tmp_script.write_text(assembly_file.read_text())
    assembler_script = Path(__file__).parent.joinpath("assembler.py")
    subprocess.run(["python3.10", str(assembler_script), str(tmp_script)])

    expected_file_name = f"{program}.hack"
    assert [path.name for path in tmp_path.glob("*.hack")] == [expected_file_name]
    assert tmp_path.joinpath(expected_file_name).read_text() == hack_file.read_text()
