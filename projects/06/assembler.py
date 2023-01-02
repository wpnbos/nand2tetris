def parse_assembly(assembly_code: str) -> list[str]:
    return [
        stripped_line
        for line in assembly_code.splitlines()
        if (stripped_line := line.strip())
    ]


def assemble_instruction(instruction: str) -> str:
    return ""


def assemble(assembly_code: str) -> str:
    return
