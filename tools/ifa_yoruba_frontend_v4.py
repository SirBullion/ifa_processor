#!/usr/bin/env python3

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


#======================================================================
# IFÁ V4 Yorùbá vocabulary
#======================================================================

ALIASES = {
    # Program structure
    "BẸ̀RẸ̀": "BERE",
    "BERE": "BERE",

    "DÚRÓ": "HALT",
    "DURO": "HALT",
    "HALT": "HALT",

    # Operand connector
    "ÀTI": "ATI",
    "ATI": "ATI",

    # Native operations
    "PÀPỌ̀": "PAPO",
    "PAPO": "PAPO",

    "YỌ": "YO",
    "YO": "YO",

    "DÁGBA": "DAGBA",
    "DAGBA": "DAGBA",

    "PÍN": "PIN",
    "PIN": "PIN",

    "KÙ": "KU",
    "KU": "KU",

    "GBÉ": "GBE",
    "GBE": "GBE",

    "ṢẸ̀DÁ": "SEDA",
    "SEDA": "SEDA",

    "JÙ": "JU",
    "JU": "JU",

    "KERÉ": "KERE",
    "KERE": "KERE",

    # V4 output operations
    "TẸ̀Y": "PRINTY",
    "TEY": "PRINTY",
    "PRINTY": "PRINTY",

    "TẸ̀RA": "PRINTRA",
    "TERA": "PRINTRA",
    "PRINTRA": "PRINTRA",

    "TẸ̀RD": "PRINTRD",
    "TERD": "PRINTRD",
    "PRINTRD": "PRINTRD",

    "TẸ̀R0": "PRINTR0",
    "TER0": "PRINTR0",
    "PRINTR0": "PRINTR0",

    "TẸ̀T": "PRINTT",
    "TET": "PRINTT",
    "PRINTT": "PRINTT",

    "TẸ̀OP": "PRINTOP",
    "TEOP": "PRINTOP",
    "PRINTOP": "PRINTOP",

    "TẸ̀IPÒ": "PRINTSTATUS",
    "TEIPO": "PRINTSTATUS",
    "PRINTSTATUS": "PRINTSTATUS",

    # Direct V4 assembly aliases
    "LOADA": "LDAI",
    "LOADB": "LDBI",
    "ADDR": "LDADDR",
}


NUMBER_WORDS = {
    "ODO": 0,
    "ÒDO": 0,

    "KAN": 1,
    "Ọ̀KAN": 1,

    "MEJI": 2,
    "MÉJÌ": 2,

    "META": 3,
    "MẸ́TA": 3,

    "MERIN": 4,
    "MẸ́RIN": 4,

    "MARUN": 5,
    "MÁRÙN-ÚN": 5,
    "MÁRÙN": 5,

    "MEFA": 6,
    "MẸ́FÀ": 6,

    "MEJE": 7,
    "MÉJE": 7,

    "MEJO": 8,
    "MẸ́JỌ": 8,

    "MESAN": 9,
    "MẸ́SÀN-ÁN": 9,
    "MẸ́SÀN": 9,

    "MEWA": 10,
    "MẸ́WÀÁ": 10,
}


NATIVE_OPERATIONS = {
    "PAPO",
    "YO",
    "DAGBA",
    "PIN",
    "KU",
    "GBE",
    "SEDA",
    "JU",
    "KERE",
}


PASSTHROUGH_INSTRUCTIONS = {
    "LDAI",
    "LDBI",
    "LDADDR",

    "BR_EQ",
    "BR_GT",
    "BR_LT",
    "JMP",

    "NOP",
    "HALT",

    "PRINTY",
    "PRINTRA",
    "PRINTRD",
    "PRINTR0",
    "PRINTT",
    "PRINTOP",
    "PRINTSTATUS",
}


def normalize(word: str) -> str:
    token = word.strip().upper()
    return ALIASES.get(token, token)


def parse_value(token: str) -> int:
    normalized = normalize(token)

    if normalized in NUMBER_WORDS:
        return NUMBER_WORDS[normalized] & 0xFF

    try:
        value = int(token, 0)
    except ValueError as error:
        raise ValueError(
            f"Unknown V4 numeric value: {token}"
        ) from error

    if not 0 <= value <= 0xFF:
        raise ValueError(
            f"V4 value outside 8-bit range: {token}"
        )

    return value


def compile_binary(
    operation: str,
    operand_a: str,
    operand_b: str,
) -> list[str]:
    if operation not in NATIVE_OPERATIONS:
        raise ValueError(
            f"Unknown V4 native operation: {operation}"
        )

    a = parse_value(operand_a)
    b = parse_value(operand_b)

    return [
        f"LDAI 0x{a:02X}\n",
        f"LDBI 0x{b:02X}\n",
        f"{operation}\n",
    ]


def compile_line(line: str) -> list[str]:
    stripped = line.strip()

    if not stripped:
        return ["\n"]

    if stripped.startswith(";"):
        return [line if line.endswith("\n") else line + "\n"]

    # Preserve labels while translating the instruction after the label.
    label = None
    instruction_text = stripped

    if ":" in stripped:
        possible_label, remainder = stripped.split(":", 1)

        if possible_label.strip():
            label = possible_label.strip()
            instruction_text = remainder.strip()

        if not instruction_text:
            return [f"{label}:\n"]

    parts = instruction_text.split()

    if not parts:
        return [line if line.endswith("\n") else line + "\n"]

    normalized = [normalize(part) for part in parts]
    mnemonic = normalized[0]

    if mnemonic == "BERE":
        return []

    if (
        len(normalized) == 4
        and normalized[2] == "ATI"
        and mnemonic in NATIVE_OPERATIONS
    ):
        generated = compile_binary(
            mnemonic,
            parts[1],
            parts[3],
        )

        if label is not None:
            generated[0] = f"{label}: {generated[0]}"

        return generated

    if mnemonic in NATIVE_OPERATIONS:
        if len(normalized) != 1:
            raise ValueError(
                f"{mnemonic} syntax: "
                f"{mnemonic} <A> ATI <B>, "
                f"or load A/B before {mnemonic}"
            )

        output = f"{mnemonic}\n"

    elif mnemonic in PASSTHROUGH_INSTRUCTIONS:
        output_parts = [mnemonic] + parts[1:]
        output = " ".join(output_parts) + "\n"

    else:
        raise ValueError(
            f"Unknown V4 Yorùbá instruction: {parts[0]}"
        )

    if label is not None:
        output = f"{label}: {output}"

    return [output]


def compile_file(
    source_path: Path,
    output_path: Path,
) -> None:
    output_lines: list[str] = []

    for line_number, line in enumerate(
        source_path.read_text(
            encoding="utf-8",
        ).splitlines(keepends=True),
        start=1,
    ):
        try:
            output_lines.extend(
                compile_line(line)
            )
        except ValueError as error:
            raise ValueError(
                f"{source_path}:{line_number}: {error}\n"
                f"    {line.rstrip()}"
            ) from error

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        "".join(output_lines),
        encoding="utf-8",
    )


def main() -> None:
    if len(sys.argv) != 3:
        print(
            "Usage: python3 "
            "tools/ifa_yoruba_frontend_v4.py "
            "<input.ifa4y> <output.ifa4>"
        )
        raise SystemExit(1)

    source_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    try:
        compile_file(
            source_path,
            output_path,
        )
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)

    print(
        f"Compiled V4 Yorùbá source "
        f"-> {output_path}"
    )


if __name__ == "__main__":
    main()
