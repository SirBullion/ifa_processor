#!/usr/bin/env python3
import sys

OPCODES = {
    "NOP":         0x0,
    "LOAD":        0x1,
    "P8":          0x2,
    "INJECT":      0x3,
    "INV_CORRUPT": 0x4,
    "CORRECT":     0x5,
    "FINAL_INV":   0x6,
    "OUT":         0x7,
    "ADD":         0x8,
    "SUB":         0x9,
    "XOR_IMM":     0xA,
    "DEC":         0xB,
    "JMP":         0xC,
    "JZ":          0xD,
    "PRINT_ODU":   0xE,
    "HALT":        0xF,
}

def clean_line(line):
    return line.split(";")[0].strip()

def parse_immediate(token, labels=None):
    token = token.strip()

    if labels and token in labels:
        return labels[token]

    if len(token) >= 3 and token[0] == "'" and token[-1] == "'":
        content = token[1:-1]
        b = content.encode("utf-8")
        if len(b) != 1:
            raise Exception(f"Use PRINT for accented/multibyte character: {token}")
        return b[0]

    if token.lower().startswith("0x"):
        return int(token, 16)

    return int(token)

def expand_print(line):
    text = line.strip()
    upper = text.upper()

    # Native Odu print macros must be checked before generic PRINT
    if upper == "PRINT_ODU_ALL":
        out = []
        for i in range(256):
            out.append(f"LOAD 0x{i:02X}")
            out.append("PRINT_ODU")
        return out

    if upper.startswith("PRINT_ODU "):
        value = text.split()[1]
        return [f"LOAD {value}", "PRINT_ODU"]

    if upper == "PRINT_ODU":
        return [line]

    # Ifa Monitor v1 aliases
    if upper.startswith("PRINTODUALL"):
        return ["PRINT_ODU_ALL"]

    if upper.startswith("PRINTODU "):
        value = text.split()[1]
        return [f"LOAD {value}", "PRINT_ODU"]

    # Generic UTF-8 text print
    if not upper.startswith("PRINT"):
        return [line]

    start = text.find('"')
    end = text.rfind('"')

    if start == -1 or end == start:
        raise Exception("PRINT requires quoted text, e.g. PRINT \"IFÁ\"")

    content = text[start+1:end]

    # Support common escape sequences
    content = (
        content
        .replace("\\\\", "\\")
        .replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace("\\r", "\r")
    )

    out = []

    for b in content.encode("utf-8"):
        out.append(f"LOAD 0x{b:02X}")
        out.append("OUT")

    return out

def first_pass(lines):
    labels = {}
    pc = 0
    expected = None
    expanded = []

    for raw in lines:
        line = clean_line(raw)
        if not line:
            continue

        for ex in expand_print(line):
            ex = clean_line(ex)
            if not ex:
                continue

            if ex.endswith(":"):
                labels[ex[:-1]] = pc
                expanded.append(ex)
                continue

            if ex.upper().startswith("EXPECT"):
                expected = parse_immediate(ex.split()[1])
                expanded.append(ex)
                continue

            pc += 1
            expanded.append(ex)

    return labels, expected, expanded

def assemble_line(line, labels):
    line = clean_line(line)

    if not line or line.endswith(":") or line.upper().startswith("EXPECT"):
        return None

    parts = line.split()
    mnemonic = parts[0].upper()

    # Relation-space instructions
    if mnemonic == "FLIP_AGREEMENT":
        return 0x0001

    if mnemonic == "FORCE_AGREEMENT":
        return 0x0002

    if mnemonic == "FORCE_DISAGREEMENT":
        return 0x0003

    if mnemonic not in OPCODES:
        raise Exception(f"Unknown instruction: {mnemonic}")

    opcode = OPCODES[mnemonic]
    imm = 0

    if len(parts) > 1:
        imm = parse_immediate(parts[1], labels)

    return (opcode << 12) | (imm & 0xFF)

def assemble(source):
    lines = open(source, encoding="utf-8").read().splitlines()
    labels, expected, expanded = first_pass(lines)

    program = []

    for line in expanded:
        inst = assemble_line(line, labels)
        if inst is not None:
            program.append(inst)

    return program, expected, labels

def write_hex(program, filename):
    with open(filename, "w") as f:
        for inst in program:
            f.write(f"{inst:04X}\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tools/ifaasm.py program.ifa")
        return

    source = sys.argv[1]
    program, expected, labels = assemble(source)

    write_hex(program, "program.hex")

    if expected is not None:
        with open("expected.hex", "w") as f:
            f.write(f"{expected:02X}\n")

    print("\n========================================")
    print("IFÁ ASSEMBLER")
    print("========================================")
    print("Instructions :", len(program))

    if labels:
        print("Labels       :", labels)

    if expected is not None:
        print(f"Expected     : 0x{expected:02X}")

    print()
    for i, inst in enumerate(program):
        print(f"{i:02X}: {inst:04X}")

    print("\nGenerated:")
    print("program.hex")
    if expected is not None:
        print("expected.hex")

if __name__ == "__main__":
    main()
