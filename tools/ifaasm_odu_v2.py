#!/usr/bin/env python3
import sys

OP = {
    "LOADA": 0x1,
    "LOADB": 0x2,
    "ADDR":  0x3,
    "ODU_RAW": 0x4,
    "ODU_FEEDBACK": 0x5,
    "ODU_STORE": 0x6,
    "ODU_RECALL": 0x7,
    "RPC_ADD": 0x8,
    "RPC_SUB": 0x9,
    "RPC_COMPARE": 0xA,
    "RMU_CLEAR": 0xB,
    "RMU_COPY": 0xC,
    "RMU_MOVE": 0xD,
    "RMU_SWAP": 0xE,
    "HALT": 0xF,
}

BR = {"BR_EQ": 1, "BR_GT": 2, "BR_LT": 3}

def clean(line):
    return line.split(";")[0].strip()

def expand_macros(lines):
    out = []
    for line in lines:
        raw = clean(line)
        if not raw:
            out.append(line)
            continue
        if raw.upper() == "PRINTODU":
            out += [
                "PRINTY\n",
                "PRINTRA\n",
                "PRINTRD\n",
                "PRINTR0\n",
                "PRINTT\n"
            ]
            continue

        if raw.upper() in ("DÁIFÁ", "DAIFA"):
            for i in range(16):
                out += [
                    f"LOADA 0x{i:02X}\n",
                    "LOADB 0x00\n",
                    "RPC_ADD\n",
                    "PRINTY\n"
                ]
            continue

        if raw.upper() == "PRINTODUALL":
            out += [
                "PRINTA\n",
                "PRINTB\n",
                "PRINTPC\n",
                "PRINTIR\n",
                "PRINTY\n",
                "PRINTRA\n",
                "PRINTRD\n",
                "PRINTR0\n",
                "PRINTT\n"
            ]
            continue

        if raw.upper() == "DAFA":
            # DAFA: print the 16 Oju Odu, 0x0 through 0xF.
            for i in range(16):
                out += [
                    f"LOADA 0x{i:02X}\n",
                    "LOADB 0x00\n",
                    "RPC_ADD\n",
                    "PRINTY\n"
                ]
            continue

        out.append(line)
    return out

def parse_num(s, labels=None):
    s = s.strip()
    if labels and s in labels:
        return labels[s]
    if s.startswith("0x"):
        return int(s, 16)
    return int(s, 0)

def first_pass(lines):
    labels = {}
    cleaned = []
    pc = 0

    for line in lines:
        line = clean(line)
        if not line:
            continue

        if line.endswith(":"):
            labels[line[:-1]] = pc
            continue

        cleaned.append((pc, line))
        pc += 1

    return labels, cleaned

def assemble_line(line, labels):
    parts = line.split()
    m = parts[0].upper()

    if m in BR:
        target = parse_num(parts[1], labels) & 0xFF
        return (0x0 << 12) | ((BR[m] & 0xF) << 8) | target

    if m == "NOP":
        return 0x0000

    if m == "JMP":
        target = parse_num(parts[1], labels) & 0xFF
        return 0x0400 | target

    if m == "CALL":
        target = parse_num(parts[1], labels) & 0xFF
        return 0xF100 | target

    if m == "RET":
        return 0xF200

    if m == "PUSH":
        return 0xF300

    if m == "POP":
        return 0xF400

    if m == "RPUSH":
        return 0xF500

    if m == "RPOP":
        return 0xF600

    if m == "PRINTY":
        return 0xF700

    if m == "PRINTRA":
        return 0xF800

    if m == "PRINTRD":
        return 0xF900

    if m == "PRINTR0":
        return 0xFA00

    if m == "PRINTT":
        return 0xFB00

    if m == "PRINTA":
        return 0xFC00

    if m == "PRINTB":
        return 0xFD00

    if m == "PRINTPC":
        return 0xFE00

    if m == "PRINTIR":
        return 0xFF00

    if m not in OP:
        raise Exception(f"Unknown instruction: {m}")

    imm = parse_num(parts[1], labels) if len(parts) > 1 else 0
    return (OP[m] << 12) | (imm & 0xFF)

def main():
    if len(sys.argv) < 2:
        print("usage: ifaasm_odu_v2.py program.ifa")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        raw_lines = f.readlines()

    lines = expand_macros(raw_lines)
    labels, cleaned = first_pass(lines)

    program = []
    listing = []

    for pc, line in cleaned:
        inst = assemble_line(line, labels)
        program.append(inst)
        listing.append((pc, inst, line))

    with open("odu_v2_program.hex", "w") as f:
        for inst in program:
            f.write(f"{inst:04x}\n")

    with open("odu_v2_program.lst", "w") as f:
        f.write("IFÁ ODU V2 PROGRAM ADDRESS MAP\n")
        f.write("=" * 60 + "\n")
        for addr in range(256):
            match = [x for x in listing if x[0] == addr]
            if match:
                pc, inst, line = match[0]
                f.write(f"{addr:03d} 0x{addr:02X}  {inst:04x}  {line}\n")
            else:
                f.write(f"{addr:03d} 0x{addr:02X}  ----  <free>\n")

    print(f"Assembled {len(program)} instructions -> odu_v2_program.hex")
    print("Address map saved -> odu_v2_program.lst")
    print()
    print("Used addresses:")
    for pc, inst, line in listing:
        print(f"{pc:03d} 0x{pc:02X}  {inst:04x}  {line}")

if __name__ == "__main__":
    main()
