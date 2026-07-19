#!/usr/bin/env python3

# --- IFÁ project import bootstrap ---
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# -----------------------------------

import sys
from language_v3.kernel import kernel

ALIASES = kernel.dictionary
NUMBER_WORDS = kernel.numbers
OPERATORS = kernel.operators

def norm(word):
    w = word.strip().upper()
    return ALIASES.get(w, w)


ODU_VALUES = {
    "OGBE": 0x00,
    "ÒGBÈ": 0x00,
    "OYEKU": 0x01,
    "ÒYÈKÚ": 0x01,
    "IWORI": 0x02,
    "ÌWÒRÌ": 0x02,
    "ODI": 0x03,
    "ÒDÍ": 0x03,
    "IROSUN": 0x04,
    "ÌRÒSÙN": 0x04,
    "OWONRIN": 0x05,
    "ÒWÓNRÍN": 0x05,
    "OBARA": 0x06,
    "ÒBÀRÀ": 0x06,
    "OKANRAN": 0x07,
    "ÒKÀNRÀN": 0x07,
    "OGUNDA": 0x08,
    "ÒGÚNDÁ": 0x08,
    "OSA": 0x09,
    "ÒSÁ": 0x09,
    "IKA": 0x0A,
    "ÌKÁ": 0x0A,
    "OTURUPON": 0x0B,
    "ÒTÚRÚPỌ̀N": 0x0B,
    "OTURA": 0x0C,
    "ÒTÚRÁ": 0x0C,
    "IRETE": 0x0D,
    "ÌRETÈ": 0x0D,
    "OSE": 0x0E,
    "Ọ̀ṢẸ́": 0x0E,
    "OFUN": 0x0F,
    "ÒFÚN": 0x0F,
}

def parse_value(x):
    x = norm(x)

    if x in ODU_VALUES:
        return ODU_VALUES[x]

    if x in NUMBER_WORDS:
        return NUMBER_WORDS[x] & 0xFF

    if x.lower().startswith("0x"):
        return int(x, 16) & 0xFF

    return int(x, 0) & 0xFF

def compile_binary(op, a_raw, b_raw):
    if op not in OPERATORS:
        raise SystemExit(f"Unknown IFÁ operator: {op}")

    info = OPERATORS[op]

    if info.get("reserved"):
        family = info.get("family", "unknown")
        raise SystemExit(
            f"{op} is reserved for native IFÁ V3 {family}. "
            "Define relation algorithm first."
        )

    a = parse_value(a_raw)
    b = parse_value(b_raw)

    return [
        f"GBA A 0x{a:02X}\n",
        f"GBA B 0x{b:02X}\n",
        f"{info['opcode']}\n",
    ]

def compile_line(line):
    raw = line.strip()

    if not raw or raw.startswith(";"):
        return [line]

    parts = [norm(p) for p in raw.split()]

    if parts[0] == "BERE":
        return []

    if parts[0] == "DURO":
        return ["DURO\n"]

    if len(parts) == 2 and parts[0] == "TE" and parts[1] == "ODU":
        return ["TEODU\n"]

    if len(parts) == 4 and parts[2] == "ATI":
        return compile_binary(parts[0], parts[1], parts[3])

    return [line]

def main():
    if len(sys.argv) != 3:
        print("usage: ifa_yoruba_frontend.py input.ifa3 output.ifa")
        raise SystemExit(1)

    out = []

    with open(sys.argv[1], encoding="utf-8") as f:
        for line in f:
            out.extend(compile_line(line))

    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.writelines(out)

if __name__ == "__main__":
    main()
