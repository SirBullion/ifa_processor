#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path


BRIDGE_BINARY = Path("sim/v4/ifa_v4_os_bridge.out")


def read_program(hex_path: Path) -> list[int]:
    program = []

    for line_number, raw_line in enumerate(
        hex_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.split(";", 1)[0].strip()

        if not line:
            continue

        try:
            instruction = int(line, 16)
        except ValueError as error:
            raise ValueError(
                f"{hex_path}:{line_number}: "
                f"invalid instruction {line!r}"
            ) from error

        if not 0 <= instruction <= 0xFFFF:
            raise ValueError(
                f"{hex_path}:{line_number}: "
                "instruction exceeds 16 bits"
            )

        program.append(instruction)

    if not program:
        raise ValueError(
            f"No instructions found in {hex_path}"
        )

    if len(program) > 256:
        raise ValueError(
            "V4 program exceeds 256 instructions"
        )

    return program


def build_commands(
    program: list[int],
    yara_id: int,
) -> list[str]:
    commands = [
        "BABALAWO ON",
        f"CREATE {yara_id}",
        f"SELECT {yara_id}",
        "CONTEXT 00 0000 00 00 00 00 00",
    ]

    for address, instruction in enumerate(program):
        commands.append(
            f"LOAD {address:02x} {instruction:04x}"
        )

    commands.extend([
        "RUN",
        "QUIT",
    ])

    return commands


def run_program(
    hex_path: Path,
    yara_id: int,
) -> int:
    if not BRIDGE_BINARY.exists():
        print(
            f"ERROR: bridge binary not found: "
            f"{BRIDGE_BINARY}",
            file=sys.stderr,
        )
        return 1

    program = read_program(hex_path)
    commands = build_commands(program, yara_id)

    command_text = "\n".join(commands) + "\n"

    result = subprocess.run(
        [
            "vvp",
            str(BRIDGE_BINARY),
            "+INTERACTIVE",
        ],
        input=command_text,
        capture_output=True,
        text=True,
    )

    print(result.stdout, end="")

    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    if result.returncode != 0:
        return result.returncode

    if "FAULT RUN" in result.stdout:
        return 1

    if "OK RUN " not in result.stdout:
        print(
            "ERROR: bridge returned no OK RUN result",
            file=sys.stderr,
        )
        return 1

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Load and execute an IFÁ V4 hexadecimal program "
            "through the ONÍLẸ̀ OS bridge."
        )
    )

    parser.add_argument(
        "hex_program",
        type=Path,
        help="V4 hexadecimal program file",
    )

    parser.add_argument(
        "--yara",
        type=int,
        default=0,
        help="YÀRÁ context ID, default 0",
    )

    args = parser.parse_args()

    if not 0 <= args.yara <= 15:
        parser.error("--yara must be between 0 and 15")

    try:
        return_code = run_program(
            args.hex_program,
            args.yara,
        )
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return_code = 1

    raise SystemExit(return_code)


if __name__ == "__main__":
    main()
