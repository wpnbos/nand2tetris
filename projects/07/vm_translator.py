INSTRUCTIONS = {"SP++": "@SP\nM=M+1", "SP--": "@SP\nM=M-1"}


def clean_lines(lines: list[str]) -> list[str]:
    """
    Removes comments and empty lines.
    """
    return [
        cleaned_line.strip() for line in lines if (cleaned_line := line.split("//")[0])
    ]


def generate_push(value: int) -> str:
    return "\n".join(
        [
            f"// push constant {value}",
            f"@{value}",
            "D=A",
            "@SP",
            "A=M",
            "M=D",
            INSTRUCTIONS["SP++"],
        ]
    )


def generate_add() -> str:
    return "\n".join(
        [
            "// add",
            INSTRUCTIONS["SP--"],
            "A=M",
            "D=M",
            INSTRUCTIONS["SP--"],
            "A=M",
            "M=M+D",
            INSTRUCTIONS["SP++"],
        ]
    )


def generate_end() -> str:
    return "\n".join(
        [
            "// end",
            "(END)",
            "@END",
            "0;JEQ",
        ]
    )


def generate_and() -> str:
    return "\n".join(
        [
            "// eq",
            INSTRUCTIONS["SP--"],
            "A=M",
            "D=M",
            INSTRUCTIONS["SP--"],
            "A=M",
            "M=M&D",
            INSTRUCTIONS["SP++"],
        ]
    )


def generate_gt() -> str:
    return "\n".join(
        [
            "// gt",
            INSTRUCTIONS["SP--"],
            "A=M",
            "D=M",
            INSTRUCTIONS["SP--"],
            "A=M",
            "M=M>D",
            INSTRUCTIONS["SP++"],
        ]
    )


def generate_lt() -> str:
    return "\n".join(
        [
            "// lt",
            INSTRUCTIONS["SP--"],
            "A=M",
            "D=M",
            INSTRUCTIONS["SP--"],
            "A=M",
            "M=M<D",
            INSTRUCTIONS["SP++"],
        ]
    )


def generate_sub() -> str:
    return "\n".join(
        [
            "// sub",
            INSTRUCTIONS["SP--"],
            "A=M",
            "D=M",
            INSTRUCTIONS["SP--"],
            "A=M",
            "M=M-D",
            INSTRUCTIONS["SP++"],
        ]
    )


def generate_or() -> str:
    return "\n".join(
        [
            "// or",
            INSTRUCTIONS["SP--"],
            "A=M",
            "D=M",
            INSTRUCTIONS["SP--"],
            "A=M",
            "M=M|D",
            INSTRUCTIONS["SP++"],
        ]
    )


def generate_neg() -> str:
    return "\n".join(
        [
            "// neg",
            INSTRUCTIONS["SP--"],
            "A=M",
            "M=-M",
            INSTRUCTIONS["SP++"],
        ]
    )


def generate_not() -> str:
    return "\n".join(
        [
            "// not",
            INSTRUCTIONS["SP--"],
            "A=M",
            "M=!M",
            INSTRUCTIONS["SP++"],
        ]
    )


def generate_eq(eq_count: int) -> str:
    return "\n".join(
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
            f"@EQUAL{eq_count}",
            "D;JEQ",
            "@SP",
            "A=M",
            "M=0",
            f"@CONT{eq_count}",
            "0;JEQ",
            f"(EQUAL{eq_count})",
            "@SP",
            "A=M",
            "M=1",
            f"(CONT{eq_count})",
        ]
    )


generators = {
    "add": generate_add,
    "sub": generate_sub,
    "or": generate_or,
    "and": generate_and,
}


def translate(vm_code: str) -> str:
    lines = clean_lines(vm_code.splitlines())

    eq_count = 0
    output = []
    for line in lines:
        command = line.split(" ")[0]
        if command == "push":
            _, mem_seg, value = line.split(" ")
            output.append(generate_push(int(value)))
        elif command == "eq":
            output.append(generate_eq(eq_count))
            eq_count += 1
        elif command in generators:
            output.append(generators[command]())
    output.append(generate_end())
    return "\n".join(output) + "\n"


if __name__ == "__main__":
    import sys
    from pathlib import Path

    target_file = Path(sys.argv[1])
    vm_code = target_file.read_text()
    target_file.with_suffix(".asm").write_text(translate(vm_code))
