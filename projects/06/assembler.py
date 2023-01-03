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

JUMP_CODES = {
    "JGT": "000",
    "JEQ": "001",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111",
}


def assemble(assembly_code: str) -> str:
    binary_codes = []
    lines = assembly_code.splitlines()
    for line in lines:
        print(line)
        # Skip comments
        line = line.strip()
        if line.startswith("//") or not line:
            continue
        if line.startswith("@"):
            # Line is an A-instruction
            value = int(line[1:])
            binary_value = format(value, "015b")
            binary_code = f"0{binary_value}"
            binary_codes.append(binary_code)
        else:
            # Line is a C-instruction
            dest, comp, jump = None, None, None
            if "=" in line:
                dest, comp = line.split("=")
            if comp and ";" in comp:
                comp, jump = comp.split(";")
            for part in (dest, comp, jump):
                if part:
                    part = part.strip()
            print(f"{dest=}, {comp=}, {jump=}")
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

            jump_code = "000"
            if jump:
                jump_code = JUMP_CODES[jump]

            binary_codes.append(f"111{a}{comp_code}{dest_code}{jump_code}")
    binary_code = "\n".join(binary_codes) + "\n"
    print(binary_code)
    return binary_code
