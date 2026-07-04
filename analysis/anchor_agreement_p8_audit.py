#!/usr/bin/env python3

def bstr(x):
    return format(x, "08b")

def bits(x):
    return [(x >> i) & 1 for i in reversed(range(8))]

def to_int(bs):
    y = 0
    for b in bs:
        y = (y << 1) | b
    return y

def aa_gate(a, b):
    anchor = a
    agreement = 1 if a == b else 0
    return anchor, agreement

def aa_inv(anchor, agreement):
    a = anchor
    b = anchor if agreement == 1 else 1 - anchor
    return a, b

def aa_p8(x):
    bs = bits(x)
    out = []
    for i in range(0, 8, 2):
        out.extend(aa_gate(bs[i], bs[i+1]))
    return to_int(out)

def aa_p8_inv(y):
    bs = bits(y)
    out = []
    for i in range(0, 8, 2):
        out.extend(aa_inv(bs[i], bs[i+1]))
    return to_int(out)

failures = 0

print("=" * 80)
print("ANCHOR–AGREEMENT P8 AUDIT")
print("=" * 80)
print("x        mapped    recovered")
print("-" * 80)

for x in range(256):
    y = aa_p8(x)
    xr = aa_p8_inv(y)

    if x < 16:
        print(f"{bstr(x)} {bstr(y)} {bstr(xr)}")

    if xr != x:
        failures += 1

print("-" * 80)
print("Total states:", 256)
print("Recovery failures:", failures)

if failures == 0:
    print("PASS: 8-bit Anchor–Agreement transform is reversible.")
else:
    print("FAIL.")
