#!/usr/bin/env python3

from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
APPS_DIR = PROJECT_ROOT / "apps_v4"
IFA4_LAUNCHER = PROJECT_ROOT / "ifa4"


ALIASES = {
    "TAN": "TAN",
    "OPEN": "TAN",

    "YARA": "YARA",
    "YÀRÁ": "YARA",

    "APPS": "APPS",
    "APPLICATIONS": "APPS",
    "ETO": "APPS",
    "ÈTÒ": "APPS",

    "LOAD": "LOAD",
    "GBA": "LOAD",

    "RUN": "RUN",
    "SE": "RUN",
    "ṢE": "RUN",

    "STATUS": "STATUS",
    "IPO": "STATUS",
    "IPÒ": "STATUS",

    "HELP": "HELP",
    "IRANLOWO": "HELP",
    "ÌRÀNLỌ́WỌ́": "HELP",

    "QUIT": "QUIT",
    "EXIT": "QUIT",
    "DA": "QUIT",
    "DÁ": "QUIT",
}


def normalize(token: str) -> str:
    upper = token.strip().upper()
    return ALIASES.get(upper, upper)


def print_banner() -> None:
    print()
    print("============================================================")
    print("                 OHÙN IFÁ V4 INTERFACE")
    print("============================================================")
    print("ONÍLẸ̀ kernel: READY")
    print("Babaláwo mode: OFF")
    print("Active YÀRÁ: 0")
    print()
    print("Enter TAN to begin.")
    print("Enter HELP to see available commands.")
    print()


def print_help() -> None:
    print()
    print("Commands")
    print("--------")
    print("TAN")
    print("    Enable the Babaláwo application environment.")
    print()
    print("YARA <id>")
    print("    Select the YÀRÁ used to execute applications.")
    print()
    print("APPS")
    print("    List applications in apps_v4/.")
    print()
    print("LOAD <application>")
    print("    Load an .ifa4 or .ifa4y application.")
    print()
    print("RUN")
    print("    Execute the currently loaded application.")
    print()
    print("STATUS")
    print("    Show the current shell state.")
    print()
    print("QUIT")
    print("    Close the OHÙN IFÁ interface.")
    print()


def discover_apps() -> dict[str, Path]:
    APPS_DIR.mkdir(parents=True, exist_ok=True)

    applications: dict[str, Path] = {}

    for path in sorted(APPS_DIR.iterdir()):
        if not path.is_file():
            continue

        if path.suffix not in {".ifa4", ".ifa4y"}:
            continue

        applications[path.stem.lower()] = path

    return applications


def print_apps() -> None:
    applications = discover_apps()

    print()
    print("AVAILABLE IFÁ V4 APPLICATIONS")
    print("-----------------------------")

    if not applications:
        print("No applications found in apps_v4/.")
        print()
        return

    for name, path in applications.items():
        application_type = (
            "Yorùbá source"
            if path.suffix == ".ifa4y"
            else "V4 assembly"
        )

        print(f"{name:<24} {application_type}")

    print()


def resolve_application(name: str) -> Path | None:
    candidate = Path(name)

    if candidate.is_file():
        return candidate.resolve()

    project_candidate = PROJECT_ROOT / candidate

    if project_candidate.is_file():
        return project_candidate.resolve()

    applications = discover_apps()
    normalized_name = candidate.stem.lower()

    return applications.get(normalized_name)


def run_application(path: Path, yara_id: int) -> int:
    print()
    print("============================================================")
    print(f"APPLICATION: {path.stem}")
    print(f"YÀRÁ:       {yara_id}")
    print("============================================================")
    print()

    result = subprocess.run(
        [
            str(IFA4_LAUNCHER),
            str(path),
            "--yara",
            str(yara_id),
        ],
        cwd=PROJECT_ROOT,
    )

    print()
    print("============================================================")

    if result.returncode == 0:
        print(f"APPLICATION COMPLETE: {path.stem}")
    else:
        print(
            f"APPLICATION FAILED: {path.stem} "
            f"(exit={result.returncode})"
        )

    print("============================================================")
    print()

    return result.returncode


def main() -> None:
    babalawo_enabled = False
    active_yara = 0
    loaded_application: Path | None = None

    print_banner()

    while True:
        try:
            raw_command = input(
                f"OHÙN[V4:YÀRÁ-{active_yara}]> "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print("DÁ — OHÙN IFÁ closed.")
            return

        if not raw_command:
            continue

        try:
            parts = shlex.split(raw_command)
        except ValueError as error:
            print(f"ERROR: {error}")
            continue

        command = normalize(parts[0])
        arguments = parts[1:]

        if command == "HELP":
            print_help()
            continue

        if command == "QUIT":
            print("DÁ — OHÙN IFÁ closed.")
            return

        if command == "TAN":
            if arguments:
                print("ERROR: TAN takes no arguments.")
                continue

            babalawo_enabled = True
            print("OK BABALÁWO TAN")
            print("OHÙN IFÁ V4 is open.")
            continue

        if command == "STATUS":
            print()
            print("OHÙN IFÁ V4 STATUS")
            print("------------------")
            print(
                "Babaláwo: "
                + ("TAN" if babalawo_enabled else "PA")
            )
            print(f"Active YÀRÁ: {active_yara}")
            print(
                "Loaded application: "
                + (
                    loaded_application.name
                    if loaded_application
                    else "NONE"
                )
            )
            print()
            continue

        if not babalawo_enabled:
            print("DENY: Enter TAN before managing applications.")
            continue

        if command == "YARA":
            if len(arguments) != 1:
                print("ERROR: YARA requires one ID.")
                continue

            try:
                requested_yara = int(arguments[0], 0)
            except ValueError:
                print("ERROR: YÀRÁ ID must be an integer.")
                continue

            if not 0 <= requested_yara <= 15:
                print("ERROR: YÀRÁ ID must be between 0 and 15.")
                continue

            active_yara = requested_yara
            print(f"OK YÀRÁ {active_yara} SELECTED")
            continue

        if command == "APPS":
            if arguments:
                print("ERROR: APPS takes no arguments.")
                continue

            print_apps()
            continue

        if command == "LOAD":
            if len(arguments) != 1:
                print("ERROR: LOAD requires one application name.")
                continue

            selected = resolve_application(arguments[0])

            if selected is None:
                print(
                    "ERROR: Application not found. "
                    "Enter APPS to list applications."
                )
                continue

            if selected.suffix not in {".ifa4", ".ifa4y"}:
                print(
                    "ERROR: Application must end in "
                    ".ifa4 or .ifa4y."
                )
                continue

            loaded_application = selected
            print(
                f"OK APPLICATION LOADED: "
                f"{loaded_application.name}"
            )
            continue

        if command == "RUN":
            if arguments:
                print("ERROR: RUN takes no arguments.")
                continue

            if loaded_application is None:
                print("ERROR: No application loaded.")
                continue

            run_application(
                loaded_application,
                active_yara,
            )
            continue

        print(f"ERROR UNKNOWN_COMMAND {parts[0]}")


if __name__ == "__main__":
    main()
