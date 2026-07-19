#!/usr/bin/env python3

from __future__ import annotations

import queue
import re
import shlex
import subprocess
import sys
import threading
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRIDGE = PROJECT_ROOT / "sim/v4/ifa_v4_os_bridge.out"
ASSEMBLER = PROJECT_ROOT / "tools/ifaasm_v4.py"
YORUBA_FRONTEND = PROJECT_ROOT / "tools/ifa_yoruba_frontend_v4.py"
APPS_DIR = PROJECT_ROOT / "apps_v4"
WORK_DIR = PROJECT_ROOT / "programs_v4"

MAX_YARA = 16


NATIVE_OPERATIONS = {
    "PAPO": 0x0,
    "PÀPỌ̀": 0x0,

    "YO": 0x1,
    "YỌ": 0x1,

    "DAGBA": 0x2,
    "DÁGBA": 0x2,

    "PIN": 0x3,
    "PÍN": 0x3,

    "KU": 0x4,
    "KÙ": 0x4,

    "GBE": 0x5,
    "GBÉ": 0x5,

    "SEDA": 0x6,
    "ṢẸ̀DÁ": 0x6,

    "JU": 0x7,
    "JÙ": 0x7,

    "KERE": 0x8,
    "KERÉ": 0x8,
}


SYMBOLIC_OPERATIONS = {
    "+": "PAPO",
    "-": "YO",
    "*": "DAGBA",
    "/": "PIN",
    "%": "KU",
    "^": "GBE",
    "==": "SEDA",
    ">": "JU",
    "<": "KERE",
}


COMMAND_ALIASES = {
    # Privilege
    "TAN": "BABALAWO_ON",
    "OPEN": "BABALAWO_ON",
    "PA": "BABALAWO_OFF",
    "CLOSE": "BABALAWO_OFF",

    # YÀRÁ lifecycle
    "YARA": "SELECT",
    "YÀRÁ": "SELECT",
    "WO": "SELECT",
    "WỌ": "SELECT",

    "SEDA_YARA": "CREATE",
    "ṢẸ̀DÁ_YÀRÁ": "CREATE",

    "DURO": "PAUSE",
    "DÚRÓ": "PAUSE",

    "TESIWAJU": "RESUME",
    "TẸ̀SÍWÁJÚ": "RESUME",

    "PARE": "DESTROY",
    "PAARẸ": "DESTROY",

    # Inspection
    "IPO": "STATUS",
    "IPÒ": "STATUS",

    # Human interpretation of the latest relation
    "OYELA": "OYELA",
    "OYÈLÁ": "OYELA",
    "OYELAA": "OYELAA",

    # Program execution
    "SE": "RUN",
    "ṢE": "RUN",

    # Shell
    "IRANLOWO": "HELP",
    "ÌRÀNLỌ́WỌ́": "HELP",
    "DA": "QUIT",
    "DÁ": "QUIT",
    "EXIT": "QUIT",
}


RAW_BRIDGE_COMMANDS = {
    "BABALAWO",
    "CREATE",
    "SELECT",
    "PAUSE",
    "RESUME",
    "DESTROY",

    "STACKWRITE",
    "STACKREAD",

    "CONTEXT",

    "RUN",
    "STEP",
    "STOP",
    "LOAD",
    "EXEC",

    "GRANT",
    "REVOKE",
    "SHARE",

    "MEMWRITE",
    "MEMREAD",
    "MEMGRANTR",
    "MEMGRANTW",
    "MEMREVOKER",
    "MEMREVOKEW",

    "STATUS",
    "QUIT",
}


class BridgeSession:
    def __init__(self) -> None:
        if not BRIDGE.exists():
            raise FileNotFoundError(
                f"V4 bridge not found: {BRIDGE}\n"
                "Run make test-v4 to rebuild it."
            )

        self.process = subprocess.Popen(
            [
                "vvp",
                str(BRIDGE),
                "+INTERACTIVE",
            ],
            cwd=PROJECT_ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        if self.process.stdin is None or self.process.stdout is None:
            raise RuntimeError("Could not open bridge pipes.")

        self.output_queue: queue.Queue[str] = queue.Queue()
        self.last_lines: list[str] = []

        # UI-only metadata for human rendering.
        # This does not modify the locked V4 hardware frame.
        self.last_operation_name: str | None = None
        self.last_operand_a: int | None = None
        self.last_operand_b: int | None = None

        self.reader = threading.Thread(
            target=self._read_output,
            daemon=True,
        )
        self.reader.start()

        self.collect_output(
            first_timeout=2.0,
            idle_timeout=0.15,
        )

    def _read_output(self) -> None:
        assert self.process.stdout is not None

        for line in self.process.stdout:
            self.output_queue.put(line.rstrip("\n"))

    def collect_output(
        self,
        first_timeout: float = 1.0,
        idle_timeout: float = 0.12,
    ) -> list[str]:
        lines: list[str] = []

        try:
            first_line = self.output_queue.get(
                timeout=first_timeout
            )
            lines.append(first_line)
        except queue.Empty:
            return lines

        while True:
            try:
                line = self.output_queue.get(
                    timeout=idle_timeout
                )
                lines.append(line)
            except queue.Empty:
                break

        for line in lines:
            print(line)

        return lines

    def command(
        self,
        command_text: str,
        first_timeout: float = 1.5,
        idle_timeout: float = 0.15,
    ) -> list[str]:
        if self.process.poll() is not None:
            raise RuntimeError(
                "The V4 bridge process has stopped."
            )

        assert self.process.stdin is not None

        self.process.stdin.write(command_text + "\n")
        self.process.stdin.flush()

        lines = self.collect_output(
            first_timeout=first_timeout,
            idle_timeout=idle_timeout,
        )

        self.last_lines = lines
        return lines

    def close(self) -> None:
        if self.process.poll() is not None:
            return

        try:
            self.command("QUIT")
        except (BrokenPipeError, RuntimeError):
            pass

        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.terminate()


def normalize(token: str) -> str:
    upper = token.strip().upper()
    return COMMAND_ALIASES.get(upper, upper)


def parse_byte(token: str) -> int:
    cleaned = token.strip()

    try:
        value = int(cleaned, 0)
    except ValueError:
        try:
            value = int(cleaned, 16)
        except ValueError as error:
            raise ValueError(
                f"Invalid 8-bit value: {token}"
            ) from error

    if not 0 <= value <= 0xFF:
        raise ValueError(
            f"Value outside 8-bit range: {token}"
        )

    return value


def parse_symbolic_expression(
    expression: str,
) -> tuple[str, int, int] | None:
    """
    Parse a direct two-operand IFÁ expression.

    Supported forms include:

        2+6
        12 / 4
        12%5
        2^8
        5==5
        9>4
        3<8

    Operands accept decimal or Python-style hexadecimal values.
    """

    match = re.fullmatch(
        r"""
        \s*
        (0[xX][0-9a-fA-F]+|\d+)
        \s*
        (==|[+\-*/%^<>])
        \s*
        (0[xX][0-9a-fA-F]+|\d+)
        \s*
        """,
        expression,
        flags=re.VERBOSE,
    )

    if match is None:
        return None

    left_text, symbol, right_text = match.groups()

    left = parse_byte(left_text)
    right = parse_byte(right_text)

    operation_name = SYMBOLIC_OPERATIONS[symbol]

    return operation_name, left, right


def execute_symbolic_expression(
    session: BridgeSession,
    expression: str,
) -> bool:
    parsed = parse_symbolic_expression(expression)

    if parsed is None:
        return False

    operation_name, a, b = parsed

    session.last_operation_name = operation_name
    session.last_operand_a = a
    session.last_operand_b = b

    session.command(
        f"EXEC {operation_name} {a:02x} {b:02x}"
    )

    return True


def signed8(value: int) -> int:
    return value - 256 if value >= 128 else value


def parse_latest_relation(
    lines: list[str],
) -> dict[str, int] | None:
    """
    Read the latest V4 EXEC or FRAME output.

    Supported examples:

        EXEC ID=0 OP=3 ... Y=02 RA=04 RD=0b R0=f0 T=01 ...
        FRAME OP=3 Y=02 RA=04 RD=0b R0=f0 T=01 ...
    """

    patterns = [
        re.compile(
            r"\bOP=([0-9a-fA-F]+).*?"
            r"\bY=([0-9a-fA-F]{2}).*?"
            r"\bRA=([0-9a-fA-F]{2}).*?"
            r"\bRD=([0-9a-fA-F]{2}).*?"
            r"\bR0=([0-9a-fA-F]{2}).*?"
            r"\bT=([0-9a-fA-F]{2})"
        ),
    ]

    for line in reversed(lines):
        if "EXEC ID=" not in line and "FRAME OP=" not in line:
            continue

        for pattern in patterns:
            match = pattern.search(line)

            if match is None:
                continue

            op, y, ra, rd, r0, transport = match.groups()

            return {
                "OP": int(op, 16),
                "Y": int(y, 16),
                "RA": int(ra, 16),
                "RD": int(rd, 16),
                "R0": int(r0, 16),
                "T": int(transport, 16),
            }

    return None


OP_NAMES = {
    0x0: "PAPO",
    0x1: "YO",
    0x2: "DAGBA",
    0x3: "PIN",
    0x4: "KU",
    0x5: "GBE",
    0x6: "SEDA",
    0x7: "JU",
    0x8: "KERE",
}


def decimal_rendering(
    session: BridgeSession,
) -> str | None:
    operation = session.last_operation_name
    a = session.last_operand_a
    b = session.last_operand_b

    if operation not in {"PIN", "KU"}:
        return None

    if a is None or b is None or b == 0:
        return None

    value = a / b

    return f"{value:.12f}".rstrip("0").rstrip(".")


def oyela(
    session: BridgeSession,
    english: bool = False,
) -> None:
    frame = parse_latest_relation(session.last_lines)

    if frame is None:
        print("KÒ SÍ ÀBÁJÁDE — no recent IFÁ relation.")
        return

    operation = OP_NAMES.get(
        frame["OP"],
        f"OP-{frame['OP']:X}",
    )

    if english:
        print()
        print("OYELAA — ENGLISH INTERPRETATION")
        print("--------------------------------")
        print(
            f"Operation     : {operation} "
            f"(OP=0x{frame['OP']:X})"
        )
        print(
            f"Result        : {signed8(frame['Y'])} "
            f"(raw 0x{frame['Y']:02X}, "
            f"unsigned {frame['Y']})"
        )

        decimal_value = decimal_rendering(session)

        if decimal_value is not None:
            print(f"Decimal       : {decimal_value}")

            if session.last_operation_name == "PIN":
                print(
                    f"Exact division: "
                    f"{frame['Y']} remainder {frame['T']}"
                )
            elif session.last_operation_name == "KU":
                print(
                    f"Exact division: "
                    f"{frame['T']} remainder {frame['Y']}"
                )

        print()
        print("Relation Frame")
        print("--------------")
        print(f"Agreement     : 0x{frame['RA']:02X}")
        print(f"Disagreement  : 0x{frame['RD']:02X}")
        print(f"Base/Return   : 0x{frame['R0']:02X}")
        print(f"Transport     : 0x{frame['T']:02X}")
        print()
        print(
            "OYELAA reads the latest IFÁ computation "
            "as a human-facing result and relation frame."
        )
        print()
        return

    print()
    print("OYÈLÁ — ÌTÚMỌ̀ ÀBÁJÁDE")
    print("----------------------")
    print(
        f"ÌṢẸ́          : {operation} "
        f"(OP=0x{frame['OP']:X})"
    )
    print(
        f"ÈSÌ / OYÈLÁ  : {signed8(frame['Y'])} "
        f"(0x{frame['Y']:02X})"
    )

    decimal_value = decimal_rendering(session)

    if decimal_value is not None:
        print(f"ÈSÌ DẸ́SÍMÀLÌ : {decimal_value}")

        if session.last_operation_name == "PIN":
            print(
                f"ÌPÍN PÍPÉ    : "
                f"{frame['Y']} pẹ̀lú ìyókù {frame['T']}"
            )
        elif session.last_operation_name == "KU":
            print(
                f"ÌPÍN PÍPÉ    : "
                f"{frame['T']} pẹ̀lú ìyókù {frame['Y']}"
            )

    print()
    print("ÀWÒRÁN ÌBÁṢẸ̀PỌ̀")
    print("----------------")
    print(f"FARAPỌ̀   = 0x{frame['RA']:02X}")
    print(f"YÀTỌ̀     = 0x{frame['RD']:02X}")
    print(f"ÌPÌLẸ̀    = 0x{frame['R0']:02X}")
    print(f"GBÉ       = 0x{frame['T']:02X}")
    print()
    print(
        "OYÈLÁ ń ka ohun tí YÀRÁ ṣe, "
        "ó sì ń túmọ̀ rẹ̀ fún ènìyàn."
    )
    print()


def print_banner() -> None:
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║               OHÙN IFÁ V4 OPERATING SYSTEM                 ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║ ONÍLẸ̀ Kernel     Shared RPC      Local RMU per YÀRÁ        ║")
    print("║ Relation Stack    General Memory  Permission Supervisor     ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print("Enter TAN to enable Babaláwo administration.")
    print("Enter HELP for the complete command list.")
    print()


def print_help() -> None:
    print(
        """
OHÙN IFÁ V4 COMMANDS
====================

Babaláwo privilege
------------------
TAN
    Enable Babaláwo mode.

PA
    Disable Babaláwo mode.

YÀRÁ lifecycle
--------------
CREATE <id>
    Create a YÀRÁ.

SELECT <id>
YARA <id>
WỌ <id>
    Select a YÀRÁ.

ENTER <id>
    Create the YÀRÁ if needed, then select it.

PAUSE <id>
RESUME <id>
DESTROY <id>

Native IFÁ operations
---------------------
PAPO <A> ATI <B>
YO <A> ATI <B>
DAGBA <A> ATI <B>
PIN <A> ATI <B>
KU <A> ATI <B>
GBE <A> ATI <B>
SEDA <A> ATI <B>
JU <A> ATI <B>
KERE <A> ATI <B>

Examples:
    PAPO 13 ATI 6
    PIN 0x0D ATI 0x06

Direct symbolic expressions
---------------------------
+     PAPO    addition
-     YO      subtraction
*     DAGBA   multiplication
/     PIN     quotient; remainder is T
%     KU      remainder; quotient is T
^     GBE     relation exponentiation
==    SEDA    equality/comparison relation
>     JU      greater-than relation
<     KERE    less-than relation

Examples:
    2+6
    12 - 4
    5*7
    13/6
    13%6
    2^8
    5==5
    9>4
    3<8

Programs and applications
-------------------------
APPS
    List files in apps_v4/.

LOADAPP <name>
    Assemble and load an application.

RUNAPP <name>
    Load and execute an application.

LOADPROGRAM <path>
    Assemble and load an .ifa4 or .ifa4y file.

RUN
STEP
STOP

LISTING
    Show the most recently assembled listing.

Context
-------
CONTEXT <PC> <IR> <A> <B> <ADDR> <FLAGS> <SP>

Example:
    CONTEXT 00 0000 00 00 00 00 00

STATUS
IPO
    Show complete ONÍLẸ̀ and active-YÀRÁ status.

OYELA
OYÈLÁ
    Interpret the latest IFÁ result and relation frame in Yorùbá.

OYELAA
    Interpret the latest IFÁ result and relation frame in English.

Relation stack diagnostics
--------------------------
STACKWRITE <byte>
STACKREAD

The V4 ISA also supports:
    RPUSH
    RPOP
    CALL
    RET

These are normally used inside loaded programs.

Relation sharing
----------------
GRANT <source> <destination>
REVOKE <source> <destination>
SHARE <source> <destination>

General memory
--------------
MEMWRITE <address> <data>
MEMREAD <address>

MEMGRANTR <address> <yara>
MEMGRANTW <address> <yara>
MEMREVOKER <address> <yara>
MEMREVOKEW <address> <yara>

Raw bridge access
-----------------
RAW <bridge command>

Example:
    RAW STATUS
    RAW EXEC 0 0d 06

Shell
-----
HISTORY
CLEAR
HELP
QUIT
DÁ
"""
    )


def discover_apps() -> dict[str, Path]:
    APPS_DIR.mkdir(parents=True, exist_ok=True)

    applications: dict[str, Path] = {}

    for path in sorted(APPS_DIR.iterdir()):
        if path.is_file() and path.suffix in {
            ".ifa4",
            ".ifa4y",
        }:
            applications[path.stem.lower()] = path

    return applications


def print_apps() -> None:
    applications = discover_apps()

    print()
    print("AVAILABLE V4 APPLICATIONS")
    print("=========================")

    if not applications:
        print("No applications found in apps_v4/.")
        print()
        return

    for index, (name, path) in enumerate(
        applications.items(),
        start=1,
    ):
        source_type = (
            "OHÙN/Yorùbá"
            if path.suffix == ".ifa4y"
            else "V4 assembly"
        )

        print(
            f"{index:>2}. {name:<26} "
            f"{source_type}"
        )

    print()


def resolve_source(name_or_path: str) -> Path:
    supplied = Path(name_or_path)

    candidates = [
        supplied,
        PROJECT_ROOT / supplied,
    ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    app = discover_apps().get(
        supplied.stem.lower()
    )

    if app is not None:
        return app.resolve()

    raise FileNotFoundError(
        f"Application or program not found: {name_or_path}"
    )


def assemble_source(source: Path) -> tuple[Path, Path]:
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    generated_source = (
        WORK_DIR / "_os_console_generated.ifa4"
    )
    output_prefix = WORK_DIR / "_os_console_program"

    assembly_source = source

    if source.suffix == ".ifa4y":
        frontend_result = subprocess.run(
            [
                sys.executable,
                str(YORUBA_FRONTEND),
                str(source),
                str(generated_source),
            ],
            cwd=PROJECT_ROOT,
        )

        if frontend_result.returncode != 0:
            raise RuntimeError(
                "OHÙN IFÁ V4 source compilation failed."
            )

        assembly_source = generated_source

    elif source.suffix != ".ifa4":
        raise ValueError(
            "Program must end in .ifa4 or .ifa4y"
        )

    assembler_result = subprocess.run(
        [
            sys.executable,
            str(ASSEMBLER),
            str(assembly_source),
            str(output_prefix),
        ],
        cwd=PROJECT_ROOT,
    )

    if assembler_result.returncode != 0:
        raise RuntimeError(
            "V4 assembly failed."
        )

    hex_path = output_prefix.with_suffix(".hex")
    listing_path = output_prefix.with_suffix(".lst")

    return hex_path, listing_path


def load_hex_program(
    session: BridgeSession,
    hex_path: Path,
) -> int:
    instructions: list[int] = []

    for line_number, raw_line in enumerate(
        hex_path.read_text(
            encoding="utf-8"
        ).splitlines(),
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

        instructions.append(instruction)

    if not instructions:
        raise ValueError(
            f"No instructions found in {hex_path}"
        )

    if len(instructions) > 256:
        raise ValueError(
            "V4 program exceeds 256 instructions"
        )

    for address, instruction in enumerate(
        instructions
    ):
        session.command(
            f"LOAD {address:02x} {instruction:04x}"
        )

    print(
        f"OK PROGRAM LOADED: "
        f"{len(instructions)} instructions"
    )

    return len(instructions)


def execute_native(
    session: BridgeSession,
    operation_name: str,
    arguments: list[str],
) -> None:
    normalized_arguments = [
        item
        for item in arguments
        if item.upper() not in {"ATI", "ÀTI"}
    ]

    if len(normalized_arguments) != 2:
        raise ValueError(
            f"{operation_name} requires two operands.\n"
            f"Example: {operation_name} 13 ATI 6"
        )

    a = parse_byte(normalized_arguments[0])
    b = parse_byte(normalized_arguments[1])

    session.last_operation_name = operation_name
    session.last_operand_a = a
    session.last_operand_b = b

    session.command(
        f"EXEC {operation_name} {a:02x} {b:02x}"
    )


def main() -> None:
    history: list[str] = []
    active_yara: int | None = None
    babalawo_enabled = False
    loaded_source: Path | None = None
    latest_listing: Path | None = None

    try:
        session = BridgeSession()
    except (OSError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)

    print_banner()

    try:
        while True:
            yara_text = (
                "NONE"
                if active_yara is None
                else str(active_yara)
            )

            try:
                raw_line = input(
                    f"OHÙN[V4:YÀRÁ-{yara_text}]> "
                ).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not raw_line:
                continue

            history.append(raw_line)

            try:
                if execute_symbolic_expression(
                    session,
                    raw_line,
                ):
                    continue
            except ValueError as error:
                print(f"ERROR: {error}")
                continue

            try:
                parts = shlex.split(raw_line)
            except ValueError as error:
                print(f"ERROR: {error}")
                continue

            original_command = parts[0]
            command = normalize(original_command)
            arguments = parts[1:]

            try:
                if command == "HELP":
                    print_help()
                    continue

                if command == "OYELA":
                    oyela(session, english=False)
                    continue

                if command == "OYELAA":
                    oyela(session, english=True)
                    continue

                if command == "CLEAR":
                    print("\033[2J\033[H", end="")
                    print_banner()
                    continue

                if command == "HISTORY":
                    for index, item in enumerate(
                        history,
                        start=1,
                    ):
                        print(f"{index:>3}: {item}")
                    continue

                if command == "QUIT":
                    break

                if command == "BABALAWO_ON":
                    session.command("BABALAWO ON")
                    babalawo_enabled = True
                    continue

                if command == "BABALAWO_OFF":
                    session.command("BABALAWO OFF")
                    babalawo_enabled = False
                    continue

                if command == "ENTER":
                    if len(arguments) != 1:
                        raise ValueError(
                            "ENTER requires one YÀRÁ ID."
                        )

                    yara_id = int(arguments[0], 0)

                    if not 0 <= yara_id < MAX_YARA:
                        raise ValueError(
                            "YÀRÁ ID must be between "
                            "0 and 15."
                        )

                    session.command(
                        f"CREATE {yara_id}"
                    )
                    session.command(
                        f"SELECT {yara_id}"
                    )

                    active_yara = yara_id
                    continue

                if command in {
                    "CREATE",
                    "SELECT",
                    "PAUSE",
                    "RESUME",
                    "DESTROY",
                }:
                    if len(arguments) != 1:
                        raise ValueError(
                            f"{command} requires one YÀRÁ ID."
                        )

                    yara_id = int(arguments[0], 0)

                    if not 0 <= yara_id < MAX_YARA:
                        raise ValueError(
                            "YÀRÁ ID must be between "
                            "0 and 15."
                        )

                    session.command(
                        f"{command} {yara_id}"
                    )

                    if command == "SELECT":
                        active_yara = yara_id

                    if (
                        command == "DESTROY"
                        and active_yara == yara_id
                    ):
                        active_yara = None

                    continue

                native_name = original_command.upper()

                if native_name in NATIVE_OPERATIONS:
                    execute_native(
                        session,
                        native_name,
                        arguments,
                    )
                    continue

                if command == "APPS":
                    print_apps()
                    continue

                if command in {
                    "LOADAPP",
                    "LOADPROGRAM",
                }:
                    if len(arguments) != 1:
                        raise ValueError(
                            f"{command} requires one source."
                        )

                    loaded_source = resolve_source(
                        arguments[0]
                    )

                    hex_path, latest_listing = (
                        assemble_source(loaded_source)
                    )

                    load_hex_program(
                        session,
                        hex_path,
                    )

                    print(
                        f"OK SOURCE READY: "
                        f"{loaded_source.name}"
                    )
                    continue

                if command == "RUNAPP":
                    if len(arguments) != 1:
                        raise ValueError(
                            "RUNAPP requires one application."
                        )

                    loaded_source = resolve_source(
                        arguments[0]
                    )

                    hex_path, latest_listing = (
                        assemble_source(loaded_source)
                    )

                    load_hex_program(
                        session,
                        hex_path,
                    )

                    session.command(
                        "RUN",
                        first_timeout=3.0,
                        idle_timeout=0.25,
                    )
                    continue

                if command == "LISTING":
                    if (
                        latest_listing is None
                        or not latest_listing.exists()
                    ):
                        print(
                            "No program has been assembled "
                            "in this session."
                        )
                    else:
                        print()
                        print(
                            latest_listing.read_text(
                                encoding="utf-8"
                            ),
                            end="",
                        )
                    continue

                if command == "RAW":
                    if not arguments:
                        raise ValueError(
                            "RAW requires a bridge command."
                        )

                    session.command(
                        " ".join(arguments),
                        first_timeout=3.0,
                        idle_timeout=0.25,
                    )
                    continue

                if command in RAW_BRIDGE_COMMANDS:
                    session.command(
                        " ".join(
                            [command] + arguments
                        ),
                        first_timeout=3.0,
                        idle_timeout=0.25,
                    )
                    continue

                print(
                    f"ERROR UNKNOWN_COMMAND "
                    f"{original_command}"
                )

            except (
                FileNotFoundError,
                OSError,
                RuntimeError,
                ValueError,
            ) as error:
                print(f"ERROR: {error}")

    finally:
        session.close()

    print("DÁ — OHÙN IFÁ V4 operating system closed.")


if __name__ == "__main__":
    main()
