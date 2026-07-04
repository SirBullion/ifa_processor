#!/usr/bin/env python3

from collections import Counter, defaultdict

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

def pair_anchor_bits(x):
    bs = bits(x, 8)
    return (bs[0], bs[2], bs[4], bs[6])

def pair_relation_bits(x):
    bs = bits(x, 8)
    return (
        bs[0] ^ bs[1],
        bs[2] ^ bs[3],
        bs[4] ^ bs[5],
        bs[6] ^ bs[7],
    )

def second_bits(x):
    bs = bits(x, 8)
    return (bs[1], bs[3], bs[5], bs[7])

def nibble_pair(x):
    return (x >> 4, x & 0xF)

def odu_index_pair(x):
    return nibble_pair(x)

print("=" * 100)
print("IFÁ BASIS / REPRESENTATION AUDIT")
print("=" * 100)

print()
print("Sample mapping:")
print("x        P8(x)    anchors(x) relations(x) second_bits(x) anchors(P8) second_bits(P8)")
print("-" * 100)

for x in range(16):
    y = p8(x)
    print(
        bstr(x),
        bstr(y),
        pair_anchor_bits(x),
        pair_relation_bits(x),
        second_bits(x),
        pair_anchor_bits(y),
        second_bits(y),
    )

print()
print("=" * 100)
print("ANCHOR PRESERVATION")
print("=" * 100)

anchor_fail = []
relation_to_output_second_fail = []

for x in range(256):
    y = p8(x)

    if pair_anchor_bits(x) != pair_anchor_bits(y):
        anchor_fail.append((x, y))

    # For P2:
    # B' = NOT(A XOR B)
    # second output bit equals NOT(relation bit)
    rel = pair_relation_bits(x)
    sec_y = second_bits(y)
    expected_sec_y = tuple(1 ^ r for r in rel)

    if sec_y != expected_sec_y:
        relation_to_output_second_fail.append((x, y, rel, sec_y, expected_sec_y))

print("anchor failures:", len(anchor_fail))
print("relation-to-output-second failures:", len(relation_to_output_second_fail))

print()
print("=" * 100)
print("INTERPRETATION OF P8 SPACE")
print("=" * 100)

print("""
For each 2-bit pair AB:

    anchor  = A
    relation = A XOR B

P2 maps:

    A' = A
    B' = NOT(A XOR B)

So P2 preserves the anchor and writes the negated relationship into the second bit.

Therefore P8 can be interpreted as a coordinate transform:

    original pair coordinates:
        (A, B)

    Ifá pair coordinates:
        (anchor, NOT(relation))

This means P8-space explicitly exposes pair relationship structure.
""")

print()
print("=" * 100)
print("CLASS GROUPING BY ANCHORS")
print("=" * 100)

groups = defaultdict(list)

for x in range(256):
    groups[pair_anchor_bits(x)].append(x)

for anchor, vals in sorted(groups.items()):
    mapped = [p8(v) for v in vals]
    print("anchor", anchor)
    print("  x states :", " ".join(bstr(v) for v in vals[:8]), "...")
    print("  P8 states:", " ".join(bstr(v) for v in mapped[:8]), "...")
    print()

print("=" * 100)
print("ODU NIBBLE EFFECT")
print("=" * 100)

nibble_changes = Counter()

for x in range(256):
    y = p8(x)
    x_pair = odu_index_pair(x)
    y_pair = odu_index_pair(y)
    nibble_changes[(x_pair, y_pair)] += 1

print("unique Odu-pair transitions:", len(nibble_changes))
print("sample Odu-pair transitions:")
for i, ((xp, yp), count) in enumerate(nibble_changes.items()):
    if i >= 20:
        break
    print(f"{xp} -> {yp}: {count}")

print()
print("=" * 100)
print("CONCLUSION")
print("=" * 100)

print("""
P8 is not encryption by itself.

A better interpretation is:

    P8 is a reversible basis transform from raw bit-pairs into
    anchor/relationship coordinates.

The preserved quantity is the anchor stream:

    A C E G

The transformed quantity is the relation stream:

    A⊕B, C⊕D, E⊕F, G⊕H

This supports the view that the Ifá processor is not merely arithmetic-centered.
It is relation-centered: it exposes relational structure between paired bits.
""")
