#!/usr/bin/env python3

from collections import Counter

def bstr(x, n=8):
    return format(x, f"0{n}b")

def bits(x, n=8):
    return [(x >> i) & 1 for i in reversed(range(n))]

def to_int(bs):
    y = 0
    for b in bs:
        y = (y << 1) | b
    return y

def aa_pair(a, b):
    anchor = a
    agreement = 1 if a == b else 0
    return anchor, agreement

def aa_transform_bits(bs):
    out = []
    for i in range(0, len(bs), 2):
        out.extend(aa_pair(bs[i], bs[i+1]))
    return out

def apply_levels(x, levels=4):
    bs = bits(x, 8)
    states = [bs]

    for _ in range(levels):
        bs = aa_transform_bits(bs)
        states.append(bs)

    return states

def state_str(bs):
    return "".join(str(b) for b in bs)

print("=" * 90)
print("RECURSIVE ANCHOR–AGREEMENT AUDIT")
print("=" * 90)

print()
print("Sample recursive paths:")
print("x        L0        L1        L2        L3        L4")
print("-" * 90)

for x in range(16):
    states = apply_levels(x, 4)
    print(
        f"{bstr(x)} "
        + " ".join(f"{state_str(s):<8}" for s in states)
    )

print()
print("=" * 90)
print("CYCLE STRUCTURE UNDER REPEATED ANCHOR–AGREEMENT")
print("=" * 90)

visited = set()
cycles = []

def aa8(x):
    return to_int(aa_transform_bits(bits(x, 8)))

for x in range(256):
    if x in visited:
        continue

    path = []
    cur = x

    while cur not in path:
        path.append(cur)
        visited.add(cur)
        cur = aa8(cur)

    cycles.append(path)

profile = Counter(len(c) for c in cycles)

print("cycle count:", len(cycles))
print("cycle length profile:", dict(profile))

print()
print("first cycles:")
for c in cycles[:20]:
    print(" -> ".join(bstr(v) for v in c))

print()
print("=" * 90)
print("FIXED STATES")
print("=" * 90)

fixed = [x for x in range(256) if aa8(x) == x]
print("fixed count:", len(fixed))
for x in fixed:
    print(bstr(x))

print()
print("=" * 90)
print("INTERPRETATION")
print("=" * 90)
print("""
The recursive test asks whether repeatedly applying the Anchor–Agreement
mapping creates a hierarchy.

If the transform has order 2, then:

    L0 -> L1 -> L0 -> L1 ...

This means the mapping is an involution: a reversible coordinate swap between
raw bit-pair space and anchor/agreement space.

If longer cycles appear, then recursive application reveals deeper hierarchy.
""")
