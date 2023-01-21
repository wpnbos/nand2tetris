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


def clean_lines(lines: list[str]) -> list[str]:
    """
    Removes comments and empty lines.
    """
    return [
        cleaned_line.strip() for line in lines if (cleaned_line := line.split("//")[0])
    ]


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


def generate_add() -> str:
    return "\n".join(
        [
            "// add",
            pop_to_d(),
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
            "// and",
            pop_to_d(),
            "M=M&D",
            INSTRUCTIONS["SP++"],
        ]
    )


def generate_gt(comp_count: int) -> str:
    return "\n".join(
        [
            "// gt",
            pop_to_d(),
            "D=D-M",
            f"@GT{comp_count}",
            "D;JLT",
            "@SP",
            "A=M",
            "M=0",
            f"@CONT{comp_count}",
            "0;JEQ",
            f"(GT{comp_count})",
            "@SP",
            "A=M",
            "M=-1",
            f"(CONT{comp_count})",
            INSTRUCTIONS["SP++"],
        ]
    )


def generate_lt(comp_count: int) -> str:
    return "\n".join(
        [
            "// lt",
            pop_to_d(),
            "D=D-M",
            f"@LT{comp_count}",
            "D;JGT",
            "@SP",
            "A=M",
            "M=0",
            f"@CONT{comp_count}",
            "0;JEQ",
            f"(LT{comp_count})",
            "@SP",
            "A=M",
            "M=-1",
            f"(CONT{comp_count})",
            INSTRUCTIONS["SP++"],
        ]
    )


def generate_sub() -> str:
    return "\n".join(
        [
            "// sub",
            pop_to_d(),
            "M=M-D",
            INSTRUCTIONS["SP++"],
        ]
    )


def generate_or() -> str:
    return "\n".join(
        [
            "// or",
            pop_to_d(),
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
            pop_to_d(),
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
            "M=-1",
            f"(CONT{comp_count})",
            INSTRUCTIONS["SP++"],
        ]
    )


generators = {
    "add": generate_add,
    "sub": generate_sub,
    "or": generate_or,
    "and": generate_and,
    "not": generate_not,
    "neg": generate_neg,
}

COMPS = {"eq": generate_eq, "lt": generate_lt, "gt": generate_gt}


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
    target_file.with_suffix(".asm").write_text(translate(vm_code, target_file.stem))
