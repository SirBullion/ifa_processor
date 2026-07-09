import subprocess
import re
import sys

MASK = 0xFF

def py_frame(a, b):
    y  = (a + b) & MASK
    ra = a & b
    rd = a ^ b
    r0 = (~(a | b)) & MASK
    t  = rd ^ y
    return y, ra, rd, r0, t

pattern = re.compile(
    r"RESULT A=([0-9a-fA-F]+) B=([0-9a-fA-F]+) "
    r"Y=([0-9a-fA-F]+) RA=([0-9a-fA-F]+) RD=([0-9a-fA-F]+) "
    r"R0=([0-9a-fA-F]+) T=([0-9a-fA-F]+)"
)

failures = []
checked = 0

for a in range(256):
    for b in range(256):
        result = subprocess.run(
            [
                "vvp",
                "sim/v4/tb_ifa_v4_single_case.out",
                f"+A={a:02X}",
                f"+B={b:02X}",
            ],
            capture_output=True,
            text=True,
        )

        m = pattern.search(result.stdout)

        if not m:
            print("Could not parse RTL output")
            print(result.stdout)
            print(result.stderr)
            sys.exit(1)

        actual = (
            int(m.group(3), 16),
            int(m.group(4), 16),
            int(m.group(5), 16),
            int(m.group(6), 16),
            int(m.group(7), 16),
        )

        expected = py_frame(a, b)

        if expected != actual:
            failures.append((a, b, expected, actual))
            print("FAIL")
            print(f"A={a:02X} B={b:02X}")
            print("expected:", expected)
            print("actual  :", actual)
            sys.exit(1)

        checked += 1

print("IFÁ V4 PYTHON vs RTL EQUIVALENCE")
print("=" * 70)
print("pairs checked:", checked)
print("failures:", len(failures))
print("PASS: RTL matches Python model for all 65,536 input pairs")
