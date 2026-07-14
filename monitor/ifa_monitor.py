#!/usr/bin/env python3

# --- IFÁ project import bootstrap ---
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# -----------------------------------

import os
import atexit
import shlex
import subprocess
import time
import re
from pathlib import Path
from language_v3.spec.voice import VOICE

OJU_ODU = [
    ("ÒGBÈ", "light, openness, clarity, emergence"),
    ("ÒYÈKÚ", "depth, concealment, endings, ancestral shadow"),
    ("ÌWÒRÌ", "reflection, inner seeing, transformation"),
    ("ÒDÍ", "boundary, enclosure, protection, resistance"),
    ("ÌRÒSÙN", "lineage, earth, blood, foundation"),
    ("ÒWÓNRÍN", "movement, instability, turning point"),
    ("ÒBÀRÀ", "speech, exchange, manifestation"),
    ("ÒKÀNRÀN", "fire, conflict, intensity, correction"),
    ("ÒGÚNDÁ", "cutting, force, iron, breakthrough"),
    ("ÒSÁ", "wind, change, dispersal, sudden shift"),
    ("ÌKÁ", "constraint, danger, entanglement"),
    ("ÒTÚRÚPỌ̀N", "inheritance, burden, continuity"),
    ("ÒTÚRÁ", "elevation, clarity, spiritual opening"),
    ("ÌRẸ̀TẸ̀", "pressure, endurance, refinement"),
    ("ÒṢÉ", "sweetness, renewal, cleansing, blessing"),
    ("ÒFÚN", "completion, whiteness, fullness, closure"),
]

HISTORY_LOG = []

# Display state is independent from privilege state.
DISPLAY_MODE = "CLEAN"

LAST_STDOUT = ""
OHUN_HISTORY = []

#=======================================================================
# IFÁ V4 — YÀRÁ Operating System State
#=======================================================================

ODU_COUNT = 16

# Operating-system capacity. This is independent of ODU_COUNT.
MAX_YARA = int(os.environ.get("IFA_MAX_YARA", "16"))

# Babaláwo is a privilege level used to invoke protected Onílẹ̀
# services. It is not the display/trace mode.
BABALAWO_MODE = False

# No YÀRÁ is active until explicitly selected.
ACTIVE_YARA = None

#=======================================================================
# V4 shell hierarchy
#
# GENERAL
#     General OHÙN IFÁ shell
#
# ONILE
#     Protected ONÍLẸ̀ administrative/security layer
#     available only through Babaláwo mode
#
# YARA
#     Active isolated YÀRÁ execution context
#=======================================================================

SHELL_MODE = "GENERAL"

# The first sixteen contexts receive canonical Odù aliases.
YARA_REGISTRY = {
    "OGBE": 0,
    "OYEKU": 1,
    "IWORI": 2,
    "ODI": 3,
    "IROSUN": 4,
    "OWONRIN": 5,
    "OBARA": 6,
    "OKANRAN": 7,
    "OGUNDA": 8,
    "OSA": 9,
    "IKA": 10,
    "OTURUPON": 11,
    "OTURA": 12,
    "IRETE": 13,
    "OSE": 14,
    "OFUN": 15,
}

YARA_NAMES = {
    yara_id: name
    for name, yara_id in YARA_REGISTRY.items()
}

#=======================================================================
# Monitor-side V4 lifecycle registry
#
# This mirrors the hardware YÀRÁ Manager until the monitor is connected
# directly to the structured RTL bridge.
#
# valid:
#     The context exists.
#
# running:
#     The context may be selected and execute.
#
# paused:
#     The context exists, but execution is suspended.
#=======================================================================

#=======================================================================
# V4 inter-YÀRÁ delegation state
#
# Permission is directional:
#
#     (source_yara, destination_yara)
#
# Isolation remains the default.
#=======================================================================

YARA_DELEGATION_PERMISSIONS = set()

DELEGATION_STATS = {
    "grants": 0,
    "revokes": 0,
    "shares": 0,
    "denied": 0,
}

YARA_STATE = {}

for yara_id in range(MAX_YARA):
    YARA_STATE[yara_id] = {
        "id": yara_id,
        "name": YARA_NAMES.get(
            yara_id,
            f"YARA{yara_id}"
        ),
        "valid": False,
        "running": False,
        "paused": False,
        "created_count": 0,
        "selected_count": 0,
        "pause_count": 0,
        "resume_count": 0,
        "execution_count": 0,
        "denied_count": 0,

        # Relation-frame delegation metadata.
        "relation_frame": None,

        # A stable copy loaded for subsequent calculations.
        #
        # relation_frame:
        #     latest local or imported frame
        #
        # loaded_frame:
        #     explicit calculation source selected by FRAME LO
        "loaded_frame": None,
        "frame_load_count": 0,
        "frame_calculation_count": 0,

        "share_out_count": 0,
        "share_in_count": 0,
        "share_denied_count": 0,
    }

LAST_RUN_TIME = {"assemble": 0.0, "compile": 0.0, "execute": 0.0, "total": 0.0}

V4_NATIVE_OPERATIONS = {
    "PAPO": 0x0,
    "YO": 0x1,
    "DAGBA": 0x2,
    "PIN": 0x3,
    "KU": 0x4,
    "GBE": 0x5,
    "SEDA": 0x6,
    "JU": 0x7,
    "KERE": 0x8,
}

V4_OPERATION_ALIASES = {
    "PÀPỌ̀": "PAPO",
    "YỌ": "YO",
    "DÁGBA": "DAGBA",
    "KÙ": "KU",
    "GBÉ": "GBE",
    "ṢẸ̀DÁ": "SEDA",
    "JÙ": "JU",
    "KERÉ": "KERE",
}


HELP = """
OHÙN IFÁ — ÌRÀNLỌ́WỌ́
---------------------

Ọ̀RỌ̀ taara
-----------
2+2
5-3
PAPO MEJI ATI META
YO MARUN ATI MEJI
SEDA 0xA5 ATI 0x11
TE ODU

Bẹrẹ Ọ̀rọ̀ nínú YÀRÁ ODÙ
----------------------
YARA OGBE

Example:
YARA OGBE
Ọ̀RỌ̀[OGBE 0x00]> PAPO META ATI MEJI
Ọ̀RỌ̀[OGBE 0x01]> TE ODU
Ọ̀RỌ̀[OGBE 0x02]> DURO

Ṣiṣe fáìlì
----------
RUN file.ifa
RUN file.ifa3
BERE file.ifa3

Ìmọ̀ ODÙ
--------
DAIFA
DÁIFÁ
PRINTODU
PRINTODUALL

BABALÁWO mode
-------------
BABALAWO        show mode
BABALAWO TAN    trace/debug ON
BABALAWO PA     trace/debug OFF

Ètò
---
HELP
VERSION
STATE
HISTORY
TIME
CLEAR
EXIT
QUIT

Àkíyèsí
-------
Àmì Yorùbá àti lai àmì mejeeji wọlé.
Example:
PÀPỌ̀ MEJI ATI META
PAPO MEJI ATI META
"""


BANNER = """
═══════════════════════════════════════════════════════════════════════
                     OHÙN IFÁ
═══════════════════════════════════════════════════════════════════════

Version      : 2.0
Core         : Relation Processor Core (RPC)
Architecture : ODU V2
Shell        : OHÙN IFÁ

Native Services
---------------
• DÁIFÁ
• PRINTODU
• PRINTODUALL

Type HELP for available commands.

═══════════════════════════════════════════════════════════════════════
"""

def boot():
    print()
    print("Booting IFÁ ODU Processor...")
    print()
    for item in [
        "Loading Relation Core",
        "Loading Relation Memory",
        "Loading Relation Feedback",
        "Loading Call Stack",
        "Loading Relation Stack",
        "Loading Assembler",
        "Loading DÁIFÁ Service",
        "Loading Knowledge Base",
        "Loading OHÙN IFÁ",
    ]:
        print(f"{item:.<45} OK")
    print()
    input("Press ENTER to enter IFÁ OS...")
    print(BANNER)

def parse_value(x):
    x = x.strip()
    if x.lower().startswith("0x"):
        return int(x, 16) & 0xFF
    if any(c in "ABCDEFabcdef" for c in x):
        return int(x, 16) & 0xFF
    return int(x, 10) & 0xFF

def print_daifa():
    print("═══════════════════════════════════════")
    print("        DÁ IFÁ — THE SIXTEEN OJÚ ODÙ")
    print("═══════════════════════════════════════")
    for i, (name, meaning) in enumerate(OJU_ODU):
        print(f"0x{i:02X}  {name:<12}  — {meaning}")
    print("═══════════════════════════════════════")

def print_version():
    print("IFÁ ODU Processor")
    print("-----------------")
    print("Version        : V2.0")
    print("Core           : ODU V2 / RPC")
    print("Word Width     : 8-bit relation, 16-bit instruction")
    print("Control        : Branch, CALL/RET, JMP")
    print("Stacks         : Value stack + Relation-frame stack")
    print("Monitor        : IFÁ OS v0")
    print("Native Service : DÁIFÁ")

def print_state():
    print("IFÁ V4 PROCESSOR STATE")
    print("----------------------")
    print("Kernel         : ONÍLẸ̀")
    print(
        "Babaláwo      :",
        "TAN" if BABALAWO_MODE else "PA"
    )
    print(f"Display        : {DISPLAY_MODE}")
    print(f"MAX_YARA       : {MAX_YARA}")
    print(f"Shell mode     : {SHELL_MODE}")

    if ACTIVE_YARA is None:
        print("Active YÀRÁ    : NONE")
    else:
        print(f"Active YÀRÁ    : {active_yara_name()}")
        print(f"Context ID     : {ACTIVE_YARA}")

def print_history():
    if not HISTORY_LOG:
        print("No history yet.")
        return
    for i, item in enumerate(HISTORY_LOG, 1):
        print(f"{i:03d}  {item}")

def print_time():
    print("Last Run Timing")
    print("---------------")
    print(f"Assemble : {LAST_RUN_TIME['assemble']:.3f} s")
    print(f"Compile  : {LAST_RUN_TIME['compile']:.3f} s")
    print(f"Execute  : {LAST_RUN_TIME['execute']:.3f} s")
    print(f"Total    : {LAST_RUN_TIME['total']:.3f} s")

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def v3_placeholder(name):
    print(f"{name}: reserved for V3.")


def signed8(v):
    return v - 256 if v >= 128 else v

def extract_abajade(stdout):
    fields = {
        "PRINTY":  "OYÈLÁ",
        "PRINTRA": "FARAPỌ̀",
        "PRINTRD": "YÀTỌ̀",
        "PRINTR0": "ÌPÌLẸ̀",
        "PRINTT":  "GBÉ",
    }

    found = {}

    for line in stdout.splitlines():
        m = re.search(r">>>\s+(PRINTY|PRINTRA|PRINTRD|PRINTR0|PRINTT)\s*=\s*([0-9a-fA-F]{2}).*?([À-ỹA-ZỌṢẸÈÉÍÌÒÓÙÚÂÊÎÔÛÁẸỌṢa-zọṣẹèéíìòóùúàá\-]+)?\s*$", line)
        if m:
            key = m.group(1)
            hx = m.group(2).lower()
            name = (m.group(3) or "").strip()
            found[key] = (hx, name)

        # fallback for PRINTY lines like: "03  ÒDÍ"
        m2 = re.match(r"^([0-9a-fA-F]{2})\s+(.+)$", line.strip())
        if m2 and "PRINTY" not in found:
            found["PRINTY"] = (m2.group(1).lower(), m2.group(2).strip())

    print("ÀBÁJÁDE")
    print("--------")

    if not found:
        print("KÒ SÍ ÀBÁJÁDE.")
        return

    order = ["PRINTY", "PRINTRA", "PRINTRD", "PRINTR0", "PRINTT"]

    for k in order:
        if k not in found:
            continue

        hx, name = found[k]
        v = int(hx, 16)
        label = fields[k]

        if k == "PRINTY":
            print(f"{label:<8}= 0x{hx.upper()} ({signed8(v)})  {name}")
        else:
            print(f"{label:<8}= 0x{hx.upper()}        {name}")


def run_program(path):
    program = Path(path)
    if not program.exists():
        print(f"File not found: {program}")
        return

    t0 = time.perf_counter()

    print(f"[ASSEMBLE] {program}")
    a0 = time.perf_counter()

    if program.suffix == ".ifa3":
        subprocess.run(["./ifa3", str(program)], check=True)
    else:
        subprocess.run(["python3", "tools/ifaasm_odu_v2.py", str(program)], check=True)

    a1 = time.perf_counter()

    print("[COMPILE]")
    c0 = time.perf_counter()
    subprocess.run([
        "iverilog", "-g2012",
        "rtl_v2/ifa_call_stack.sv",
        "rtl_v2/ifa_relation_frame_stack.sv",
        "rtl_v3/ifa_rpc.sv",
        "rtl_v2/ifa_relation_state_memory.sv",
        "rtl_v2/ifa_relation_feedback_unit.sv",
        "rtl_v2/ifa_odu_v2_core.sv",
        "rtl_v2/ifa_odu_v2_cpu.sv",
        "tb_v2/tb_odu_v2_cpu.sv",
        "-o", "sim/ifa_monitor_run.out",
    ], check=True)
    c1 = time.perf_counter()

    print("[RUN]")
    e0 = time.perf_counter()
    result = subprocess.run(["vvp", "sim/ifa_monitor_run.out"],  capture_output=True)
    stdout = result.stdout.decode("utf-8", errors="replace")
    e1 = time.perf_counter()

    if BABALAWO_MODE:
        print(stdout, end="")
    else:
        extract_abajade(stdout)

    LAST_RUN_TIME["assemble"] = a1 - a0
    LAST_RUN_TIME["compile"] = c1 - c0
    LAST_RUN_TIME["execute"] = e1 - e0
    LAST_RUN_TIME["total"] = time.perf_counter() - t0

def run_macro_program(text, name="_monitor_tmp.ifa"):
    tmp = Path("programs_v2") / name
    tmp.write_text(text)
    run_program(tmp)

def ifa_arithmetic(op, a, b):
    av = parse_value(a)
    bv = parse_value(b)

    if op == "ADD":
        program = f"LOADA 0x{av:02X}\nLOADB 0x{bv:02X}\nRPC_ADD\nPRINTODU\nHALT\n"
    elif op == "SUB":
        program = f"LOADA 0x{av:02X}\nLOADB 0x{bv:02X}\nRPC_SUB\nPRINTODU\nHALT\n"
    elif op == "MUL":
        y = (av * bv) & 0xFF
        print(f"IFÁ MUL {av} * {bv} = 0x{y:02X} ({y}) — full native algorithm reserved for V3")
        return
    elif op == "DIV":
        if bv == 0:
            print("Division by zero.")
            return
        y = (av // bv) & 0xFF
        print(f"IFÁ DIV {av} / {bv} = 0x{y:02X} ({y}) — full native algorithm reserved for V3")
        return
    elif op == "MOD":
        if bv == 0:
            print("Modulo by zero.")
            return
        y = (av % bv) & 0xFF
        print(f"IFÁ MOD {av} % {bv} = 0x{y:02X} ({y}) — full native algorithm reserved for V3")
        return
    elif op == "EXP":
        y = pow(av, bv, 256)
        print(f"IFÁ EXP {av}^{bv} = 0x{y:02X} ({y}) — full native algorithm reserved for V3")
        return
    else:
        print("Unknown arithmetic op.")
        return

    run_macro_program(program, "_monitor_expr.ifa")

def ifa_relation(op, a, b):
    av = parse_value(a)
    bv = parse_value(b)

    agree = av & bv
    disagree = av ^ bv
    toggle = (~disagree) & 0xFF
    transport = ((av << 1) | (av >> 7)) & 0xFF

    print("IFÁ Relation")
    print("------------")
    print(f"A          : 0x{av:02X}")
    print(f"B          : 0x{bv:02X}")
    if op == "AGREE":
        print(f"Agreement  : 0x{agree:02X}")
    elif op == "DISAGREE":
        print(f"Disagree   : 0x{disagree:02X}")
    elif op == "TOGGLE":
        print(f"Toggle     : 0x{toggle:02X}")
    elif op == "TRANSPORT":
        print(f"Transport  : 0x{transport:02X}")
    elif op == "PHI":
        print(f"Agreement  : 0x{agree:02X}")
        print(f"Disagree   : 0x{disagree:02X}")
        print(f"Toggle     : 0x{toggle:02X}")
        print(f"Transport  : 0x{transport:02X}")
    else:
        print("Unknown relation op.")



def normalize_symbolic_oro(c):
    text = c.strip().replace(" ", "")

    patterns = (
        (r"(0x[0-9a-fA-F]+|\d+)\+(0x[0-9a-fA-F]+|\d+)", "PAPO"),
        (r"(0x[0-9a-fA-F]+|\d+)\-(0x[0-9a-fA-F]+|\d+)", "YO"),
        (r"(0x[0-9a-fA-F]+|\d+)\*(0x[0-9a-fA-F]+|\d+)", "DAGBA"),
        (r"(0x[0-9a-fA-F]+|\d+)\/(0x[0-9a-fA-F]+|\d+)", "PIN"),
        (r"(0x[0-9a-fA-F]+|\d+)%(0x[0-9a-fA-F]+|\d+)", "KU"),
        (r"(0x[0-9a-fA-F]+|\d+)\^(0x[0-9a-fA-F]+|\d+)", "GBE"),
        (r"(0x[0-9a-fA-F]+|\d+)==(0x[0-9a-fA-F]+|\d+)", "SEDA"),
        (r"(0x[0-9a-fA-F]+|\d+)>(0x[0-9a-fA-F]+|\d+)", "JU"),
        (r"(0x[0-9a-fA-F]+|\d+)<(0x[0-9a-fA-F]+|\d+)", "KERE"),
    )

    for pattern, op in patterns:
        m = re.fullmatch(pattern, text)
        if m:
            return f"{op} {m.group(1)} ATI {m.group(2)}"

    return c

V4_BRIDGE_PROCESS = None


def stop_persistent_v4_bridge():
    """Stop the live V4 bridge process cleanly."""

    global V4_BRIDGE_PROCESS

    process = V4_BRIDGE_PROCESS

    if process is None:
        return

    if process.poll() is None:
        try:
            process.stdin.write("QUIT\n")
            process.stdin.flush()
            process.wait(timeout=2)
        except Exception:
            process.terminate()

    V4_BRIDGE_PROCESS = None


def start_persistent_v4_bridge():
    """Start or return the live interactive V4 bridge."""

    global V4_BRIDGE_PROCESS

    if (
        V4_BRIDGE_PROCESS is not None
        and V4_BRIDGE_PROCESS.poll() is None
    ):
        return V4_BRIDGE_PROCESS

    bridge_binary = Path("sim/v4/ifa_v4_os_bridge.out")

    if not bridge_binary.exists():
        raise FileNotFoundError(
            f"V4 OS bridge binary not found: {bridge_binary}"
        )

    process = subprocess.Popen(
        [
            "vvp",
            str(bridge_binary),
            "+INTERACTIVE",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    ready_line = process.stdout.readline().strip()

    if ready_line != "IFA_V4_OS_BRIDGE READY":
        stderr = process.stderr.read()

        process.terminate()

        raise RuntimeError(
            "V4 OS bridge failed to start. "
            f"stdout={ready_line!r} stderr={stderr!r}"
        )

    V4_BRIDGE_PROCESS = process
    return process


atexit.register(stop_persistent_v4_bridge)


def parse_v4_exec_line(stdout):
    """Parse the final EXEC or OK RUN result from the V4 bridge."""

    result_lines = []

    for raw_line in str(stdout).splitlines():
        line = raw_line.strip()

        if line.startswith("EXEC "):
            result_lines.append(
                line.split()[1:]
            )

        elif line.startswith("OK RUN "):
            result_lines.append(
                line.split()[2:]
            )

    if not result_lines:
        return None

    fields = {}

    for token in result_lines[-1]:
        if "=" not in token:
            continue

        key, value = token.split("=", 1)
        fields[key] = value

    required = {
        "ID",
        "OP",
        "HIT",
        "MISS",
        "Y",
        "RA",
        "RD",
        "R0",
        "T",
        "VALID",
        "EXC",
        "EXC_CODE",
        "STATE",
        "STATE_CODE",
        "EQ",
        "GT",
        "LT",
    }

    if not required.issubset(fields):
        return None

    parsed = {
        "id": int(fields["ID"], 10),
        "op": int(fields["OP"], 16),
        "hit": int(fields["HIT"], 10),
        "miss": int(fields["MISS"], 10),

        "Y": int(fields["Y"], 16),
        "RA": int(fields["RA"], 16),
        "RD": int(fields["RD"], 16),
        "R0": int(fields["R0"], 16),
        "T": int(fields["T"], 16),

        "valid": int(fields["VALID"], 10),

        "exception_valid": int(fields["EXC"], 10),
        "exception_code": int(fields["EXC_CODE"], 16),

        "state_valid": int(fields["STATE"], 10),
        "state_code": int(fields["STATE_CODE"], 16),

        "eq": int(fields["EQ"], 10),
        "gt": int(fields["GT"], 10),
        "lt": int(fields["LT"], 10),
    }

    # Program-run results also expose final execution context.
    if "PC" in fields:
        parsed["pc"] = int(fields["PC"], 16)

    if "IR" in fields:
        parsed["ir"] = int(fields["IR"], 16)

    if "A" in fields:
        parsed["A"] = int(fields["A"], 16)

    if "B" in fields:
        parsed["B"] = int(fields["B"], 16)

    if "ADDR" in fields:
        parsed["address"] = int(fields["ADDR"], 16)

    if "FLAGS" in fields:
        parsed["flags"] = int(fields["FLAGS"], 16)

    return parsed

def run_v4_os_bridge(commands):
    """Send commands through the persistent interactive V4 bridge."""

    process = start_persistent_v4_bridge()

    output_lines = []

    for command in commands:
        command = str(command).strip()

        if not command or command == "QUIT":
            continue

        if process.poll() is not None:
            raise RuntimeError(
                "V4 OS bridge terminated unexpectedly."
            )

        process.stdin.write(command + "\n")
        process.stdin.flush()

        response = process.stdout.readline()

        if response == "":
            raise RuntimeError(
                f"V4 OS bridge returned EOF after: {command}"
            )

        output_lines.append(response)

    return {
        "returncode": (
            process.poll()
            if process.poll() is not None
            else 0
        ),
        "stdout": "".join(output_lines),
        "stderr": "",
    }


def execute_v4_native_line(line):
    """Execute one numeric native operation as a V4 program."""

    parts = str(line).strip().split()

    if len(parts) != 4 or parts[2].upper() != "ATI":
        return None

    operation = parts[0].upper()
    operation = V4_OPERATION_ALIASES.get(
        operation,
        operation,
    )

    if operation not in V4_NATIVE_OPERATIONS:
        return None

    try:
        operand_a = int(parts[1], 0)
        operand_b = int(parts[3], 0)
    except ValueError:
        # Yoruba number words remain on the legacy language path
        # until the complete V4 frontend migration.
        return None

    if not 0 <= operand_a <= 0xFF:
        return None

    if not 0 <= operand_b <= 0xFF:
        return None

    yara_id = (
        ACTIVE_YARA
        if ACTIVE_YARA is not None
        else 0
    )

    operation_code = V4_NATIVE_OPERATIONS[operation]

    instruction_load_a = (
        0x1000
        | operand_a
    )

    instruction_load_b = (
        0x2000
        | operand_b
    )

    instruction_native = (
        0x8000
        | (operation_code << 8)
    )

    instruction_halt = 0xF100

    result = run_v4_os_bridge([
        "BABALAWO ON",
        f"CREATE {yara_id}",
        f"SELECT {yara_id}",

        # Reset the selected YÀRÁ execution context to program address 0.
        # The YÀRÁ local RMU is not cleared.
        "CONTEXT 00 0000 00 00 00 00",

        f"LOAD 00 {instruction_load_a:04x}",
        f"LOAD 01 {instruction_load_b:04x}",
        f"LOAD 02 {instruction_native:04x}",
        f"LOAD 03 {instruction_halt:04x}",

        "RUN",
    ])

    parsed = parse_v4_exec_line(
        result["stdout"]
    )

    return {
        "operation": operation,
        "bridge": result,
        "frame": parsed,
    }

def run_yoruba_line(line):
    native_result = execute_v4_native_line(line)

    if native_result is not None:
        bridge = native_result["bridge"]
        frame = native_result["frame"]
        operation = native_result["operation"]

        if bridge["returncode"] != 0:
            print(VOICE["error"])

            if bridge["stdout"]:
                print(bridge["stdout"], end="")

            if bridge["stderr"]:
                print(bridge["stderr"], end="")

            return

        if frame is None:
            print("ÀṢÌṢE: V4 bridge returned no EXEC frame.")
            return

        globals()["LAST_STDOUT"] = bridge["stdout"]

        if (
            SHELL_MODE == "YARA"
            and ACTIVE_YARA is not None
        ):
            record_yara_relation_frame(
                ACTIVE_YARA,
                operation,
                frame["Y"],
                frame["RA"],
                frame["RD"],
                frame["R0"],
                frame["T"],
            )

            state = YARA_STATE[ACTIVE_YARA]
            state["execution_count"] += 1

        print("ÀBÁJÁDE")
        print("--------")
        print(f"OP      = {operation}")
        print(f"OYÈLÁ   = 0x{frame['Y']:02X} ({frame['Y']})")
        print(f"FARAPỌ̀ = 0x{frame['RA']:02X}")
        print(f"YÀTỌ̀   = 0x{frame['RD']:02X}")
        print(f"ÌPÌLẸ̀  = 0x{frame['R0']:02X}")
        print(f"GBÉ     = 0x{frame['T']:02X}")
        print(
            "STATUS  = "
            f"VALID={frame['valid']} "
            f"EXC={frame['exception_valid']} "
            f"EXC_CODE={frame['exception_code']} "
            f"STATE={frame['state_valid']} "
            f"STATE_CODE={frame['state_code']} "
            f"EQ={frame['eq']} "
            f"GT={frame['gt']} "
            f"LT={frame['lt']} "
            f"HIT={frame['hit']} "
            f"MISS={frame['miss']}"
        )

        return

    tmp = Path("language_v3/examples/_monitor_line.ifa3")
    tmp.write_text(f"""BERE

{line}

TE ODU

DURO
""", encoding="utf-8")

    result = subprocess.run(
        ["./ifarun", str(tmp)],
        
        capture_output=True
    )

    out = result.stdout.decode("utf-8", errors="replace")
    globals()["LAST_STDOUT"] = out

    err = result.stderr.decode("utf-8", errors="replace")

    if DISPLAY_MODE == "TRACE":
        print(out, end="")
    if result.returncode != 0:
        print(VOICE["error"])
        print(out, end="")
        print(err, end="")
        return

        print(result.stderr)
        return

    # Legacy language fallback may display its result, but it must not
    # modify the authoritative V4 YÀRÁ frame. RTL is the execution and
    # relation-memory source of truth.
    extract_abajade(out)
    return
    for ln in out.splitlines():
        stripped = ln.strip()

        if stripped.startswith(">>>"):
            print(stripped)

        elif len(stripped) >= 2 and stripped[:2].lower() in [
            "00","01","02","03","04","05","06","07",
            "08","09","0a","0b","0c","0d","0e","0f"
        ]:
            print(stripped)


def run_expression(expr):
    expr = expr.replace(" ", "")
    if "+" in expr:
        a, b = expr.split("+", 1)
        ifa_arithmetic("ADD", a, b)
    elif "-" in expr:
        a, b = expr.split("-", 1)
        ifa_arithmetic("SUB", a, b)
    else:
        print("Expression not understood. Try 2+1 or A5+11.")



# Temporary compatibility alias for older monitor functions.
ODU_YARA = YARA_REGISTRY


def resolve_yara_id(value):
    """Resolve an Odù alias or numeric YÀRÁ identifier."""

    raw = str(value).strip()
    key = raw.upper()

    if key in YARA_REGISTRY:
        yara_id = YARA_REGISTRY[key]
    else:
        try:
            yara_id = int(raw, 0)
        except ValueError:
            return None

    if yara_id < 0 or yara_id >= MAX_YARA:
        return None

    return yara_id


def yara_display_name(yara_id):
    """Return an Odù alias or generated YÀRÁ name."""

    return YARA_NAMES.get(
        yara_id,
        f"YARA{yara_id}"
    )


def ask_confirmation(message):
    """Ask for a BẸẸNI/RARA confirmation."""

    try:
        answer = input(f"{message} [BẸẸNI/RARA]: ").strip().upper()
    except EOFError:
        print("RARA")
        return False

    yes_values = {
        "BẸẸNI",
        "BEENI",
        "YES",
        "Y",
    }

    no_values = {
        "RARA",
        "NO",
        "N",
    }

    if answer in yes_values:
        return True

    if answer in no_values:
        return False

    print("KÒ YE. Lo BẸẸNI tabi RARA.")
    return False


def require_onile_mode():
    """Require the protected ONÍLẸ̀ administrative shell."""

    if SHELL_MODE != "ONILE":
        print(
            "DENY: This command is available only "
            "inside ONÍLẸ̀ administrative mode."
        )
        return False

    if not BABALAWO_MODE:
        print(
            "DENY: ONÍLẸ̀ administration requires "
            "BABALÁWO TAN."
        )
        return False

    return True


def active_yara_name():
    """Return the display name of the currently selected YÀRÁ."""

    if ACTIVE_YARA is None:
        return None

    return YARA_NAMES.get(
        ACTIVE_YARA,
        f"YARA{ACTIVE_YARA}"
    )


def onile_create_yara(name):
    """Create and start one YÀRÁ context."""

    if not require_onile_mode():
        return False

    yara_id = resolve_yara_id(name)

    if yara_id is None:
        print(f"DENY: Invalid YÀRÁ name or ID: {name}")
        return False

    state = YARA_STATE[yara_id]

    if state["valid"]:
        print(
            f"DENY: YÀRÁ {state['name']} already exists."
        )
        return False

    state["valid"] = True
    state["running"] = True
    state["paused"] = False
    state["created_count"] += 1

    print(
        f"YÀRÁ {state['name']} created "
        f"(Context ID {yara_id})."
    )

    return True


def onile_destroy_yara(name, force=False):
    """Destroy one YÀRÁ, optionally without confirmation."""

    global ACTIVE_YARA
    global SHELL_MODE

    if not require_onile_mode():
        return False

    yara_id = resolve_yara_id(name)

    if yara_id is None:
        print(f"DENY: Invalid YÀRÁ name or ID: {name}")
        return False

    state = YARA_STATE[yara_id]

    if not state["valid"]:
        print(
            f"DENY: YÀRÁ {state['name']} does not exist."
        )
        return False

    if not force:
        confirmed = ask_confirmation(
            f"Destroy YÀRÁ {state['name']} "
            f"(Context ID {yara_id})?"
        )

        if not confirmed:
            print(
                f"Destroy cancelled. "
                f"YÀRÁ {state['name']} remains active."
            )
            return False

    state["valid"] = False
    state["running"] = False
    state["paused"] = False
    state["relation_frame"] = None
    state["loaded_frame"] = None

    # Remove every delegation permission involving this YÀRÁ.
    permissions_to_remove = {
        permission
        for permission in YARA_DELEGATION_PERMISSIONS
        if yara_id in permission
    }

    YARA_DELEGATION_PERMISSIONS.difference_update(
        permissions_to_remove
    )
    state["selected_count"] = 0

    if ACTIVE_YARA == yara_id:
        ACTIVE_YARA = None
        SHELL_MODE = "ONILE"

    print(
        f"YÀRÁ {state['name']} destroyed "
        f"(Context ID {yara_id})."
    )

    return True

def validate_existing_yara(value):
    """Resolve and validate one existing YÀRÁ."""

    yara_id = resolve_yara_id(value)

    if yara_id is None:
        print(
            f"DENY: Invalid YÀRÁ name or ID: {value}"
        )
        return None

    state = YARA_STATE[yara_id]

    if not state["valid"]:
        print(
            f"DENY: YÀRÁ {yara_display_name(yara_id)} "
            "has not been created."
        )
        return None

    return yara_id


def record_yara_relation_frame(
    yara_id,
    op,
    y,
    ra,
    rd,
    r0,
    transport,
):
    """Record the latest operation-aware relation frame."""

    if yara_id not in YARA_STATE:
        return False

    state = YARA_STATE[yara_id]

    if not state["valid"]:
        return False

    state["relation_frame"] = {
        "OP": str(op).strip().upper(),
        "Y": int(y) & 0xFF,
        "RA": int(ra) & 0xFF,
        "RD": int(rd) & 0xFF,
        "R0": int(r0) & 0xFF,
        "T": int(transport) & 0xFF,
    }

    return True


def onile_grant_delegation(source, destination):
    """Grant directional frame-delegation permission."""

    if not require_onile_mode():
        return False

    source_id = validate_existing_yara(source)

    if source_id is None:
        return False

    destination_id = validate_existing_yara(destination)

    if destination_id is None:
        return False

    if source_id == destination_id:
        print(
            "DENY: Delegation permission requires "
            "different source and destination YÀRÁ."
        )
        DELEGATION_STATS["denied"] += 1
        return False

    permission = (
        source_id,
        destination_id,
    )

    if permission in YARA_DELEGATION_PERMISSIONS:
        print(
            "DENY: Delegation permission already exists: "
            f"{yara_display_name(source_id)} → "
            f"{yara_display_name(destination_id)}"
        )
        DELEGATION_STATS["denied"] += 1
        return False

    YARA_DELEGATION_PERMISSIONS.add(permission)
    DELEGATION_STATS["grants"] += 1

    print(
        "Permission granted: "
        f"{yara_display_name(source_id)} → "
        f"{yara_display_name(destination_id)}"
    )

    return True


def onile_revoke_delegation(source, destination):
    """Revoke directional frame-delegation permission."""

    if not require_onile_mode():
        return False

    source_id = validate_existing_yara(source)

    if source_id is None:
        return False

    destination_id = validate_existing_yara(destination)

    if destination_id is None:
        return False

    permission = (
        source_id,
        destination_id,
    )

    if permission not in YARA_DELEGATION_PERMISSIONS:
        print(
            "DENY: No delegation permission exists: "
            f"{yara_display_name(source_id)} → "
            f"{yara_display_name(destination_id)}"
        )
        DELEGATION_STATS["denied"] += 1
        return False

    YARA_DELEGATION_PERMISSIONS.remove(permission)
    DELEGATION_STATS["revokes"] += 1

    print(
        "Permission revoked: "
        f"{yara_display_name(source_id)} → "
        f"{yara_display_name(destination_id)}"
    )

    return True


def onile_share_relation_frame(source, destination):
    """Delegate the latest relation frame through ONÍLẸ̀."""

    if not require_onile_mode():
        return False

    source_id = validate_existing_yara(source)

    if source_id is None:
        return False

    destination_id = validate_existing_yara(destination)

    if destination_id is None:
        return False

    source_state = YARA_STATE[source_id]
    destination_state = YARA_STATE[destination_id]

    if source_id == destination_id:
        print(
            "DENY: A YÀRÁ cannot delegate a frame to itself."
        )

        source_state["share_denied_count"] += 1
        DELEGATION_STATS["denied"] += 1
        return False

    permission = (
        source_id,
        destination_id,
    )

    if permission not in YARA_DELEGATION_PERMISSIONS:
        print(
            "DENY: No delegation permission from "
            f"{source_state['name']} to "
            f"{destination_state['name']}."
        )

        source_state["share_denied_count"] += 1
        DELEGATION_STATS["denied"] += 1
        return False

    relation_frame = source_state["relation_frame"]

    if relation_frame is None:
        print(
            f"DENY: YÀRÁ {source_state['name']} "
            "has no recorded relation frame."
        )
        print(
            "Execute a relation inside the source YÀRÁ first."
        )

        source_state["share_denied_count"] += 1
        DELEGATION_STATS["denied"] += 1
        return False

    # Import only the relation frame.
    #
    # PC, registers, flags, call stack and program state are not copied.
    destination_state["relation_frame"] = dict(
        relation_frame
    )

    source_state["share_out_count"] += 1
    destination_state["share_in_count"] += 1

    DELEGATION_STATS["shares"] += 1

    print(
        "Relation frame delegated: "
        f"{source_state['name']} → "
        f"{destination_state['name']}"
    )

    print(
        "FRAME "
        f"Y={relation_frame['Y']:02x} "
        f"RA={relation_frame['RA']:02x} "
        f"RD={relation_frame['RD']:02x} "
        f"R0={relation_frame['R0']:02x} "
        f"T={relation_frame['T']:02x}"
    )

    return True


def show_delegation_permissions():
    """Display the current directional permission matrix."""

    if not require_onile_mode():
        return False

    print("ONÍLẸ̀ DELEGATION PERMISSIONS")
    print("-----------------------------")

    if not YARA_DELEGATION_PERMISSIONS:
        print("NONE")
    else:
        for source_id, destination_id in sorted(
            YARA_DELEGATION_PERMISSIONS
        ):
            print(
                f"{source_id:03d} "
                f"{yara_display_name(source_id):<12} "
                "→ "
                f"{destination_id:03d} "
                f"{yara_display_name(destination_id)}"
            )

    print("")
    print("DELEGATION STATISTICS")
    print("---------------------")
    print(
        f"Grants  : {DELEGATION_STATS['grants']}"
    )
    print(
        f"Revokes : {DELEGATION_STATS['revokes']}"
    )
    print(
        f"Shares  : {DELEGATION_STATS['shares']}"
    )
    print(
        f"Denied  : {DELEGATION_STATS['denied']}"
    )

    return True


def onile_show_status():
    """Show ONÍLẸ̀ kernel and lifecycle state."""

    if not require_onile_mode():
        return False

    valid_count = sum(
        1
        for state in YARA_STATE.values()
        if state["valid"]
    )

    running_count = sum(
        1
        for state in YARA_STATE.values()
        if state["valid"] and state["running"]
    )

    paused_count = sum(
        1
        for state in YARA_STATE.values()
        if state["valid"] and state["paused"]
    )

    print("ONÍLẸ̀ SYSTEM STATUS")
    print("--------------------")
    print(f"Kernel          : ONÍLẸ̀")
    print(f"MAX_YARA        : {MAX_YARA}")
    print(f"Created YÀRÁ    : {valid_count}")
    print(f"Running YÀRÁ    : {running_count}")
    print(f"Paused YÀRÁ     : {paused_count}")
    print(
        "Babaláwo       : "
        + ("TAN" if BABALAWO_MODE else "PA")
    )

    if ACTIVE_YARA is None:
        print("Active YÀRÁ     : NONE")
    else:
        print(
            f"Active YÀRÁ     : "
            f"{yara_display_name(ACTIVE_YARA)}"
        )
        print(f"Context ID      : {ACTIVE_YARA}")

    print("")
    print("YÀRÁ LIFECYCLE TABLE")
    print("--------------------")

    for yara_id in range(MAX_YARA):
        state = YARA_STATE[yara_id]

        if not state["valid"]:
            lifecycle = "EMPTY"
        elif state["paused"]:
            lifecycle = "PAUSED"
        elif state["running"]:
            lifecycle = "RUNNING"
        else:
            lifecycle = "STOPPED"

        marker = "*" if yara_id == ACTIVE_YARA else " "

        print(
            f"{marker} {yara_id:03d} "
            f"{state['name']:<12} "
            f"{lifecycle:<8} "
            f"selected={state['selected_count']}"
        )

    return True


def select_yara(name):
    """Select a created and running YÀRÁ from ONÍLẸ̀ mode."""

    global ACTIVE_YARA
    global SHELL_MODE

    if SHELL_MODE != "ONILE":
        print(
            "DENY: Enter ONÍLẸ̀ administrative mode "
            "before selecting a YÀRÁ."
        )
        return False

    if not BABALAWO_MODE:
        print(
            "DENY: YÀRÁ selection through ONÍLẸ̀ "
            "requires BABALÁWO TAN."
        )
        return False

    yara_id = resolve_yara_id(name)

    if yara_id is None:
        print(f"KÒ WỌLÉ: {name}")
        print(
            "Lo: YARA OGBE, YARA OYEKU, "
            "tabi YARA 16"
        )
        return False

    state = YARA_STATE[yara_id]

    if not state["valid"]:
        print(
            f"DENY: YÀRÁ {state['name']} "
            "has not been created."
        )
        print(
            f"Use: ONILE DA {state['name']}"
        )
        return False

    if not state["running"] or state["paused"]:
        print(
            f"DENY: YÀRÁ {state['name']} "
            "is not running."
        )
        return False

    ACTIVE_YARA = yara_id
    SHELL_MODE = "YARA"

    state["selected_count"] += 1

    print(
        f"YÀRÁ {state['name']} selected "
        f"(Context ID {ACTIVE_YARA})."
    )

    return True

def require_active_yara():
    """Return the active YÀRÁ state or deny the request."""

    if SHELL_MODE != "YARA" or ACTIVE_YARA is None:
        print("DENY: No active YÀRÁ execution mode.")
        print(
            "Use: BABALAWO TAN → ONILE → "
            "DA OGBE → YARA OGBE"
        )
        return None

    return YARA_STATE[ACTIVE_YARA]


def pause_active_yara():
    """Pause the active YÀRÁ and return to ONÍLẸ̀."""

    global ACTIVE_YARA
    global SHELL_MODE

    state = require_active_yara()

    if state is None:
        return False

    if not state["valid"]:
        print(
            f"DENY: YÀRÁ {state['name']} does not exist."
        )
        state["denied_count"] += 1
        return False

    if state["paused"] or not state["running"]:
        print(
            f"DENY: YÀRÁ {state['name']} is already paused."
        )
        state["denied_count"] += 1
        return False

    state["running"] = False
    state["paused"] = True
    state["pause_count"] += 1

    paused_name = state["name"]

    ACTIVE_YARA = None
    SHELL_MODE = "ONILE"

    print(
        f"YÀRÁ {paused_name} paused. "
        "Context and local RMU state preserved."
    )

    print(
        "Returned to ONÍLẸ̀ administrative mode."
    )

    return True


def resume_yara(name):
    """Resume one paused YÀRÁ from ONÍLẸ̀ mode."""

    if not require_onile_mode():
        return False

    yara_id = resolve_yara_id(name)

    if yara_id is None:
        print(
            f"DENY: Invalid YÀRÁ name or ID: {name}"
        )
        return False

    state = YARA_STATE[yara_id]

    if not state["valid"]:
        print(
            f"DENY: YÀRÁ {state['name']} does not exist."
        )
        state["denied_count"] += 1
        return False

    if state["running"] and not state["paused"]:
        print(
            f"DENY: YÀRÁ {state['name']} is already running."
        )
        state["denied_count"] += 1
        return False

    state["running"] = True
    state["paused"] = False
    state["resume_count"] += 1

    print(
        f"YÀRÁ {state['name']} resumed "
        f"(Context ID {yara_id})."
    )

    return True


def require_loaded_frame():
    """Return the active YÀRÁ and its loaded calculation frame."""

    state = require_active_yara()

    if state is None:
        return None, None

    loaded_frame = state.get("loaded_frame")

    if loaded_frame is None:
        print("DENY: No relation frame has been loaded.")
        print("Use FRAME LO first.")
        state["denied_count"] += 1
        return state, None

    return state, loaded_frame


def show_current_frame():
    """Display the current and loaded frames in the active YÀRÁ."""

    state = require_active_yara()

    if state is None:
        return False

    print("YÀRÁ RELATION FRAME")
    print("-------------------")
    print(f"Name       : {state['name']}")
    print(f"Context ID : {state['id']}")

    current = state.get("relation_frame")

    if current is None:
        print("Current    : NONE")
    else:
        print(
            "Current    : "
            f"OP={current.get('OP', 'UNKNOWN')} "
            f"Y={current['Y']:02x} "
            f"RA={current['RA']:02x} "
            f"RD={current['RD']:02x} "
            f"R0={current['R0']:02x} "
            f"T={current['T']:02x}"
        )

    loaded = state.get("loaded_frame")

    if loaded is None:
        print("Loaded     : NONE")
    else:
        print(
            "Loaded     : "
            f"OP={loaded.get('OP', 'UNKNOWN')} "
            f"Y={loaded['Y']:02x} "
            f"RA={loaded['RA']:02x} "
            f"RD={loaded['RD']:02x} "
            f"R0={loaded['R0']:02x} "
            f"T={loaded['T']:02x}"
        )

    return True


def load_current_frame():
    """Load the current relation frame for subsequent calculations."""

    state = require_active_yara()

    if state is None:
        return False

    current = state.get("relation_frame")

    if current is None:
        print(
            f"DENY: YÀRÁ {state['name']} "
            "has no current relation frame."
        )
        print(
            "Execute a relation or receive a delegated frame first."
        )
        state["denied_count"] += 1
        return False

    # Copy the frame so future calculations may replace relation_frame
    # without altering the explicitly loaded source.
    state["loaded_frame"] = dict(current)
    state["frame_load_count"] += 1

    loaded = state["loaded_frame"]

    print(
        f"Relation frame loaded in YÀRÁ {state['name']}."
    )

    print(
        "LOADED "
        f"OP={loaded.get('OP', 'UNKNOWN')} "
        f"Y={loaded['Y']:02x} "
        f"RA={loaded['RA']:02x} "
        f"RD={loaded['RD']:02x} "
        f"R0={loaded['R0']:02x} "
        f"T={loaded['T']:02x}"
    )

    return True


def calculate_from_loaded_frame(
    operation,
    field,
    second_value,
):
    """Use one loaded frame component as an arithmetic operand.

    Supported fields:

        Y
        RA
        RD
        R0
        T

    Supported operations:

        PAPO
        YO
        SEDA

    Example:

        FRAME PAPO Y ATI 6

    becomes:

        PAPO <loaded Y> ATI 6
    """

    state, loaded = require_loaded_frame()

    if state is None or loaded is None:
        return False

    # AUTO means: reuse the operation identity stored in the frame.
    if operation is None:
        operation = "AUTO"

    operation = str(operation).strip().upper()

    if operation in ("AUTO", "OP"):
        operation = str(
            loaded.get("OP", "UNKNOWN")
        ).strip().upper()

    field = field.strip().upper()

    valid_operations = {
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

    valid_fields = {
        "Y",
        "RA",
        "RD",
        "R0",
        "T",
    }

    if operation not in valid_operations:
        print(
            f"DENY: Unsupported frame operation: {operation}"
        )
        print("Lo: FRAME PAPO Y ATI 6")
        state["denied_count"] += 1
        return False

    if field not in valid_fields:
        print(
            f"DENY: Unknown relation-frame field: {field}"
        )
        print("Fields: Y RA RD R0 T")
        state["denied_count"] += 1
        return False

    try:
        operand_b = int(str(second_value), 0)
    except ValueError:
        print(
            f"DENY: Invalid second operand: {second_value}"
        )
        state["denied_count"] += 1
        return False

    if operand_b < 0 or operand_b > 0xFF:
        print(
            "DENY: Calculation operand must be between "
            "0 and 255."
        )
        state["denied_count"] += 1
        return False

    operand_a = loaded[field]

    state["frame_calculation_count"] += 1

    print(
        f"FRAME CALC {operation}: "
        f"{field}=0x{operand_a:02x} "
        f"ATI 0x{operand_b:02x}"
    )

    # Route through the monitor's existing arithmetic command path.
    #
    # This preserves the existing assembler, simulator, ÀBÁJÁDE output,
    # relation-frame capture and YÀRÁ accounting.
    execute(
        f"{operation} {operand_a} ATI {operand_b}"
    )

    return True


def show_yara_stats():
    """Display statistics for the active YÀRÁ."""

    state = require_active_yara()

    if state is None:
        return False

    print("YÀRÁ STATISTICS")
    print("---------------")
    print(f"Name          : {state['name']}")
    print(f"Context ID    : {state['id']}")
    print(f"Valid         : {state['valid']}")
    print(f"Running       : {state['running']}")
    print(f"Paused        : {state['paused']}")
    print(f"Created       : {state['created_count']}")
    print(f"Selected      : {state['selected_count']}")
    print(f"Paused count  : {state['pause_count']}")
    print(f"Resumed count : {state['resume_count']}")
    print(f"Executions    : {state['execution_count']}")
    print(f"Denied        : {state['denied_count']}")
    print(f"Shared out    : {state['share_out_count']}")
    print(f"Imported      : {state['share_in_count']}")
    print(f"Share denied  : {state['share_denied_count']}")
    print(f"Frame loads   : {state['frame_load_count']}")
    print(
        f"Frame calcs   : "
        f"{state['frame_calculation_count']}"
    )

    relation_frame = state["relation_frame"]

    if relation_frame is None:
        print("Relation frame : NONE")
    else:
        print(
            "Relation frame : "
            f"OP={relation_frame.get('OP', 'UNKNOWN')} "
            f"Y={relation_frame['Y']:02x} "
            f"RA={relation_frame['RA']:02x} "
            f"RD={relation_frame['RD']:02x} "
            f"R0={relation_frame['R0']:02x} "
            f"T={relation_frame['T']:02x}"
        )

    return True


def show_current_yara():
    """Show the current V4 execution context."""

    if ACTIVE_YARA is None:
        print("KÒ SÍ YÀRÁ TÍ A YÀN.")
        return

    state = YARA_STATE[ACTIVE_YARA]

    print("YÀRÁ CURRENT")
    print("------------")
    print(f"Name       : {active_yara_name()}")
    print(f"Context ID : {ACTIVE_YARA}")
    print(f"MAX_YARA   : {MAX_YARA}")
    print(f"Valid      : {state['valid']}")
    print(f"Running    : {state['running']}")
    print(f"Paused     : {state['paused']}")
    print(
        f"Selections : {state['selected_count']}"
    )


def list_yara():
    """List all configured YÀRÁ slots and lifecycle states."""

    print("YÀRÁ REGISTRY")
    print("-------------")

    for yara_id in range(MAX_YARA):
        state = YARA_STATE[yara_id]

        if not state["valid"]:
            lifecycle = "EMPTY"
        elif state["paused"]:
            lifecycle = "PAUSED"
        elif state["running"]:
            lifecycle = "RUNNING"
        else:
            lifecycle = "STOPPED"

        marker = "*" if yara_id == ACTIVE_YARA else " "

        print(
            f"{marker} {yara_id:03d} "
            f"{state['name']:<12} "
            f"{lifecycle}"
        )

def monitor_prompt():
    """Build the prompt for the current V4 shell level."""

    if SHELL_MODE == "ONILE":
        return "ONÍLẸ̀> "

    if SHELL_MODE == "YARA" and ACTIVE_YARA is not None:
        return f"OHÙN IFÁ[{active_yara_name()}]> "

    return "OHÙN IFÁ> "



def enter_onile_mode():
    """Enter or return to the protected ONÍLẸ̀ layer."""

    global SHELL_MODE
    global ACTIVE_YARA

    # From a YÀRÁ, ONILE returns to the already-authorized
    # administrative layer.
    if SHELL_MODE == "YARA":
        ACTIVE_YARA = None
        SHELL_MODE = "ONILE"

        print("Returned to ONÍLẸ̀ administrative mode.")
        return True

    # Entering ONÍLẸ̀ from the general shell requires Babaláwo.
    if not BABALAWO_MODE:
        print(
            "DENY: ONÍLẸ̀ administrative mode requires "
            "BABALÁWO TAN."
        )
        return False

    SHELL_MODE = "ONILE"
    ACTIVE_YARA = None

    print("ONÍLẸ̀ administrative mode entered.")
    return True


def leave_onile_mode():
    """Return from ONÍLẸ̀ to the general OHÙN IFÁ shell."""

    global SHELL_MODE
    global ACTIVE_YARA

    if SHELL_MODE == "YARA":
        ACTIVE_YARA = None
        SHELL_MODE = "ONILE"

        print("Returned to ONÍLẸ̀ administrative mode.")
        return True

    if SHELL_MODE == "ONILE":
        ACTIVE_YARA = None
        SHELL_MODE = "GENERAL"

        print("Returned to general OHÙN IFÁ shell.")
        return True

    print("Already in the general OHÙN IFÁ shell.")
    return True



def ita_leave_onile(force=False):
    """Leave ONÍLẸ̀, with optional confirmation bypass."""

    if SHELL_MODE == "YARA":
        print(
            "DENY: ITA is an ONÍLẸ̀ administrative command."
        )
        print(
            "Use ONILE first to return from the active YÀRÁ."
        )
        return False

    if SHELL_MODE != "ONILE":
        print(
            "DENY: You are not inside ONÍLẸ̀ administrative mode."
        )
        return False

    if not force:
        confirmed = ask_confirmation(
            "Leave ONÍLẸ̀ administrative mode?"
        )

        if not confirmed:
            print("Remain inside ONÍLẸ̀.")
            return False

    return leave_onile_mode()

def oro_address_mode(start_addr):
    addr = int(start_addr, 0)
    lines = ["BERE\n"]

    print(f"ODÙ Ń GBỌ́ ní adírẹ́sì 0x{addr:02X}.")
    print("DURO = " + VOICE["finished"])

    while True:
        try:
            line = input(f"Ọ̀RỌ̀[0x{addr:02X}]> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return

        lines.append(line + "\n")

        if line.strip().upper() in ("DURO", "DÚRÓ"):
            break

        addr += 1

    tmp = Path("programs_v3/_ohun_oro_buffer.ifa3")
    tmp.write_text("".join(lines), encoding="utf-8")

    run_program(tmp)


def parse_last_frame(stdout):
    frame = {}

    patterns = {
        # Y must come from the explicit PRINTY record.
        # The previous "|^" alternative allowed any bare hexadecimal
        # output line to overwrite Y.
        "Y":  r">>> PRINTY\s*=\s*([0-9a-fA-F]{2})(?:\s+\((\d+)\))?\s*(.*)$",
        "RA": r">>> PRINTRA\s*=\s*([0-9a-fA-F]{2})\s*(.*)$",
        "RD": r">>> PRINTRD\s*=\s*([0-9a-fA-F]{2})\s*(.*)$",
        "R0": r">>> PRINTR0\s*=\s*([0-9a-fA-F]{2})\s*(.*)$",
        "T":  r">>> PRINTT\s*=\s*([0-9a-fA-F]{2})\s*(.*)$",
    }

    for line in stdout.splitlines():
        line = line.strip()

        # PRINTY can appear as "03  ÒDÍ"
        m0 = re.match(r"^([0-9a-fA-F]{2})\s+(.+)$", line)
        if m0 and "Y" not in frame:
            hx = m0.group(1).upper()
            frame["Y"] = {
                "hex": hx,
                "unsigned": int(hx, 16),
                "signed": signed8(int(hx, 16)),
                "odu": m0.group(2).strip(),
            }

        for key, pat in patterns.items():
            m = re.match(pat, line)
            if m:
                hx = m.group(1).upper()
                tail = m.group(3).strip() if key == "Y" and len(m.groups()) >= 3 else m.group(2).strip()
                frame[key] = {
                    "hex": hx,
                    "unsigned": int(hx, 16),
                    "signed": signed8(int(hx, 16)),
                    "odu": tail,
                }

    return frame


def capture_relation_frame_for_active_yara(
    stdout,
    operation,
):
    """Store the latest operation-aware frame in the active YÀRÁ."""

    if SHELL_MODE != "YARA" or ACTIVE_YARA is None:
        return False

    state = YARA_STATE.get(ACTIVE_YARA)

    if state is None or not state["valid"] or not state["running"]:
        return False

    operation = str(operation).strip().upper()

    valid_operations = {
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

    if operation not in valid_operations:
        return False

    frame = parse_last_frame(stdout)

    required_fields = (
        "Y",
        "RA",
        "RD",
        "R0",
        "T",
    )

    missing_fields = [
        field
        for field in required_fields
        if field not in frame
    ]

    if missing_fields:
        if DISPLAY_MODE == "TRACE":
            print(
                "TRACE: Relation frame not recorded; "
                "missing fields: "
                + ", ".join(missing_fields)
            )

        return False

    recorded = record_yara_relation_frame(
        ACTIVE_YARA,
        operation,
        frame["Y"]["unsigned"],
        frame["RA"]["unsigned"],
        frame["RD"]["unsigned"],
        frame["R0"]["unsigned"],
        frame["T"]["unsigned"],
    )

    if recorded:
        state["execution_count"] += 1

        if DISPLAY_MODE == "TRACE":
            print(
                "TRACE: Relation frame stored in "
                f"YÀRÁ {state['name']}: "
                f"OP={operation} "
                f"Y={frame['Y']['unsigned']:02X} "
                f"RA={frame['RA']['unsigned']:02X} "
                f"RD={frame['RD']['unsigned']:02X} "
                f"R0={frame['R0']['unsigned']:02X} "
                f"T={frame['T']['unsigned']:02X}"
            )

    return recorded

def oyela(english=False):
    if not LAST_STDOUT:
        print("KÒ SÍ ÀBÁJÁDE.")
        return

    frame = parse_last_frame(LAST_STDOUT)

    if not frame:
        print("KÒ SÍ ÀBÁJÁDE.")
        return

    if english:
        print("OYELAA — English Interpretation")
        print("--------------------------------")
        if "Y" in frame:
            y = frame["Y"]
            print(f"Result        : {y['signed']}  (raw 0x{y['hex']}, unsigned {y['unsigned']})")
            if y.get("odu"):
                print(f"Result Odù    : {y['odu']}")

        print()
        print("Relation Frame")
        print("--------------")
        labels = {
            "RA": "Agreement",
            "RD": "Disagreement",
            "R0": "Base/Return",
            "T":  "Transport",
        }
        for k in ("RA", "RD", "R0", "T"):
            if k in frame:
                v = frame[k]
                print(f"{labels[k]:<13}: 0x{v['hex']}  {v.get('odu','')}")

        print()
        print("Meaning")
        print("-------")
        print("OYELAA reads the last IFÁ computation as a human-facing result plus its relation frame.")
        return

    print("OYÈLÁ — ÌTÚMỌ̀ ÀBÁJÁDE")
    print("----------------------")

    if "Y" in frame:
        y = frame["Y"]
        print(f"ÈSÌ / OYÈLÁ : {y['signed']}  (0x{y['hex']})")
        if y.get("odu"):
            print(f"ODÙ          : {y['odu']}")

    print()
    print("ÀWÒRÁN ÌBÁṢẸ̀PỌ̀")
    print("----------------")
    labels = {
        "RA": "FARAPỌ̀",
        "RD": "YÀTỌ̀",
        "R0": "ÌPÌLẸ̀",
        "T":  "GBÉ",
    }
    for k in ("RA", "RD", "R0", "T"):
        if k in frame:
            v = frame[k]
            print(f"{labels[k]:<8}= 0x{v['hex']}  {v.get('odu','')}")

    print()
    print("OYÈLÁ ń ka ohun tí ODÙ ṣe, ó sì ń túmọ̀ rẹ̀ fún ènìyàn.")


def add_history(cmd):
    c = cmd.strip()
    if not c:
        return
    skip = ("ITAN", "ÌTÀN", "TUN", "TÚN", "PADA", "PADÀ", "HELP", "OYELA", "OYÈLÁ", "OYELAA")
    if c.upper().split()[0] in skip:
        return
    OHUN_HISTORY.append(c)

def show_history():
    if not OHUN_HISTORY:
        print("KÒ SÍ ÌTÀN.")
        return

    print("ÌTÀN OHÙN")
    print("---------")
    for i, c in enumerate(OHUN_HISTORY, 1):
        print(f"{i:03d}  {c}")

def repeat_last():
    if not OHUN_HISTORY:
        print("KÒ SÍ Ọ̀RỌ̀ TÍ A LE TÚN ṢE.")
        return
    execute(OHUN_HISTORY[-1])

def return_to_history(n):
    try:
        idx = int(n) - 1
    except ValueError:
        print("PADA nilo nọ́ńbà.")
        return

    if idx < 0 or idx >= len(OHUN_HISTORY):
        print("KÒ SÍ ÌTÀN YẸN.")
        return

    execute(OHUN_HISTORY[idx])


def oro_yara_mode(name):
    key = name.strip().upper()
    if key not in ODU_YARA:
        print(f"KÒ WỌLÉ: {name}")
        print("Lo: YARA OGBE, YARA IWORI, YARA ODI...")
        return

    addr = ODU_YARA[key]
    lines = ["BERE\n"]

    print(f"ODÙ Ń GBỌ́ nínú YÀRÁ {key} (0x{addr:02X}).")
    print("DURO = Ó PARÍ")

    cur = addr
    while True:
        try:
            line = input(f"Ọ̀RỌ̀[{key} 0x{cur:02X}]> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return

        command = line.strip()
        command_upper = command.upper()
        command_parts = command.split()

        # Change YÀRÁ without leaving Ọ̀RỌ̀ mode.
        if (
            len(command_parts) == 2
            and command_parts[0].upper() in ("YARA", "YÀRÁ", "YARO")
        ):
            new_key = command_parts[1].upper()

            if new_key not in ODU_YARA:
                print(f"KÒ WỌLÉ: {command_parts[1]}")
                continue

            key = new_key
            addr = ODU_YARA[key]
            cur = addr

            print(f"ODÙ Ń GBỌ́ nínú YÀRÁ {key} (0x{addr:02X}).")
            continue

        lines.append(line + "\n")

        if command_upper in ("DURO", "DÚRÓ"):
            break

        cur += 1

    tmp = Path("programs_v3/_ohun_oro_buffer.ifa3")
    tmp.write_text("".join(lines), encoding="utf-8")

    run_program(tmp)

def execute(cmd):
    c = cmd.strip()
    if not c:
        return

    HISTORY_LOG.append(c)
    u = c.upper()


    if u in ("TAN", "BABALAWO TAN", "BABALÁWO TAN"):
        globals()["BABALAWO_MODE"] = True
        print("BABALÁWO TAN")
        return

    if u in ("PA", "BABALAWO PA", "BABALÁWO PA"):
        globals()["BABALAWO_MODE"] = False
        globals()["SHELL_MODE"] = "GENERAL"
        globals()["ACTIVE_YARA"] = None

        print("BABALÁWO PA")
        print(
            "Returned to general OHÙN IFÁ shell."
        )
        return

    if u in ("BABALAWO", "BABALÁWO"):
        print(
            "BABALÁWO:",
            "TAN" if BABALAWO_MODE else "PA"
        )
        return

    parts = c.split()

    if u in ("EXIT", "QUIT"):
        raise SystemExit



    if u in ("ITAN", "ÌTÀN", "HISTORY"):
        show_history()
        return

    if u in ("TUN", "TÚN"):
        repeat_last()
        return

    if u.startswith("PADA") or u.startswith("PADÀ"):
        args = c.strip().split()
        if len(args) == 1:
            repeat_last()
        elif len(args) == 2:
            return_to_history(args[1])
        else:
            print("PADA n")
        return

    if u in ("OYELA", "OYÈLÁ"):
        oyela(False)
        return

    if u == "OYELAA":
        oyela(True)
        return


    # Wildcard developer commands
    if u == "TAN":
        globals()["BABALAWO_MODE"] = True
        print("BABALÁWO TAN")
        return

    if u == "PA":
        globals()["BABALAWO_MODE"] = False
        print("BABALÁWO PA")
        return

    if u == "HELP":
        print(HELP)
        return

    if u == "VERSION":
        print_version()
        return

    if u == "STATE":
        print_state()
        return

    if u == "HISTORY":
        print_history()
        return

    if u == "CLEAR":
        clear_screen()
        return

    if u == "TIME":
        print_time()
        return

    if u == "MODE CLEAN":
        globals()["DISPLAY_MODE"] = "CLEAN"
        print("Display mode: CLEAN")
        return

    if u == "MODE TRACE":
        globals()["DISPLAY_MODE"] = "TRACE"
        print("Display mode: TRACE")
        return

    if u in ("DÁIFÁ", "DAIFA"):
        print_daifa()
        return

    if u == "PRINTODU":
        run_macro_program("PRINTODU\nHALT\n", "_monitor_printodu.ifa")
        return

    if u == "PRINTODUALL":
        run_macro_program("PRINTODUALL\nHALT\n", "_monitor_printoduall.ifa")
        return

    if u.startswith("RUN "):
        args = shlex.split(c)
        if len(args) == 2:
            run_program(args[1])
        return


    #--------------------------------------------------------------
    # ONÍLẸ̀ administrative shorthand
    #
    # Inside ONÍLẸ̀:
    #
    #     DA OGBE
    #     PARUN OGBE
    #     PARUN OGBE TARA
    #     WO
    #
    # are aliases for:
    #
    #     ONILE DA OGBE
    #     ONILE PARUN OGBE
    #     ONILE PARUN OGBE TARA
    #     ONILE WO
    #--------------------------------------------------------------

    if SHELL_MODE == "ONILE":
        if u.startswith("DA "):
            args = shlex.split(c)

            if len(args) != 2:
                print("Lo: DA OGBE")
                return

            onile_create_yara(args[1])
            return

        if u.startswith("PARUN "):
            args = shlex.split(c)

            if len(args) not in (2, 3):
                print("Lo: PARUN OGBE")
                print("tabi: PARUN OGBE TARA")
                return

            force = False

            if len(args) == 3:
                if args[2].upper() != "TARA":
                    print("Lo: PARUN OGBE TARA")
                    return

                force = True

            onile_destroy_yara(
                args[1],
                force=force
            )
            return

        # PA is reserved exclusively for Babaláwo mode.
        if u == "PA" or u.startswith("PA "):
            print(f"KÒ WỌLÉ: {c}")
            print("PA belongs only to BABALÁWO.")
            print("Lo: PARUN OGBE")
            print("tabi: PARUN OGBE TARA")
            return

        if u == "WO":
            onile_show_status()
            return

    #--------------------------------------------------------------
    # V4 inter-YÀRÁ delegation administration
    #
    # PIN <source> <destination>
    #     Grant directional permission.
    #
    # FAGILE <source> <destination>
    #     Revoke directional permission.
    #
    # SHARE <source> <destination>
    #     Import the source relation frame into the destination.
    #
    # ASE
    #     Show current delegation permissions.
    #--------------------------------------------------------------

    if SHELL_MODE == "ONILE":
        if u.startswith("PIN "):
            args = shlex.split(c)

            if len(args) != 3:
                print("Lo: PIN OGBE OYEKU")
                return

            onile_grant_delegation(
                args[1],
                args[2],
            )
            return

        if u.startswith("FAGILE "):
            args = shlex.split(c)

            if len(args) != 3:
                print("Lo: FAGILE OGBE OYEKU")
                return

            onile_revoke_delegation(
                args[1],
                args[2],
            )
            return

        if u.startswith("SHARE "):
            args = shlex.split(c)

            if len(args) != 3:
                print("Lo: SHARE OGBE OYEKU")
                return

            onile_share_relation_frame(
                args[1],
                args[2],
            )
            return

        if u in (
            "ASE",
            "ÀṢẸ",
            "PERMISSIONS",
        ):
            show_delegation_permissions()
            return

    #--------------------------------------------------------------
    # Symbolic relation-frame calculations
    #
    # Examples:
    #
    #     Y+1
    #     RD-2
    #     RA*4
    #     T==0
    #
    # The symbol explicitly selects the native operation.
    #--------------------------------------------------------------

    symbolic_frame_text = c.strip().replace(" ", "")

    symbolic_frame_match = re.fullmatch(
        r"(Y|RA|RD|R0|T)"
        r"(==|\+|-|\*|/|%|\^|>|<)"
        r"(0x[0-9a-fA-F]+|\d+)",
        symbolic_frame_text,
        flags=re.IGNORECASE,
    )

    if symbolic_frame_match:
        symbolic_frame_operations = {
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

        frame_field = symbolic_frame_match.group(1).upper()
        frame_symbol = symbolic_frame_match.group(2)
        frame_value = symbolic_frame_match.group(3)

        calculate_from_loaded_frame(
            symbolic_frame_operations[frame_symbol],
            frame_field,
            frame_value,
        )
        return

    # Reuse the operation identity stored in the loaded frame.
    #
    # Example:
    #
    #     FRAME Y ATI 6
    #
    # becomes:
    #
    #     <loaded OP> <loaded Y> ATI 6
    #
    if u.startswith("FRAME "):
        args = shlex.split(c)

        if (
            len(args) == 4
            and args[2].upper() == "ATI"
            and args[1].upper() in ("Y", "RA", "RD", "R0", "T")
        ):
            calculate_from_loaded_frame(
                "AUTO",
                args[1],
                args[3],
            )
            return

    if (
        u.startswith("FRAME PAPO ")
        or u.startswith("FRAME YO ")
        or u.startswith("FRAME DAGBA ")
        or u.startswith("FRAME PIN ")
        or u.startswith("FRAME KU ")
        or u.startswith("FRAME GBE ")
        or u.startswith("FRAME SEDA ")
        or u.startswith("FRAME JU ")
        or u.startswith("FRAME KERE ")
    ):
        args = shlex.split(c)

        if len(args) != 4:
            print("Lo: ONILE PIN OGBE OYEKU")
            return

        onile_grant_delegation(
            args[2],
            args[3],
        )
        return

    if (
        u.startswith("FRAME PAPO ")
        or u.startswith("FRAME YO ")
        or u.startswith("FRAME DAGBA ")
        or u.startswith("FRAME PIN ")
        or u.startswith("FRAME KU ")
        or u.startswith("FRAME GBE ")
        or u.startswith("FRAME SEDA ")
        or u.startswith("FRAME JU ")
        or u.startswith("FRAME KERE ")
    ):
        args = shlex.split(c)

        if len(args) != 4:
            print("Lo: ONILE FAGILE OGBE OYEKU")
            return

        onile_revoke_delegation(
            args[2],
            args[3],
        )
        return

    if (
        u.startswith("FRAME PAPO ")
        or u.startswith("FRAME YO ")
        or u.startswith("FRAME DAGBA ")
        or u.startswith("FRAME PIN ")
        or u.startswith("FRAME KU ")
        or u.startswith("FRAME GBE ")
        or u.startswith("FRAME SEDA ")
        or u.startswith("FRAME JU ")
        or u.startswith("FRAME KERE ")
    ):
        args = shlex.split(c)

        if len(args) != 4:
            print("Lo: ONILE SHARE OGBE OYEKU")
            return

        onile_share_relation_frame(
            args[2],
            args[3],
        )
        return

    if u in (
        "ONILE ASE",
        "ONÍLẸ̀ ASE",
        "ONILE ÀṢẸ",
        "ONÍLẸ̀ ÀṢẸ",
    ):
        show_delegation_permissions()
        return

    #--------------------------------------------------------------
    # V4 ONÍLẸ̀ lifecycle administration
    #
    # ONILE DA <name>
    #     Create and start a YÀRÁ.
    #
    # ONILE PARUN <name>
    #     Destroy and clear a YÀRÁ.
    #
    # ONILE WO
    #     Display kernel lifecycle status.
    #--------------------------------------------------------------

    if (
        u.startswith("FRAME PAPO ")
        or u.startswith("FRAME YO ")
        or u.startswith("FRAME DAGBA ")
        or u.startswith("FRAME PIN ")
        or u.startswith("FRAME KU ")
        or u.startswith("FRAME GBE ")
        or u.startswith("FRAME SEDA ")
        or u.startswith("FRAME JU ")
        or u.startswith("FRAME KERE ")
    ):
        args = shlex.split(c)

        if len(args) != 3:
            print("Lo: ONILE DA OGBE")
            return

        onile_create_yara(args[2])
        return

    if (
        u.startswith("FRAME PAPO ")
        or u.startswith("FRAME YO ")
        or u.startswith("FRAME DAGBA ")
        or u.startswith("FRAME PIN ")
        or u.startswith("FRAME KU ")
        or u.startswith("FRAME GBE ")
        or u.startswith("FRAME SEDA ")
        or u.startswith("FRAME JU ")
        or u.startswith("FRAME KERE ")
    ):
        args = shlex.split(c)

        if len(args) not in (3, 4):
            print("Lo: ONILE PARUN OGBE")
            print("tabi: ONILE PARUN OGBE TARA")
            return

        force = False

        if len(args) == 4:
            if args[3].upper() != "TARA":
                print("Lo: ONILE PARUN OGBE TARA")
                return

            force = True

        onile_destroy_yara(
            args[2],
            force=force
        )
        return

    if u in (
        "ONILE WO",
        "ONÍLẸ̀ WO",
    ):
        onile_show_status()
        return

    #--------------------------------------------------------------
    # V4 ONÍLẸ̀ exit commands
    #
    # ITA
    #     Ask before leaving ONÍLẸ̀.
    #
    # ITA TARA
    #     Leave immediately without confirmation.
    #--------------------------------------------------------------

    if u == "ITA":
        ita_leave_onile(force=False)
        return

    if u == "ITA TARA":
        ita_leave_onile(force=True)
        return

    #--------------------------------------------------------------
    # V4 shell transitions
    #
    # GENERAL --ONILE--> ONILE requires Babaláwo.
    # YARA    --ONILE--> ONILE returns to administration.
    # ONILE   --PADA----> GENERAL.
    #--------------------------------------------------------------

    if u in ("ONILE", "ONÍLẸ̀"):
        enter_onile_mode()
        return

    if u in ("PADA", "PADÀ"):
        if SHELL_MODE in ("ONILE", "YARA"):
            leave_onile_mode()
            return

    #--------------------------------------------------------------
    # V4 YÀRÁ inspection commands
    #
    # These must appear before the generic "YARA <name>" handler.
    #--------------------------------------------------------------

    if u in (
        "YARA WO",
        "YÀRÁ WO",
        "YARO WO",
    ):
        if SHELL_MODE != "ONILE":
            print(
                "DENY: Enter ONÍLẸ̀ administrative mode first."
            )
            return

        show_current_yara()
        return

    if u in (
        "YARA GBOGBO",
        "YÀRÁ GBOGBO",
        "YARO GBOGBO",
    ):
        if SHELL_MODE != "ONILE":
            print(
                "DENY: YÀRÁ registry is an ONÍLẸ̀ "
                "administrative service."
            )
            return

        list_yara()
        return

    #--------------------------------------------------------------
    # V4 relation-frame calculation commands
    #
    # FRAME WO
    #     Show current and loaded frames.
    #
    # FRAME LO
    #     Copy the current frame into the stable calculation frame.
    #
    # FRAME PAPO Y ATI 6
    # FRAME YO RD ATI 2
    # FRAME SEDA RA ATI 4
    #--------------------------------------------------------------

    if u in (
        "FRAME WO",
        "FIREEMU WO",
    ):
        show_current_frame()
        return

    if u in (
        "FRAME LO",
        "FIREEMU LO",
    ):
        load_current_frame()
        return

    if (
        u.startswith("FRAME PAPO ")
        or u.startswith("FRAME YO ")
        or u.startswith("FRAME DAGBA ")
        or u.startswith("FRAME PIN ")
        or u.startswith("FRAME KU ")
        or u.startswith("FRAME GBE ")
        or u.startswith("FRAME SEDA ")
        or u.startswith("FRAME JU ")
        or u.startswith("FRAME KERE ")
    ):
        args = shlex.split(c)

        if len(args) != 5 or args[3].upper() != "ATI":
            print("Lo: FRAME PAPO Y ATI 6")
            print("Fields: Y RA RD R0 T")
            return

        calculate_from_loaded_frame(
            args[1],
            args[2],
            args[4],
        )
        return

    #--------------------------------------------------------------
    # Special YÀRÁ commands
    #
    # These must be checked before generic YARA <name> selection.
    #--------------------------------------------------------------

    if u in (
        "YARA STATS",
        "YÀRÁ STATS",
        "YARO STATS",
    ):
        if SHELL_MODE != "YARA" or ACTIVE_YARA is None:
            print(
                "DENY: YARA STATS requires an active YÀRÁ."
            )
            print(
                "Select a created YÀRÁ from ONÍLẸ̀ first."
            )
            return

        show_yara_stats()
        return

    if u in (
        "YARA SUN",
        "YÀRÁ SUN",
        "YARO SUN",
    ):
        if SHELL_MODE != "YARA" or ACTIVE_YARA is None:
            print(
                "DENY: YARA SUN requires an active YÀRÁ."
            )
            return

        pause_active_yara()
        return

    if (
        u.startswith("FRAME PAPO ")
        or u.startswith("FRAME YO ")
        or u.startswith("FRAME DAGBA ")
        or u.startswith("FRAME PIN ")
        or u.startswith("FRAME KU ")
        or u.startswith("FRAME GBE ")
        or u.startswith("FRAME SEDA ")
        or u.startswith("FRAME JU ")
        or u.startswith("FRAME KERE ")
    ):
        if SHELL_MODE != "ONILE":
            print(
                "DENY: YARA JI is an ONÍLẸ̀ "
                "administrative command."
            )
            print(
                "Use ONILE first to return from the active YÀRÁ."
            )
            return

        args = shlex.split(c)

        if len(args) != 3:
            print("Lo: YARA JI OGBE")
            return

        resume_yara(args[2])
        return

    if u == "DURO" and SHELL_MODE == "YARA":
        print(
            "DURO exits only the inner Ọ̀RỌ̀ programming prompt."
        )
        print(
            "Use ONILE to leave the active YÀRÁ."
        )
        return

    #--------------------------------------------------------------
    # V4 YÀRÁ selection
    #
    # YARA OGBE selects an execution context.
    #--------------------------------------------------------------

    if (
        u.startswith("YARA ")
        or u.startswith("YÀRÁ ")
        or u.startswith("YARO ")
    ):
        args = shlex.split(c)

        if len(args) == 2:
            select_yara(args[1])
        else:
            print("Lo: YARA OGBE")

        return

    #--------------------------------------------------------------
    # V4 Ọ̀RỌ̀ programming mode
    #
    # ORO enters programming mode inside the currently selected
    # YÀRÁ.
    #--------------------------------------------------------------

    if u in ("ORO", "Ọ̀RỌ̀"):
        if SHELL_MODE != "YARA" or ACTIVE_YARA is None:
            print("DENY: No active YÀRÁ execution mode.")
            print(
                "Use: BABALAWO TAN → ONILE → YARA OGBE"
            )
            return

        oro_yara_mode(active_yara_name())
        return

    if u.startswith("BERE "):
        args = shlex.split(c)
        if len(args) == 2:
            if args[1].lower().startswith("0x") or args[1].isdigit():
                oro_address_mode(args[1])
            else:
                run_program(args[1])
        return

    if len(parts) == 4 and parts[0].upper() == "IFA":
        op = parts[1].upper()
        if op in ("ADD", "SUB", "MUL", "DIV", "MOD", "EXP"):
            ifa_arithmetic(op, parts[2], parts[3])
            return
        if op in ("AGREE", "DISAGREE", "TOGGLE", "TRANSPORT", "PHI"):
            ifa_relation(op, parts[2], parts[3])
            return

    if u.startswith("BENCHMARK ") or u.startswith("PCM "):
        v3_placeholder(u)
        return

    # Natural Yorùbá V3 command inside IFÁ OS
    first = parts[0].upper() if parts else ""
    if first in ("PAPO", "PÀPỌ̀", "YO", "YỌ", "DAGBA", "DÁGBA", "PIN", "KU", "KÙ", "GBE", "GBÉ", "SEDA", "ṢẸ̀DÁ", "JU", "JÙ", "KERE", "KERÉ"):
        add_history(c)
        run_yoruba_line(normalize_symbolic_oro(c))
        return

    # IFÁ V3 natural Yorùbá / symbol expression inside IFÁ OS
    v3_first = parts[0].upper() if parts else ""
    v3_words = ("PAPO", "PÀPỌ̀", "YO", "YỌ", "DAGBA", "DÁGBA", "PIN", "KU", "KÙ", "GBE", "GBÉ", "SEDA", "ṢẸ̀DÁ", "JU", "JÙ", "KERE", "KERÉ")
    v3_symbols = ("+", "-", "*", "/", "%", "^")

    if v3_first in v3_words or any(sym in c for sym in v3_symbols):
        add_history(c)
        run_yoruba_line(normalize_symbolic_oro(c))
        return

    if "+" in c or "-" in c:
        run_expression(c)
        return

    print(f"{VOICE['unknown']}: {c}")

def main():
    boot()
    while True:
        try:
            execute(input(monitor_prompt()))
        except (EOFError, KeyboardInterrupt):
            print()
            break
        except SystemExit:
            break
    print(VOICE["goodbye"])

if __name__ == "__main__":
    main()
