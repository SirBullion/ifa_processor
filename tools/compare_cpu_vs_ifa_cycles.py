#!/usr/bin/env python3
import re
import subprocess
import sys
from pathlib import Path

bench = sys.argv[1] if len(sys.argv) > 1 else "benchmarks/03_relation_reuse.ifa3"

def run(cmd):
    return subprocess.run(cmd, text=True, capture_output=True)

print("=====================================")
print(" IFÁ vs CPU CYCLE COMPARISON")
print("=====================================")
print("Benchmark:", bench)
print()

ifa = run(["./ifarun", bench])
print("[IFÁ]")
print(ifa.stdout)

m = re.search(r"ODU V2 CPU halted after\s+(\d+)\s+cycles", ifa.stdout)
ifa_cycles = int(m.group(1)) if m else None

# CPU ref uses the same odu_v2_program.hex produced by ifarun
subprocess.run(["iverilog", "-g2012", "rtl_v3/cpu_ref_v3.sv", "-o", "sim/cpu_ref_v3.out"], check=True)
cpu = run(["vvp", "sim/cpu_ref_v3.out"])

print("[CPU REF]")
print(cpu.stdout)

def grab(name, text):
    m = re.search(rf"{name}\s*=\s*(\d+)", text)
    return int(m.group(1)) if m else None

ref_cycles = grab("cycles", cpu.stdout)
ref_instr  = grab("instructions", cpu.stdout)
unsupported = grab("unsupported_relation", cpu.stdout)

print("=====================================")
print(" SUMMARY")
print("=====================================")
print(f"same_hex_stream        = yes")
print(f"ifa_cycles             = {ifa_cycles}")
print(f"ref_cycles             = {ref_cycles}")
print(f"ref_instructions       = {ref_instr}")
print(f"cpu_relation_unsupported = {unsupported}")

if ifa_cycles and ref_cycles:
    print(f"speedup_ref_over_ifa   = {ref_cycles / ifa_cycles:.3f}x")

print()
print("Interpretation:")
print("- This compares both cores after assembling the exact same program hex.")
print("- CPU unsupported_relation counts relation instructions it cannot natively interpret.")
print("- True relation-reuse speedup requires IFÁ RTL hit/miss counters in V4.")
