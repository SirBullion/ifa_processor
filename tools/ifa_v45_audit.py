#!/usr/bin/env python3
"""Run any IFÁ v4.5 hardware program with RMU/cycle audit and waveform."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
AUDIT_DIR = ROOT / "build" / "v45" / "audits"
RUN_RE = re.compile(
    r"CYCLES=(?P<cycles>\d+).*RMU_HITS=(?P<hits>\d+) "
    r"RMU_MISSES=(?P<misses>\d+)"
)


def run_checked(command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    print("$ " + " ".join(command), flush=True)
    return subprocess.run(command, cwd=ROOT, text=True, check=True, **kwargs)


def program_image(program: Path) -> tuple[Path, str]:
    source = program.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    name = source.stem
    if source.suffix.lower() == ".ifa45":
        prefix = AUDIT_DIR / name
        run_checked([sys.executable, "tools/ifaasm_v45.py", str(source), str(prefix)])
        return prefix.with_suffix(".hex"), name
    if source.suffix.lower() == ".hex":
        return source, name
    raise ValueError("hardware audit accepts .ifa45 source or .hex image")


def bridge_input(image: Path) -> str:
    commands = [
        "BABALAWO ON",
        "CREATE 0",
        "SELECT 0",
        "CONTEXT 00 0000 00 00 00 00 00",
    ]
    for address, word in enumerate(image.read_text(encoding="utf-8").splitlines()):
        word = word.strip()
        if word:
            commands.append(f"LOAD {address:02x} {word}")
    commands.extend(("RUN", "QUIT"))
    return "\n".join(commands) + "\n"


def audit(program: Path, open_wave: bool) -> int:
    image, name = program_image(program)
    run_checked(["make", "v45-build"])

    vcd = AUDIT_DIR / f"{name}.vcd"
    fst = AUDIT_DIR / f"{name}.fst"
    log = AUDIT_DIR / f"{name}.log"
    result = run_checked(
        ["vvp", "sim/v45/ifa_v45_os_bridge.out", "+INTERACTIVE", f"+VCD={vcd}"],
        input=bridge_input(image), capture_output=True,
    )
    log.write_text(result.stdout, encoding="utf-8")

    prints = sum(line.startswith("PRINT ") for line in result.stdout.splitlines())
    run_line = next((line for line in result.stdout.splitlines() if line.startswith("OK RUN")), "")
    fault_line = next((line for line in result.stdout.splitlines() if line.startswith("FAULT")), "")
    if fault_line:
        print(fault_line)
        print(f"AUDIT_LOG={log}")
        return 1
    match = RUN_RE.search(run_line)
    if match is None:
        print("KÒ WỌLÉ: no completed RUN audit record")
        print(f"AUDIT_LOG={log}")
        return 1

    cycles = int(match.group("cycles"))
    hits = int(match.group("hits"))
    misses = int(match.group("misses"))
    accesses = hits + misses
    hit_rate = 100.0 * hits / accesses if accesses else 0.0

    print(run_line)
    print("=" * 64)
    print(f"IFÁ V4.5 AUDIT: {program}")
    print(f"CYCLES={cycles}")
    print(f"RMU_HITS={hits}")
    print(f"RMU_MISSES={misses}")
    print(f"RMU_ACCESSES={accesses}")
    print(f"RMU_HIT_RATE={hit_rate:.2f}%")
    print(f"PRINT_EVENTS={prints}")
    print(f"AUDIT_LOG={log}")

    converter = shutil.which("vcd2fst")
    if converter:
        run_checked([converter, str(vcd), str(fst)])
        print(f"WAVEFORM={fst}")
        wave = fst
    else:
        print("WARNING: vcd2fst not found; retaining VCD")
        print(f"WAVEFORM={vcd}")
        wave = vcd
    print("=" * 64)

    if open_wave:
        viewer = shutil.which("gtkwave")
        if viewer:
            subprocess.Popen([viewer, str(wave)], cwd=ROOT)
        else:
            print("WARNING: GTKWave not found")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit an IFÁ v4.5 program in RTL")
    parser.add_argument("program", type=Path, help=".ifa45 source or .hex image")
    parser.add_argument("--open-wave", action="store_true", help="open the generated trace in GTKWave")
    arguments = parser.parse_args()
    try:
        return audit(arguments.program, arguments.open_wave)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"KÒ WỌLÉ: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
