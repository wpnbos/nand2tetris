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


def generate_gt(comp_count: int) -> str:
    return "\n".join(
        [
            "// gt",
            INSTRUCTIONS["SP--"],
            "A=M",
            "D=M",
            INSTRUCTIONS["SP--"],
            "A=M",
            "D=M-D",
            f"@GT{comp_count}",
            "D;JGT",
            "@SP",
            "A=M",
            "M=0",
            f"@CONT{comp_count}",
            "0;JEQ",
            f"(GT{comp_count})",
            "@SP",
            "A=M",
            "M=1",
            f"(CONT{comp_count})",
        ]
    )


def generate_lt(comp_count: int) -> str:
    return "\n".join(
        [
            "// lt",
            INSTRUCTIONS["SP--"],
            "A=M",
            "D=M",
            INSTRUCTIONS["SP--"],
            "A=M",
            "D=D-M",
            f"@LT{comp_count}",
            "D;JLT",
            "@SP",
            "A=M",
            "M=0",
            f"@CONT{comp_count}",
            "0;JEQ",
            f"(LT{comp_count})",
            "@SP",
            "A=M",
            "M=1",
            f"(CONT{comp_count})",
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


def generate_eq(comp_count: int) -> str:
    return "\n".join(
        [
            "// eq",
            INSTRUCTIONS["SP--"],
            "A=M",
            "D=M",
            INSTRUCTIONS["SP--"],
            "A=M",
            "D=M-D",
            f"@EQUAL{comp_count}",
            "D;JEQ",
            "@SP",
            "A=M",
            "M=0",
            f"@CONT{comp_count}",
            "0;JEQ",
            f"(EQUAL{comp_count})",
            "@SP",
            "A=M",
            "M=1",
            f"(CONT{comp_count})",
        ]
    )


generators = {
    "add": generate_add,
    "sub": generate_sub,
    "or": generate_or,
    "and": generate_and,
}

COMPS = {"eq": generate_eq, "lt": generate_lt, "gt": generate_gt}


def translate(vm_code: str) -> str:
    # Seems to be a problem with gt. See first gt call in StackTest.vm
    lines = clean_lines(vm_code.splitlines())

    comp_count = 0
    output = []
    for line in lines:
        command = line.split(" ")[0]
        if command == "push":
            _, mem_seg, value = line.split(" ")
            output.append(generate_push(int(value)))
        elif command in COMPS:
            output.append(COMPS[command](comp_count))
            comp_count += 1
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
