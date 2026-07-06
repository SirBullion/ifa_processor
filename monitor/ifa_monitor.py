#!/usr/bin/env python3
import os
import shlex
import subprocess
import time
from pathlib import Path

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
LAST_RUN_TIME = {"assemble": 0.0, "compile": 0.0, "execute": 0.0, "total": 0.0}

HELP = """
IFÁ Monitor Commands
--------------------

Arithmetic
----------
IFA ADD A B
IFA SUB A B
IFA MUL A B
IFA DIV A B
IFA MOD A B
IFA EXP A B

Relations
---------
IFA AGREE A B
IFA DISAGREE A B
IFA TOGGLE A B
IFA TRANSPORT A B
IFA PHI A B

Knowledge
---------
DÁIFÁ
DAIFA
PRINTODU
PRINTODUALL

Program
-------
RUN <program.ifa>

System
------
HELP
VERSION
STATE
HISTORY
CLEAR
TIME
EXIT
QUIT

V3 Reserved
-----------
PCM WRITE A B
PCM READ RA RD T
PCM SEARCH RA RD T
PCM STATS

BENCHMARK MATRIX
BENCHMARK ROBOT
BENCHMARK EXPDIV
BENCHMARK ALL
"""

BANNER = """
═══════════════════════════════════════════════════════════════════════
                     IFÁ ODU PROCESSOR
═══════════════════════════════════════════════════════════════════════

Version      : 2.0
Core         : Relation Processor Core (RPC)
Architecture : ODU V2
Monitor      : IFÁ OS v0

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
        "Loading IFÁ Monitor",
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
    print("IFÁ PROCESSOR STATE")
    print("-------------------")
    print("STATE is monitor-level in v0.")
    print("Use PRINTODUALL or RUN a program with PRINTODUALL for live CPU state.")

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

def run_program(path):
    program = Path(path)
    if not program.exists():
        print(f"File not found: {program}")
        return

    t0 = time.perf_counter()

    print(f"[ASSEMBLE] {program}")
    a0 = time.perf_counter()
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
    result = subprocess.run(["vvp", "sim/ifa_monitor_run.out"], check=True, text=True, capture_output=True)
    e1 = time.perf_counter()

    print(result.stdout, end="")

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

def execute(cmd):
    c = cmd.strip()
    if not c:
        return

    HISTORY_LOG.append(c)
    u = c.upper()
    parts = c.split()

    if u in ("EXIT", "QUIT"):
        raise SystemExit

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

    if "+" in c or "-" in c:
        run_expression(c)
        return

    print("Unknown command:", c)

def main():
    boot()
    while True:
        try:
            execute(input("IFÁ> "))
        except (EOFError, KeyboardInterrupt):
            print()
            break
        except SystemExit:
            break
    print("ỌDÀBỌ̀.")

if __name__ == "__main__":
    main()
