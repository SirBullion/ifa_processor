#!/usr/bin/env python3

def bits(x, n=8):
    return [(x >> i) & 1 for i in reversed(range(n))]

def to_int(bs):
    y = 0
    for b in bs:
        y = (y << 1) | b
    return y

def bstr(x):
    return format(x, "08b")

def p2(a, b):
    # A' = A
    # B' = NOT(A XOR B)
    return a, 1 ^ (a ^ b)

def p8(x):
    bs = bits(x, 8)
    out = []
    for i in range(0, 8, 2):
        out.extend(p2(bs[i], bs[i + 1]))
    return to_int(out)

def p8_inv(y):
    # current P8 is self-inverse
    return p8(y)

failures = 0

print("=" * 80)
print("TEST 1 — CIPHERTEXT LEAKAGE / READABILITY")
print("=" * 80)
print("Question: If attacker sees y = P8(x), can they recover x?")
print()

print("sample:")
print("x        y=P8(x)   recovered=P8(y)")
print("-" * 40)

for x in range(256):
    y = p8(x)
    xr = p8_inv(y)

    if x < 16:
        print(f"{bstr(x)} {bstr(y)} {bstr(xr)}")

    if xr != x:
        failures += 1

print()
print("Total states:", 256)
print("Recovery failures:", failures)

if failures == 0:
    print()
    print("RESULT:")
    print("P8 is fully reversible. Anyone who knows P8 can recover x from y.")
    print("Conclusion: P8 alone is NOT encryption.")
else:
    print("Unexpected: recovery failed for some states.")
