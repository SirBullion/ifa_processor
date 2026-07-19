#!/usr/bin/env python3

from __future__ import annotations

import csv
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRIDGE = PROJECT_ROOT / "sim/v4/ifa_v4_os_bridge.out"
CSV_PATH = PROJECT_ROOT / "analysis/v4_cpu_vs_ifa_native.csv"


@dataclass(frozen=True)
class TestCase:
    operation: str
    a: int
    b: int


TESTS = [
    TestCase("PAPO", 2, 6),
    TestCase("PAPO", 13, 7),

    TestCase("YO", 12, 4),
    TestCase("YO", 4, 12),

    TestCase("DAGBA", 7, 5),
    TestCase("DAGBA", 20, 20),

    TestCase("PIN", 13, 7),
    TestCase("PIN", 12, 4),

    TestCase("KU", 13, 7),
    TestCase("KU", 12, 5),

    TestCase("GBE", 2, 7),
    TestCase("GBE", 3, 5),

    TestCase("SEDA", 5, 5),
    TestCase("SEDA", 5, 7),

    TestCase("JU", 9, 4),
    TestCase("JU", 3, 8),

    TestCase("KERE", 3, 8),
    TestCase("KERE", 9, 4),
]


EXEC_PATTERN = re.compile(
    r"EXEC ID=(?P<yara>\d+) "
    r"OP=(?P<op>[0-9a-fA-F]+) "
    r"HIT=(?P<hit>\d+) "
    r"MISS=(?P<miss>\d+) "
    r"Y=(?P<y>[0-9a-fA-F]{2}) "
    r"RA=(?P<ra>[0-9a-fA-F]{2}) "
    r"RD=(?P<rd>[0-9a-fA-F]{2}) "
    r"R0=(?P<r0>[0-9a-fA-F]{2}) "
    r"T=(?P<t>[0-9a-fA-F]{2}) "
    r"VALID=(?P<valid>\d+) "
    r"EXC=(?P<exc>\d+) "
    r"EXC_CODE=(?P<exc_code>[0-9a-fA-F]+) "
    r"STATE=(?P<state>\d+) "
    r"STATE_CODE=(?P<state_code>[0-9a-fA-F]+) "
    r"EQ=(?P<eq>\d+) "
    r"GT=(?P<gt>\d+) "
    r"LT=(?P<lt>\d+)"
)


def cpu_reference(
    operation: str,
    a: int,
    b: int,
) -> dict[str, int]:
    if operation == "PAPO":
        full = a + b
        return {
            "y": full & 0xFF,
            "t": (full >> 8) & 0xFF,
            "eq": 0,
            "gt": 0,
            "lt": 0,
        }

    if operation == "YO":
        return {
            "y": (a - b) & 0xFF,
            "t": 1 if a < b else 0,
            "eq": 0,
            "gt": 0,
            "lt": 0,
        }

    if operation == "DAGBA":
        full = a * b
        return {
            "y": full & 0xFF,
            "t": (full >> 8) & 0xFF,
            "eq": 0,
            "gt": 0,
            "lt": 0,
        }

    if operation == "PIN":
        if b == 0:
            return {
                "y": 0,
                "t": 0xFF,
                "eq": 0,
                "gt": 0,
                "lt": 0,
            }

        return {
            "y": a // b,
            "t": a % b,
            "eq": 0,
            "gt": 0,
            "lt": 0,
        }

    if operation == "KU":
        if b == 0:
            return {
                "y": 0,
                "t": 0xFF,
                "eq": 0,
                "gt": 0,
                "lt": 0,
            }

        return {
            "y": a % b,
            "t": a // b,
            "eq": 0,
            "gt": 0,
            "lt": 0,
        }

    if operation == "GBE":
        full = pow(a, b)

        return {
            "y": full & 0xFF,
            "t": (full >> 8) & 0xFF,
            "eq": 0,
            "gt": 0,
            "lt": 0,
        }

    if operation == "SEDA":
        return {
            "y": (a - b) & 0xFF,
            "t": int(a < b),
            "eq": int(a == b),
            "gt": int(a > b),
            "lt": int(a < b),
        }

    if operation == "JU":
        return {
            "y": int(a > b),
            "t": int(a < b),
            "eq": int(a == b),
            "gt": int(a > b),
            "lt": int(a < b),
        }

    if operation == "KERE":
        return {
            "y": int(a < b),
            "t": int(a < b),
            "eq": int(a == b),
            "gt": int(a > b),
            "lt": int(a < b),
        }

    raise ValueError(f"Unknown operation: {operation}")


def run_ifa(test: TestCase) -> dict[str, int]:
    commands = "\n".join([
        "BABALAWO ON",
        "CREATE 0",
        "SELECT 0",
        f"EXEC {test.operation} {test.a:02x} {test.b:02x}",
        "QUIT",
        "",
    ])

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".txt",
        encoding="utf-8",
        delete=False,
    ) as handle:
        handle.write(commands)
        command_path = Path(handle.name)

    try:
        result = subprocess.run(
            [
                "vvp",
                str(BRIDGE),
                f"+CMD_FILE={command_path}",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        command_path.unlink(missing_ok=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"Bridge failed for {test}:\n"
            f"{result.stdout}\n{result.stderr}"
        )

    for line in result.stdout.splitlines():
        match = EXEC_PATTERN.fullmatch(line.strip())

        if match is None:
            continue

        values: dict[str, int] = {}

        for key, raw_value in match.groupdict().items():
            base = 16 if key in {
                "op",
                "y",
                "ra",
                "rd",
                "r0",
                "t",
                "exc_code",
                "state_code",
            } else 10

            values[key] = int(raw_value, base)

        return values

    raise RuntimeError(
        f"No EXEC result found for {test}:\n{result.stdout}"
    )


def main() -> None:
    if not BRIDGE.exists():
        raise SystemExit(
            f"Bridge not found: {BRIDGE}\n"
            "Run make test-v4 first."
        )

    rows: list[dict[str, object]] = []
    pass_count = 0

    print()
    print("=" * 104)
    print("CPU REFERENCE VS IFÁ PROCESSOR V4 — NATIVE OPERATION COMPARISON")
    print("=" * 104)
    print(
        f"{'OP':<8} {'A':>4} {'B':>4} "
        f"{'CPU Y':>7} {'IFÁ Y':>7} "
        f"{'CPU T':>7} {'IFÁ T':>7} "
        f"{'FLAGS':>11} {'RESULT':>9}"
    )
    print("-" * 104)

    for test in TESTS:
        cpu = cpu_reference(
            test.operation,
            test.a,
            test.b,
        )
        ifa = run_ifa(test)

        scalar_match = (
            cpu["y"] == ifa["y"]
            and cpu["t"] == ifa["t"]
        )

        flag_match = (
            cpu["eq"] == ifa["eq"]
            and cpu["gt"] == ifa["gt"]
            and cpu["lt"] == ifa["lt"]
        )

        passed = scalar_match and flag_match

        if passed:
            pass_count += 1

        flag_text = (
            f"{ifa['eq']}{ifa['gt']}{ifa['lt']}"
        )

        print(
            f"{test.operation:<8} "
            f"{test.a:>4} {test.b:>4} "
            f"{cpu['y']:>7} {ifa['y']:>7} "
            f"{cpu['t']:>7} {ifa['t']:>7} "
            f"{flag_text:>11} "
            f"{'PASS' if passed else 'CHECK':>9}"
        )

        rows.append({
            "operation": test.operation,
            "a": test.a,
            "b": test.b,

            "cpu_y": cpu["y"],
            "ifa_y": ifa["y"],

            "cpu_t": cpu["t"],
            "ifa_t": ifa["t"],

            "cpu_eq": cpu["eq"],
            "ifa_eq": ifa["eq"],

            "cpu_gt": cpu["gt"],
            "ifa_gt": ifa["gt"],

            "cpu_lt": cpu["lt"],
            "ifa_lt": ifa["lt"],

            "ifa_ra": ifa["ra"],
            "ifa_rd": ifa["rd"],
            "ifa_r0": ifa["r0"],

            "ifa_valid": ifa["valid"],
            "ifa_exception": ifa["exc"],
            "ifa_exception_code": ifa["exc_code"],
            "ifa_state": ifa["state"],
            "ifa_state_code": ifa["state_code"],

            "scalar_match": scalar_match,
            "flag_match": flag_match,
            "passed": passed,
        })

    CSV_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with CSV_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)

    print("-" * 104)
    print(
        f"PASS: {pass_count}/{len(TESTS)} "
        "CPU scalar/predicate comparisons"
    )
    print(f"CSV: {CSV_PATH}")
    print()
    print("IFÁ additional outputs recorded:")
    print("    RA, RD, R0, VALID, EXC, EXC_CODE, STATE, STATE_CODE")
    print("=" * 104)

    if pass_count != len(TESTS):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
