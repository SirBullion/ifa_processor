#!/usr/bin/env python3

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

def aa_inv_pair(anchor, agreement):
    a = anchor
    b = anchor if agreement else 1 - anchor
    return a, b

def aa8(x):
    bs = bits(x, 8)
    out = []
    for i in range(0, 8, 2):
        out.extend(aa_pair(bs[i], bs[i+1]))
    return to_int(out)

def aa8_inv(y):
    bs = bits(y, 8)
    out = []
    for i in range(0, 8, 2):
        out.extend(aa_inv_pair(bs[i], bs[i+1]))
    return to_int(out)

def anchors(x):
    bs = bits(x, 8)
    return [bs[0], bs[2], bs[4], bs[6]]

def agreements(x):
    y = aa8(x)
    bs = bits(y, 8)
    return [bs[1], bs[3], bs[5], bs[7]]

def replace_agreements(x, new_agreements):
    y = aa8(x)
    bs = bits(y, 8)

    bs[1] = new_agreements[0]
    bs[3] = new_agreements[1]
    bs[5] = new_agreements[2]
    bs[7] = new_agreements[3]

    return aa8_inv(to_int(bs))

def flip_all_agreements(x):
    ag = agreements(x)
    return replace_agreements(x, [1-a for a in ag])

def force_agreement(x):
    return replace_agreements(x, [1,1,1,1])

def force_disagreement(x):
    return replace_agreements(x, [0,0,0,0])

print("=" * 90)
print("ANCHOR–AGREEMENT NATURAL OPERATIONS AUDIT")
print("=" * 90)

print()
print("x        anchors agreements  flip_agree  force_agree force_disagree")
print("-" * 90)

for x in [0x00,0x01,0x02,0x03,0x55,0xAA,0xA5,0xFF]:
    print(
        bstr(x),
        anchors(x),
        agreements(x),
        bstr(flip_all_agreements(x)),
        bstr(force_agreement(x)),
        bstr(force_disagreement(x)),
    )

print()
print("=" * 90)
print("INTERPRETATION")
print("=" * 90)

print("""
In Anchor–Agreement space, the natural operations are not ordinary arithmetic.

Examples:

1. flip_all_agreements(x)
   Keeps the anchor stream A C E G unchanged.
   Inverts every agreement relation.

2. force_agreement(x)
   Keeps anchors unchanged.
   Forces each pair to agree:
       AB -> AA
       CD -> CC
       EF -> EE
       GH -> GG

3. force_disagreement(x)
   Keeps anchors unchanged.
   Forces each pair to disagree:
       AB -> A~A
       CD -> C~C
       EF -> E~E
       GH -> G~G

These are relation-space operations.
They are different from ADD/SUB because they operate on agreement structure,
not numeric magnitude.
""")
