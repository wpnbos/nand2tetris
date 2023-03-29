from pathlib import Path

import pytest

import syntax_analyzer

example_programs = ("Square", "ExpressionLessSquare", "ArrayTest")
example_dirs = [Path(__file__).parent.joinpath(dir_) for dir_ in example_programs]


def get_jack_files():
    for program_dir in example_dirs:
        if "Array" in str(program_dir) or "Expression" in str(program_dir):
            continue
        for jack_file in program_dir.glob("*.jack"):
            yield pytest.param(jack_file, id=f"{program_dir.name}/{jack_file.name}")


@pytest.mark.parametrize("jack_file", get_jack_files())
def test_tokenizes_program_correctly(jack_file: Path):
    expected_tokenized = (
        jack_file.parent.joinpath(f"{jack_file.stem}T.xml").read_text().splitlines()
    )
    tokenized = syntax_analyzer.tokenize(jack_file.read_text())
    for i, expected_token in enumerate(expected_tokenized[1:-1]):
        token_type, text = expected_token.split(">", maxsplit=1)
        expected_token_type = token_type.replace("<", "").strip()
        expected_text = text.split(" <", maxsplit=1)[0].lstrip()
        assert tokenized[i].type_.name == expected_token_type
        assert tokenized[i].text == expected_text


@pytest.mark.parametrize("jack_file", get_jack_files())
def test_creates_correct_xml(jack_file: Path):
    expected_xml = (
        jack_file.parent.joinpath(f"{jack_file.stem}.xml").read_text().splitlines()
    )
    generated_xml = syntax_analyzer.generate_xml(jack_file.read_text()).splitlines()
    for i, expected_line in enumerate(expected_xml):
        print(expected_line)
        assert generated_xml[i] == expected_line.strip()
