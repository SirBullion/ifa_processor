#!/usr/bin/env python3

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs" / "v4"

JSON_PATH = DOCS / "ifa_v4_isa.json"
MD_PATH = DOCS / "IFA_V4_ISA.md"

INSTRUCTIONS = [
    ("BR_EQ", "0x01TT", "Branch to TT when EQ=1"),
    ("BR_GT", "0x02TT", "Branch to TT when GT=1"),
    ("BR_LT", "0x03TT", "Branch to TT when LT=1"),
    ("JMP", "0x04TT", "Jump unconditionally to TT"),

    ("LDAI", "0x10II", "Load immediate II into A"),
    ("LDBI", "0x20II", "Load immediate II into B"),
    ("LDADDR", "0x30II", "Load immediate II into ADDR"),

    ("PAPO", "0x8000", "Native add, OP=0"),
    ("YO", "0x8100", "Native subtract, OP=1"),
    ("DAGBA", "0x8200", "Native multiply, OP=2"),
    ("PIN", "0x8300", "Native divide, OP=3"),
    ("KU", "0x8400", "Native modulo, OP=4"),
    ("GBE", "0x8500", "Native GBÉ operation, OP=5"),
    ("SEDA", "0x8600", "Native compare, OP=6"),
    ("JU", "0x8700", "Native greater-than predicate, OP=7"),
    ("KERE", "0x8800", "Native less-than predicate, OP=8"),

    ("NOP", "0xF000", "No operation"),
    ("HALT", "0xF100", "Halt program execution"),
    ("PRINTY", "0xF200", "Print relation-frame Y"),
    ("PRINTRA", "0xF300", "Print relation-frame RA"),
    ("PRINTRD", "0xF400", "Print relation-frame RD"),
    ("PRINTR0", "0xF500", "Print relation-frame R0"),
    ("PRINTT", "0xF600", "Print relation-frame T"),
    ("PRINTOP", "0xF700", "Print native OP"),
    ("PRINTSTATUS", "0xF800", "Print packed latest-operation status"),

    (
        "RPUSH",
        "0xF900",
        "Preserve the complete IFÁ relation frame in the active YÀRÁ relation stack",
    ),
    (
        "RPOP",
        "0xFA00",
        "Restore the most recently preserved IFÁ relation through ONÍLẸ̀ administrative import",
    ),
    (
        "CALL",
        "0xFBtt",
        "Preserve the relation and return continuation, then transfer execution to 8-bit target tt",
    ),
    (
        "RET",
        "0xFC00",
        "Restore the preserved relation and resume at its saved return continuation",
    ),
]

def build_json():
    return {
        "architecture": {
            "name": "IFÁ Processor V4",
            "instruction_width_bits": 16,
            "data_width_bits": 8,
            "program_address_width_bits": 8,
            "maximum_program_instructions": 256,
            "maximum_yara": 16,
        },
        "instruction_format": {
            "major_opcode": "IR[15:12]",
            "subopcode": "IR[11:8]",
            "immediate_or_target": "IR[7:0]",
        },
        "relation_frame": {
            "definition": "Ψ = {Y, RA, RD, R0, T}",
            "fields": ["Y", "RA", "RD", "R0", "T"],
        },
        "rmu_key": {
            "definition": "K = {OP, RA, RD, T}",
            "fields": ["OP", "RA", "RD", "T"],
        },
        "instructions": [
            {
                "mnemonic": m,
                "encoding": e,
                "semantics": s,
            }
            for m, e, s in INSTRUCTIONS
        ],
    }


def build_markdown(isa):
    lines = [
        "# IFÁ Processor V4 — Canonical ISA",
        "",
        "## Instructions",
        "",
        "| Encoding | Mnemonic | Semantics |",
        "|---|---|---|",
    ]

    for ins in isa["instructions"]:
        lines.append(
            f"| `{ins['encoding']}` | "
            f"`{ins['mnemonic']}` | "
            f"{ins['semantics']} |"
        )

    lines.extend([
        "",
        "## Relation frame",
        "",
        "```text",
        "Ψ = {Y, RA, RD, R0, T}",
        "```",
        "",
        "## RMU key",
        "",
        "```text",
        "K = {OP, RA, RD, T}",
        "```",
    ])

    return "\n".join(lines)


def main():
    DOCS.mkdir(parents=True, exist_ok=True)

    isa = build_json()

    JSON_PATH.write_text(
        json.dumps(isa, indent=2),
        encoding="utf-8",
    )

    MD_PATH.write_text(
        build_markdown(isa),
        encoding="utf-8",
    )

    print("Generated:", JSON_PATH)
    print("Generated:", MD_PATH)
    print("Instruction count:", len(isa["instructions"]))


if __name__ == "__main__":
    main()
