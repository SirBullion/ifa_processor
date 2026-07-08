#!/usr/bin/env python3

# --- IFÁ project import bootstrap ---
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# -----------------------------------

import os
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
DISPLAY_MODE = "CLEAN"
LAST_STDOUT = ""
OHUN_HISTORY = []
globals()["BABALAWO_MODE"] = False

LAST_RUN_TIME = {"assemble": 0.0, "compile": 0.0, "execute": 0.0, "total": 0.0}

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

Bẹrẹ Ọ̀rọ̀ ní adírẹ́sì
----------------------
BERE 0x00

Example:
BERE 0x00
Ọ̀RỌ̀[0x00]> PAPO META ATI MEJI
Ọ̀RỌ̀[0x01]> TE ODU
Ọ̀RỌ̀[0x02]> DURO

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

    m = re.fullmatch(r"(0x[0-9a-fA-F]+|\d+)\+(0x[0-9a-fA-F]+|\d+)", text)
    if m:
        return f"PAPO {m.group(1)} ATI {m.group(2)}"

    m = re.fullmatch(r"(0x[0-9a-fA-F]+|\d+)\-(0x[0-9a-fA-F]+|\d+)", text)
    if m:
        return f"YO {m.group(1)} ATI {m.group(2)}"

    return c

def run_yoruba_line(line):
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


def oro_address_mode(start_addr):
    addr = int(start_addr, 0)
    lines = ["BERE\n"]

    print(f"ODÙ is listening from address 0x{addr:02X}.")
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
        "Y":  r"(?:>>> PRINTY\s*=\s*|^)([0-9a-fA-F]{2})(?:\s+\((\d+)\))?\s*(.*)$",
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

def execute(cmd):
    c = cmd.strip()
    if not c:
        return

    HISTORY_LOG.append(c)
    u = c.upper()

    if u in ("TAN", "BABALAWO TAN", "BABALÁWO TAN"):
        globals()["BABALAWO_MODE"] = True
        globals()["DISPLAY_MODE"] = "TRACE"
        print("BABALÁWO TAN")
        return

    if u in ("PA", "BABALAWO PA", "BABALÁWO PA"):
        globals()["BABALAWO_MODE"] = False
        globals()["DISPLAY_MODE"] = "CLEAN"
        print("BABALÁWO PA")
        return

    if u in ("BABALAWO", "BABALÁWO"):
        print("BABALÁWO:", "TAN" if DISPLAY_MODE == "TRACE" else "PA")
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
        globals()["DISPLAY_MODE"] = "TRACE"
        print("BABALÁWO TAN")
        return

    if u == "PA":
        globals()["BABALAWO_MODE"] = False
        globals()["DISPLAY_MODE"] = "CLEAN"
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
    if first in ("PAPO", "PÀPỌ̀", "YO", "YỌ", "SEDA", "ṢẸ̀DÁ"):
        add_history(c)
        run_yoruba_line(normalize_symbolic_oro(c))
        return

    # IFÁ V3 natural Yorùbá / symbol expression inside IFÁ OS
    v3_first = parts[0].upper() if parts else ""
    v3_words = ("PAPO", "PÀPỌ̀", "YO", "YỌ", "SEDA", "ṢẸ̀DÁ", "GBA")
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
            execute(input("OHÙN IFÁ> "))
        except (EOFError, KeyboardInterrupt):
            print()
            break
        except SystemExit:
            break
    print(VOICE["goodbye"])

if __name__ == "__main__":
    main()
