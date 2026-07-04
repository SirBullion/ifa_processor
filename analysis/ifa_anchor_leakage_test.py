#!/usr/bin/env python3

def bits(x):
    return [(x >> i) & 1 for i in reversed(range(8))]

def to_int(bs):
    y = 0
    for b in bs:
        y = (y << 1) | b
    return y

def bstr(x):
    return format(x, "08b")

def p2(a,b):
    return a, 1 ^ (a ^ b)

def p8(x):
    bs = bits(x)
    out = []
    for i in range(0,8,2):
        out.extend(p2(bs[i], bs[i+1]))
    return to_int(out)

def anchors_from_input(x):
    bs = bits(x)
    return [bs[0], bs[2], bs[4], bs[6]]

def anchors_from_output(y):
    bs = bits(y)
    return [bs[0], bs[2], bs[4], bs[6]]

failures = 0

print("="*70)
print("IFÁ Φ-P8 ANCHOR LEAKAGE TEST")
print("="*70)
print("x        y=P8(x)   input anchors   output anchors")
print("-"*70)

for x in range(256):
    y = p8(x)
    ai = anchors_from_input(x)
    ao = anchors_from_output(y)

    if x < 16:
        print(f"{bstr(x)} {bstr(y)}   {ai}        {ao}")

    if ai != ao:
        failures += 1

print("-"*70)
print("Total states:", 256)
print("Anchor mismatch failures:", failures)

if failures == 0:
    print()
    print("RESULT:")
    print("Anchor bits leak completely through Φ-P8.")
    print("Visible leaked bits: A,C,E,G = 4 of 8 bits.")
    print("Conclusion: Φ-P8 alone provides structure, not confidentiality.")
else:
    print("Unexpected: anchor mismatch found.")
