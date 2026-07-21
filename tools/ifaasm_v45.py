#!/usr/bin/env python3
"""Assembler for the backward-compatible IFÁ V4.5 native ISA.

V4.5 retains every V4 encoding and adds major class 0x4 for the data
movement needed by compiled programs.  Keeping this assembler separate is
intentional: V4 source and binaries continue to use ``ifaasm_v4.py``.
"""

import sys
from pathlib import Path

try:
    from tools.ifaasm_v4 import (
        assemble_instruction as assemble_v4_instruction,
        collect_labels,
        normalize_mnemonic,
        parse_number,
        strip_label,
        write_outputs,
    )
except ModuleNotFoundError:  # Direct execution from the tools directory.
    from ifaasm_v4 import (
        assemble_instruction as assemble_v4_instruction,
        collect_labels,
        normalize_mnemonic,
        parse_number,
        strip_label,
        write_outputs,
    )


DATA_OPERATIONS = {
    "MOVY_A": 0x0,
    "MOVY_B": 0x1,
    "MOVADDR_A": 0x2,
    "MOVADDR_B": 0x3,
    "LOAD_A": 0x4,
    "LOAD_B": 0x5,
    "STORE_A": 0x6,
    "STORE_B": 0x7,
}

DATA_ALIASES = {
    "MOVYA": "MOVY_A",
    "MOVYB": "MOVY_B",
    "MOVADDRA": "MOVADDR_A",
    "MOVADDRB": "MOVADDR_B",
    "LOADA": "LOAD_A",
    "LOADB": "LOAD_B",
    "STOREA": "STORE_A",
    "STOREB": "STORE_B",
}

ARG_SOURCES = {
    "A": 0x0, "B": 0x1, "ADDRESS": 0x2, "FLAGS": 0x3,
}
REGISTER_PRINTS = {
    "PRINTA": 0x0, "PRINTB": 0x1, "PRINTADDR": 0x2, "PRINTFLAGS": 0x3,
}


def assemble_instruction(line, labels):
    instruction = strip_label(line)
    if not instruction:
        return None

    parts = instruction.split()
    mnemonic = normalize_mnemonic(parts[0])
    mnemonic = DATA_ALIASES.get(mnemonic, mnemonic)

    if mnemonic in DATA_OPERATIONS:
        if len(parts) != 1:
            raise ValueError(f"{mnemonic} takes no operands")
        return 0x4000 | (DATA_OPERATIONS[mnemonic] << 8)

    if mnemonic == "ARGBEGIN":
        if len(parts) != 1:
            raise ValueError("ARGBEGIN takes no operands")
        return 0x6000

    if mnemonic == "ARG":
        if len(parts) != 3:
            raise ValueError("ARG syntax: ARG <0..3> <A|B|ADDRESS|FLAGS>")
        destination = parse_number(parts[1], labels)
        source = parts[2].upper()
        if not 0 <= destination <= 3:
            raise ValueError("ARG destination must be between 0 and 3")
        if source not in ARG_SOURCES:
            raise ValueError("ARG source must be A, B, ADDRESS, or FLAGS")
        return 0x5000 | (destination << 10) | (ARG_SOURCES[source] << 8)

    if mnemonic in REGISTER_PRINTS:
        if len(parts) != 1:
            raise ValueError(f"{mnemonic} takes no operands")
        return 0x7000 | (REGISTER_PRINTS[mnemonic] << 8)

    if mnemonic == "RETVOID":
        if len(parts) != 1:
            raise ValueError("RETVOID takes no operands")
        return 0xFE00

    # V4's published CALL encoding is retained, while avoiding the V4
    # assembler's historical reference to the undefined parse_value helper.
    if mnemonic == "CALL":
        if len(parts) != 2:
            raise ValueError("CALL requires one target")
        target = parse_number(parts[1], labels)
        if not 0 <= target <= 0xFF:
            raise ValueError("CALL target must fit in 8 bits")
        return 0xFB00 | target

    return assemble_v4_instruction(line, labels)


def assemble(lines):
    labels = collect_labels(lines)
    program = []
    listing = []

    for line_number, source_line in enumerate(lines, start=1):
        instruction_text = strip_label(source_line)
        if not instruction_text:
            continue
        try:
            word = assemble_instruction(source_line, labels)
        except Exception as error:
            raise ValueError(
                f"Line {line_number}: {error}\n    {source_line.rstrip()}"
            ) from error
        if word is not None:
            listing.append((len(program), word, instruction_text))
            program.append(word)

    if len(program) > 256:
        raise ValueError("V4.5 program exceeds 256 instructions")
    return program, listing


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/ifaasm_v45.py <program.ifa45> [output-prefix]")
        raise SystemExit(1)

    source_path = Path(sys.argv[1])
    output_prefix = Path(sys.argv[2]) if len(sys.argv) >= 3 else source_path.with_suffix("")
    lines = source_path.read_text(encoding="utf-8").splitlines()
    program, listing = assemble(lines)
    hex_path = output_prefix.with_suffix(".hex")
    list_path = output_prefix.with_suffix(".lst")
    write_outputs(program, listing, hex_path, list_path)
    print(f"Assembled {len(program)} V4.5 instructions -> {hex_path}")
    print(f"Listing -> {list_path}")


if __name__ == "__main__":
    main()
