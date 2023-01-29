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


def generate_push(mem_seg, address, dest):
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


def translate_push(line: str, file_stem: str) -> str:
    _, mem_seg, dest = line.split(" ")
    address = str(
        MEM_MAP[mem_seg] + int(dest)
        if mem_seg not in ("static", "constant")
        else f"{file_stem}.{int(dest)}"
    )
    return generate_push(mem_seg, address, dest)


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


def restore_register(register: str) -> str:
    return "\n".join(
        [
            f"// restore {register}",
            "@SP",
            "A=M",
            "D=M",
            f"@{register}",
            "M=D",
        ]
    )


def generate_return():
    return "\n".join(
        [
            "// return",
            "@ARG",  # Store ARG in TMP
            "D=M",
            "@R13",
            "M=D",
            INSTRUCTIONS["SP--"],  # Place return value at ARG
            "A=M",
            "D=M",
            "@ARG",
            "A=M",
            "M=D",
            "@LCL",  # Go to LCL to start restoring frame
            "D=M",
            "@SP",
            "M=D",  # Set SP to LCL
            INSTRUCTIONS["SP--"],  # Now at THAT
            restore_register("THAT"),
            INSTRUCTIONS["SP--"],  # Now at THIS
            restore_register("THIS"),
            INSTRUCTIONS["SP--"],  # Now at ARG
            restore_register("ARG"),
            INSTRUCTIONS["SP--"],  # Now at LCL
            restore_register("LCL"),
            INSTRUCTIONS["SP--"],  # Now somewhere in the arguments
            "@R13",
            "D=M",
            "@SP",
            "M=D",
            INSTRUCTIONS["SP++"],
            "A=M",
            "A=M",
            "0;JMP",
        ]
    )


def generate_goto(symbol: str) -> str:
    return "\n".join(
        [
            f"// goto {symbol}",
            f"@{symbol}",
            "0;JMP",
        ]
    )


def translate(vm_code: str, file_stem: str) -> str:
    # Seems to be a problem with gt. See first gt call in StackTest.vm
    lines = clean_lines(vm_code.splitlines())

    comp_count = 0
    call_count = 0
    output: list[str] = []
    # Generate bootstrap code
    output.append(
        "\n".join(
            [
                # "// bootstrap",
                # "@256",
                # "D=A",
                # "@SP",
                # "M=D",
                "// call Sys.init 0",  # Implement call to Sys.init
                generate_goto("Sys.init"),
            ]
        )
    )
    for line in lines:
        command = line.split(" ")[0]
        if command == "push":
            output.append(translate_push(line, file_stem))
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
        elif command == "goto":
            symbol = line.split(" ")[1]
            output.append(generate_goto(symbol))
        elif command == "function":
            _, symbol, n_vars = line.split(" ")
            output.append(
                "\n".join(
                    [f"// function {symbol} {n_vars}"]
                    + [f"({symbol})"]
                    + [generate_push("constant", None, 0) for _ in range(int(n_vars))]
                )
            )
        elif command == "return":
            output.append(generate_return())
        elif command == "call":
            _, symbol, n_args = line.split(" ")
            output.append(
                "\n".join(
                    [
                        f"// call {symbol} {n_args}",
                        "@SP // save new ARG to TMP",
                        "D=M",
                        f"@{n_args}",
                        "D=D-A",
                        "@R13",
                        "M=D",
                        f"@RETURN{call_count} // push return address",
                        "D=A",
                        "@SP",
                        "A=M",
                        "M=D",
                        INSTRUCTIONS["SP++"],
                        "@LCL // push LCL",
                        "D=M",
                        "@SP",
                        "A=M",
                        "M=D",
                        INSTRUCTIONS["SP++"],
                        "@ARG // push ARG",
                        "D=M",
                        "@SP",
                        "A=M",
                        "M=D",
                        INSTRUCTIONS["SP++"],
                        "@THIS // push THIS",
                        "D=M",
                        "@SP",
                        "A=M",
                        "M=D",
                        INSTRUCTIONS["SP++"],
                        "@THAT // push THAT",
                        "D=M",
                        "@SP",
                        "A=M",
                        "M=D",
                        INSTRUCTIONS["SP++"],
                        "@R13 // update ARG",
                        "D=M",
                        "@ARG",
                        "M=D",
                        "@SP // update LCL",
                        "D=M",
                        "@LCL",
                        "M=D",
                        generate_goto(symbol),
                        f"(RETURN{call_count})",
                    ],
                )
            )
            call_count += 1

    output.append(generate_end())
    return "\n".join(output) + "\n"


if __name__ == "__main__":
    import sys
    from pathlib import Path

    target_folder = Path(sys.argv[1])
    vm_files = target_folder.glob("*.vm")
    vm_code = "\n".join([file_.read_text() for file_ in vm_files])
    print(target_folder)
    target_folder.joinpath(target_folder.stem).with_suffix(".asm").write_text(
        translate(vm_code, target_folder.stem)
    )
