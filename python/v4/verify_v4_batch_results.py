import re
import sys

MASK = 0xFF

pattern = re.compile(
    r"RESULT A=([0-9a-fA-F]+) B=([0-9a-fA-F]+) "
    r"Y=([0-9a-fA-F]+) RA=([0-9a-fA-F]+) RD=([0-9a-fA-F]+) "
    r"R0=([0-9a-fA-F]+) T=([0-9a-fA-F]+)"
)

def py_frame(a, b):
    y  = (a + b) & MASK
    ra = a & b
    rd = a ^ b
    r0 = (~(a | b)) & MASK
    t  = rd ^ y
    return y, ra, rd, r0, t

checked = 0

with open("sim/v4/v4_rtl_exhaustive_results.txt") as f:
    for line in f:
        m = pattern.search(line)
        if not m:
            continue

        a = int(m.group(1), 16)
        b = int(m.group(2), 16)

        actual = tuple(int(m.group(i), 16) for i in range(3, 8))
        expected = py_frame(a, b)

        if actual != expected:
            print("FAIL")
            print(f"A={a:02X} B={b:02X}")
            print("expected:", expected)
            print("actual  :", actual)
            sys.exit(1)

        checked += 1

print("IFÁ V4 BATCH RTL vs PYTHON EQUIVALENCE")
print("=" * 70)
print("pairs checked:", checked)
print("failures:", 0)

if checked != 65536:
    print("FAIL: expected 65536 pairs")
    sys.exit(1)

print("PASS: batch RTL results match Python model")
