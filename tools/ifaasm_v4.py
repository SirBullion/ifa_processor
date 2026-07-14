#!/usr/bin/env python3

import sys
from pathlib import Path


#======================================================================
# IFÁ V4 instruction encoding
#
# 0x0Ctt : branch/jump
# 0x1Iii : LDAI immediate
# 0x2Iii : LDBI immediate
# 0x3Iii : LDADDR immediate
# 0x8O00 : native operation
# 0xF000 : NOP
# 0xF100 : HALT
#======================================================================


NATIVE_OPERATIONS = {
    "PAPO":  0x0,
    "YO":    0x1,
    "DAGBA": 0x2,
    "PIN":   0x3,
    "KU":    0x4,
    "GBE":   0x5,
    "SEDA":  0x6,
    "JU":    0x7,
    "KERE":  0x8,
}


ALIASES = {
    "PÀPỌ̀": "PAPO",
    "YỌ": "YO",
    "DÁGBA": "DAGBA",
    "KÙ": "KU",
    "GBÉ": "GBE",
    "ṢẸ̀DÁ": "SEDA",
    "JÙ": "JU",
    "KERÉ": "KERE",

    "LOADA": "LDAI",
    "LOADB": "LDBI",
    "ADDR": "LDADDR",

    "DURO": "HALT",
    "DÚRÓ": "HALT",
}


BRANCH_CONDITIONS = {
    "BR_EQ": 0x1,
    "BR_GT": 0x2,
    "BR_LT": 0x3,
    "JMP":   0x4,
}


def clean_line(line):
    """Remove comments and surrounding whitespace."""

    return line.split(";", 1)[0].strip()


def normalize_mnemonic(value):
    mnemonic = value.strip().upper()
    return ALIASES.get(mnemonic, mnemonic)


def parse_number(value, labels):
    token = value.strip()

    if token in labels:
        return labels[token]

    upper = token.upper()

    if upper in labels:
        return labels[upper]

    return int(token, 0)


def collect_labels(lines):
    labels = {}
    pc = 0

    for source_line in lines:
        line = clean_line(source_line)

        if not line:
            continue

        while ":" in line:
            label, remainder = line.split(":", 1)
            label = label.strip().upper()

            if not label:
                raise ValueError("Empty label name")

            if label in labels:
                raise ValueError(
                    f"Duplicate label: {label}"
                )

            labels[label] = pc
            line = remainder.strip()

            if not line:
                break

        if line:
            pc += 1

    return labels


def strip_label(line):
    instruction = clean_line(line)

    while ":" in instruction:
        _, instruction = instruction.split(":", 1)
        instruction = instruction.strip()

    return instruction


def assemble_instruction(line, labels):
    instruction = strip_label(line)

    if not instruction:
        return None

    parts = instruction.split()
    mnemonic = normalize_mnemonic(parts[0])

    #------------------------------------------------------------------
    # Immediate context instructions
    #------------------------------------------------------------------

    if mnemonic == "LDAI":
        if len(parts) != 2:
            raise ValueError("LDAI syntax: LDAI <value>")

        immediate = parse_number(
            parts[1],
            labels,
        ) & 0xFF

        return 0x1000 | immediate

    if mnemonic == "LDBI":
        if len(parts) != 2:
            raise ValueError("LDBI syntax: LDBI <value>")

        immediate = parse_number(
            parts[1],
            labels,
        ) & 0xFF

        return 0x2000 | immediate

    if mnemonic == "LDADDR":
        if len(parts) != 2:
            raise ValueError(
                "LDADDR syntax: LDADDR <value>"
            )

        immediate = parse_number(
            parts[1],
            labels,
        ) & 0xFF

        return 0x3000 | immediate

    #------------------------------------------------------------------
    # Native IFÁ mathematical operations
    #------------------------------------------------------------------

    if mnemonic in NATIVE_OPERATIONS:
        if len(parts) != 1:
            raise ValueError(
                f"{mnemonic} takes no inline operands; "
                "load A and B first"
            )

        operation = NATIVE_OPERATIONS[mnemonic]

        return (
            0x8000
            | ((operation & 0xF) << 8)
        )

    #------------------------------------------------------------------
    # Branch and jump instructions
    #------------------------------------------------------------------

    if mnemonic in BRANCH_CONDITIONS:
        if len(parts) != 2:
            raise ValueError(
                f"{mnemonic} syntax: "
                f"{mnemonic} <target>"
            )

        target = parse_number(
            parts[1],
            labels,
        ) & 0xFF

        condition = BRANCH_CONDITIONS[mnemonic]

        return (
            ((condition & 0xF) << 8)
            | target
        )

    #------------------------------------------------------------------
    # System instructions
    #------------------------------------------------------------------

    if mnemonic == "NOP":
        if len(parts) != 1:
            raise ValueError("NOP takes no operands")

        return 0xF000

    if mnemonic == "HALT":
        if len(parts) != 1:
            raise ValueError("HALT takes no operands")

        return 0xF100

    if mnemonic == "PRINTY":
        if len(parts) != 1:
            raise ValueError("PRINTY takes no operands")

        return 0xF200

    if mnemonic == "PRINTRA":
        if len(parts) != 1:
            raise ValueError("PRINTRA takes no operands")

        return 0xF300

    if mnemonic == "PRINTRD":
        if len(parts) != 1:
            raise ValueError("PRINTRD takes no operands")

        return 0xF400

    if mnemonic == "PRINTR0":
        if len(parts) != 1:
            raise ValueError("PRINTR0 takes no operands")

        return 0xF500

    if mnemonic == "PRINTT":
        if len(parts) != 1:
            raise ValueError("PRINTT takes no operands")

        return 0xF600

    if mnemonic == "PRINTOP":
        if len(parts) != 1:
            raise ValueError("PRINTOP takes no operands")

        return 0xF700

    if mnemonic == "PRINTSTATUS":
        if len(parts) != 1:
            raise ValueError("PRINTSTATUS takes no operands")

        return 0xF800

    if mnemonic == "RPUSH":
        if len(parts) != 1:
            raise ValueError("RPUSH takes no operands")

        return 0xF900

    if mnemonic == "RPOP":
        if len(parts) != 1:
            raise ValueError("RPOP takes no operands")

        return 0xFA00

    if mnemonic == "CALL":
        if len(parts) != 2:
            raise ValueError("CALL requires one target")

        target = parse_value(parts[1], labels)

        if not 0 <= target <= 0xFF:
            raise ValueError("CALL target must fit in 8 bits")

        return 0xFB00 | target

    if mnemonic == "RET":
        if len(parts) != 1:
            raise ValueError("RET takes no operands")

        return 0xFC00

    raise ValueError(
        f"Unknown V4 instruction: {mnemonic}"
    )


def assemble(lines):
    labels = collect_labels(lines)

    program = []
    listing = []

    for line_number, source_line in enumerate(
        lines,
        start=1,
    ):
        instruction_text = strip_label(source_line)

        if not instruction_text:
            continue

        try:
            word = assemble_instruction(
                source_line,
                labels,
            )
        except Exception as error:
            raise ValueError(
                f"Line {line_number}: {error}\n"
                f"    {source_line.rstrip()}"
            ) from error

        if word is None:
            continue

        address = len(program)

        program.append(word)

        listing.append(
            (
                address,
                word,
                instruction_text,
            )
        )

    if len(program) > 256:
        raise ValueError(
            "V4 program exceeds 256 instructions"
        )

    return program, listing


def write_outputs(
    program,
    listing,
    hex_path,
    list_path,
):
    with hex_path.open(
        "w",
        encoding="utf-8",
    ) as output:
        for word in program:
            output.write(f"{word:04x}\n")

    with list_path.open(
        "w",
        encoding="utf-8",
    ) as output:
        for address, word, instruction in listing:
            output.write(
                f"{address:02x}  "
                f"{word:04x}  "
                f"{instruction}\n"
            )


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python3 tools/ifaasm_v4.py "
            "<program.ifa4> [output-prefix]"
        )
        raise SystemExit(1)

    source_path = Path(sys.argv[1])

    if len(sys.argv) >= 3:
        output_prefix = Path(sys.argv[2])
    else:
        output_prefix = source_path.with_suffix("")

    hex_path = output_prefix.with_suffix(".hex")
    list_path = output_prefix.with_suffix(".lst")

    lines = source_path.read_text(
        encoding="utf-8",
    ).splitlines()

    program, listing = assemble(lines)

    write_outputs(
        program,
        listing,
        hex_path,
        list_path,
    )

    print(
        f"Assembled {len(program)} V4 instructions "
        f"-> {hex_path}"
    )

    print(
        f"Listing -> {list_path}"
    )


if __name__ == "__main__":
    main()
