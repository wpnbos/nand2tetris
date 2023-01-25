from functools import partial

INSTRUCTIONS = {"SP++": "@SP\nM=M+1", "SP--": "@SP\nM=M-1", "SP=D": "@SP\nA=M\nM=D"}
MEM_MAP = {
    "local": 1,
    "argument": 3,
    "this": 3,
    "that": 4,
    "pointer": 3,
    "temp": 5,
    "static": 16,
}
SYMBOLS = {
    "local": "LCL",
    "argument": "ARG",
    "this": "THIS",
    "that": "THAT",
    "pointer": "THIS",
}
OPERATORS = {"add": "+", "sub": "-", "and": "&", "or": "|", "neg": "-", "not": "!"}


def clean_lines(lines: list[str]) -> list[str]:
    """
    Removes comments and empty lines.
    """
    return [
        cleaned_line.strip() for line in lines if (cleaned_line := line.split("//")[0])
    ]


def generate_operator(operator: str) -> str:
    return "\n".join(
        [
            f"// {operator}",
            pop_to_d(),
            f"M=M{OPERATORS[operator]}D",
            INSTRUCTIONS["SP++"],
        ]
    )


def pop_to_d() -> str:
    return "\n".join(
        [
            INSTRUCTIONS["SP--"],
            "A=M",
            "D=M",
            INSTRUCTIONS["SP--"],
            "A=M",
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


def generate_comp(comp: str, comp_count: int) -> str:
    return "\n".join(
        [
            f"// {comp}",
            pop_to_d(),
            "D=D-M",
            f"@COMP{comp_count}",
            "D;JEQ" if comp == "eq" else "D;JGT" if comp == "lt" else "D;JLT",
            "@SP",
            "A=M",
            "M=0",
            f"@CONT{comp_count}",
            "0;JEQ",
            f"(COMP{comp_count})",
            "@SP",
            "A=M",
            "M=-1",
            f"(CONT{comp_count})",
            INSTRUCTIONS["SP++"],
        ]
    )


def generate_single_value_operator(operator: str) -> str:
    return "\n".join(
        [
            f"// {operator}",
            INSTRUCTIONS["SP--"],
            "A=M",
            f"M={OPERATORS[operator]}M",
            INSTRUCTIONS["SP++"],
        ]
    )


generators = {
    "add": partial(generate_operator, "add"),
    "sub": partial(generate_operator, "sub"),
    "or": partial(generate_operator, "or"),
    "and": partial(generate_operator, "and"),
    "not": partial(generate_single_value_operator, "not"),
    "neg": partial(generate_single_value_operator, "neg"),
}


def push_constant_to_d(value: int) -> str:
    return f"@{value}\nD=A"


def push_value_from_address_to_d(address: str) -> str:
    return f"@{address}\nD=M"


def push_value_from_mem_seg_to_d(mem_seg: str, i: int) -> str:
    return "\n".join(
        [
            f"@{SYMBOLS[mem_seg]}",
            "D=M",
            f"@{i}",
            "A=D+A",
            "D=M",
        ]
    )


def generate_push(line: str, file_stem: str) -> str:
    _, mem_seg, dest = line.split(" ")
    address = str(
        MEM_MAP[mem_seg] + int(dest)
        if mem_seg not in ("static", "constant")
        else f"{file_stem}.{int(dest)}"
    )
    instruction = "\n".join(
        [
            f"// push {mem_seg} {dest}",
            push_value_from_address_to_d(address)
            if mem_seg in ("temp", "pointer", "static")
            else push_constant_to_d(int(dest))
            if mem_seg == "constant"
            else push_value_from_mem_seg_to_d(mem_seg, int(dest)),
            INSTRUCTIONS["SP=D"],
            INSTRUCTIONS["SP++"],
        ]
    )
    return instruction


def generate_pop(line: str, file_stem: str) -> str:
    _, mem_seg, dest = line.split(" ")
    if mem_seg in ("temp", "pointer", "static"):
        address = (
            MEM_MAP[mem_seg] + int(dest)
            if not mem_seg == "static"
            else f"{file_stem}.{int(dest)}"
        )
        return "\n".join(
            [
                f"// pop {mem_seg} {dest}",
                f"@{address}",
                "D=A",
                "@R13",
                "M=D",
                "@SP",
                "M=M-1",
                "A=M",
                "D=M",
                "@R13",
                "A=M",
                "M=D",
            ]
        )
    else:
        return "\n".join(
            [
                f"// pop {mem_seg} {dest}",
                f"@{SYMBOLS[mem_seg]}",
                "D=M",
                f"@{dest}",
                "D=D+A",
                "@R13",
                "M=D",
                "@SP",
                "M=M-1",
                "A=M",
                "D=M",
                "@R13",
                "A=M",
                "M=D",
            ]
        )


def translate(vm_code: str, file_stem: str) -> str:
    # Seems to be a problem with gt. See first gt call in StackTest.vm
    lines = clean_lines(vm_code.splitlines())

    comp_count = 0
    output = []
    for line in lines:
        command = line.split(" ")[0]
        if command == "push":
            output.append(generate_push(line, file_stem))
        elif command == "pop":
            output.append(generate_pop(line, file_stem))
        elif command in ("gt", "lt", "eq"):
            output.append(generate_comp(command, comp_count))
            comp_count += 1
        elif command in generators:
            output.append(generators[command]())
        elif command == "label":
            symbol = line.split(" ")[1]
            output.append(f"({symbol})")
        elif command == "if-goto":
            symbol = line.split(" ")[1]
            output.append(
                "\n".join(
                    [
                        f"// if-goto {symbol}",
                        INSTRUCTIONS["SP--"],
                        "A=M",
                        "D=M",
                        f"@{symbol}",
                        "D;JNE",
                    ]
                )
            )

    output.append(generate_end())
    return "\n".join(output) + "\n"


if __name__ == "__main__":
    import sys
    from pathlib import Path

    target_file = Path(sys.argv[1])
    vm_code = target_file.read_text()
    target_file.with_suffix(".asm").write_text(translate(vm_code, target_file.stem))
