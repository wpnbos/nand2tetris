from copy import deepcopy


COMP_CODES = {
    "0": "101010",
    "1": "111111",
    "-1": "111010",
    "D": "001100",
    "A": "110000",
    "!D": "001101",
    "!A": "110001",
    "-D": "001111",
    "-A": "110011",
    "D+1": "011111",
    "A+1": "110111",
    "D-1": "001110",
    "A-1": "110010",
    "D+A": "000010",
    "A+D": "000010",
    "D-A": "010011",
    "A-D": "000111",
    "D&A": "000000",
    "D|A": "010101",
}

JMP_CODES = {
    "JGT": "001",
    "JEQ": "010",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111",
}


SYMBOLS = {
    "SCREEN": 16384,
    "KBD": 24576,
}
for i, symbol in enumerate(("SP", "LCL", "ARG", "THIS", "THAT")):
    SYMBOLS[symbol] = i
for i in range(16):
    SYMBOLS[f"R{i}"] = i


def get_label_symbols(lines: list[str]) -> dict[str, int]:
    label_symbols = {}

    line_counter = 0
    for line in lines:
        if line.startswith("("):
            # Line is a label declaration
            symbol = line.replace("(", "").replace(")", "")
            label_symbols[symbol] = line_counter
            continue
        line_counter += 1

    return label_symbols


def clean_lines(lines: list[str]) -> list[str]:
    """
    Removes comments and empty lines.
    """
    return [
        cleaned_line.strip() for line in lines if (cleaned_line := line.split("//")[0])
    ]


def assemble_c_instruction(instruction: str) -> str:
    dest, comp, jmp = None, None, None
    comp = instruction
    if "=" in comp:
        dest, comp = comp.split("=")
    if ";" in comp:
        comp, jmp = comp.split(";")
    for part in (dest, comp, jmp):
        if part:
            part = part.strip()

    dest_code = [0, 0, 0]
    if dest:
        dest = "".join(sorted(dest))
        if "A" in dest:
            dest_code[0] = 1
        if "D" in dest:
            dest_code[1] = 1
        if "M" in dest:
            dest_code[2] = 1
    dest_code = "".join([str(bit_) for bit_ in dest_code])

    comp_code = "000000"
    if comp:
        comp_code = COMP_CODES[comp.replace("M", "A")]
        a = "1" if "M" in comp else "0"

    jmp_code = "000"
    if jmp:
        jmp_code = JMP_CODES[jmp]

    return f"111{a}{comp_code}{dest_code}{jmp_code}"


def assemble(assembly_code: str) -> str:
    binary_codes = []
    lines = clean_lines(assembly_code.splitlines())
    symbols = deepcopy(SYMBOLS) | get_label_symbols(lines)

    address_counter = 16
    for line in lines:
        if line.startswith("("):
            # Skip label declarations
            continue
        if line.startswith("@"):
            # Line is an A-instruction
            value = line[1:]
            try:
                value = int(value)
            except ValueError:
                # Instruction contains a symbol
                if value not in symbols:
                    symbols[value] = address_counter
                    address_counter += 1
                value = symbols[value]
            binary_value = format(value, "015b")
            binary_code = f"0{binary_value}"
            binary_codes.append(binary_code)
        else:
            # Line is a C-instruction
            binary_codes.append(assemble_c_instruction(line))

    binary_code = "\n".join(binary_codes) + "\n"
    return binary_code


if __name__ == "__main__":
    import sys
    from pathlib import Path

    target_file = Path(sys.argv[1])
    write_path = target_file.parent.joinpath(f"{target_file.stem}.hack")
    write_path.write_text(assemble(target_file.read_text()))
