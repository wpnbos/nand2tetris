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


def generate_eq() -> str:
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


def translate(vm_code: str) -> str:
    lines = clean_lines(vm_code.splitlines())

    output = []
    for line in lines:
        command = line.split(" ")[0]
        if command == "push":
            _, mem_seg, value = line.split(" ")
            output.append(generate_push(int(value)))
        elif command == "add":
            output.append(generate_add())
        elif command == "sub":
            output.append(generate_sub())
        elif command == "or":
            output.append(generate_or())
        elif command == "and":
            output.append(generate_and())
    output.append(generate_end())
    return "\n".join(output) + "\n"
