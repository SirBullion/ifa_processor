#!/usr/bin/env python3

from collections import Counter

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
    return a, 1 ^ (a ^ b)

def p8(x):
    bs = bits(x, 8)
    out = []
    for i in range(0, 8, 2):
        out.extend(p2(bs[i], bs[i+1]))
    return to_int(out)

def parity(x):
    return x.bit_count() % 2

def hamming_weight(x):
    return x.bit_count()

def nibble_hi(x):
    return (x >> 4) & 0xF

def nibble_lo(x):
    return x & 0xF

def pair_values(x):
    return [
        (x >> 6) & 0b11,
        (x >> 4) & 0b11,
        (x >> 2) & 0b11,
        x & 0b11,
    ]

def pair_a_bits(x):
    bs = bits(x, 8)
    return [bs[0], bs[2], bs[4], bs[6]]

def pair_b_bits(x):
    bs = bits(x, 8)
    return [bs[1], bs[3], bs[5], bs[7]]

def check_invariant(name, fn):
    failures = []
    for x in range(256):
        y = p8(x)
        if fn(x) != fn(y):
            failures.append((x, y, fn(x), fn(y)))
    return failures

tests = {
    "full value": lambda x: x,
    "parity": parity,
    "hamming_weight": hamming_weight,
    "high_nibble": nibble_hi,
    "low_nibble": nibble_lo,
    "pair_values": pair_values,
    "pair_A_bits": pair_a_bits,
    "pair_B_bits": pair_b_bits,
}

print("=" * 90)
print("IFÁ P8 INVARIANT AUDIT")
print("=" * 90)

for name, fn in tests.items():
    failures = check_invariant(name, fn)
    print(f"{name:<20} invariant: {len(failures) == 0}   failures: {len(failures)}")
    if failures[:5]:
        for x, y, fx, fy in failures[:5]:
            print(f"  {bstr(x)} -> {bstr(y)} | {fx} -> {fy}")

print()
print("=" * 90)
print("PAIR-LEVEL TRANSITION COUNTS")
print("=" * 90)

pair_counter = Counter()

for x in range(256):
    y = p8(x)
    for px, py in zip(pair_values(x), pair_values(y)):
        pair_counter[(px, py)] += 1

for (px, py), count in sorted(pair_counter.items()):
    print(f"{px:02b} -> {py:02b}: {count}")

print()
print("=" * 90)
print("FIXED STATES")
print("=" * 90)

fixed = [x for x in range(256) if p8(x) == x]
print("fixed count:", len(fixed))
print("fixed states:")
for x in fixed:
    print(bstr(x))

print()
print("=" * 90)
print("INTERPRETATION")
print("=" * 90)
print("""
The current P8 applies P2 independently to four bit-pairs.

Per pair:
    A' = A
    B' = NOT(A XOR B)

Therefore:
    - The first bit of each pair is invariant.
    - The second bit of each pair may change.
    - P8 is reversible.
    - P8 is self-inverse.
    - The full state is not generally invariant.
    - Hamming weight and parity are not generally invariant.
    - The invariant structure is pair-anchor preservation.

This means P8 preserves the anchor bits of each pair while transforming the
relation between A and B.
""")
