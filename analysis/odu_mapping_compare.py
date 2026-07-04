#!/usr/bin/env python3

ODU = [
    "Ògbè", "Ògúndá", "Ìretẹ̀", "Ìròsùn",
    "Òtúrá", "Òsé", "Òdí", "Òbàrà",
    "Òsá", "Ìwòrì", "Òfún", "Ìká",
    "Òwónrín", "Òtúrúpọn", "Òkànràn", "Òyèkú"
]

def b8(x):
    return format(x, "08b")

def odu_pair(x):
    return f"{ODU[(x >> 4) & 0xF]} {ODU[x & 0xF]}"

def force_agreement(x):
    y = 0
    for shift in [6,4,2,0]:
        a = (x >> (shift+1)) & 1
        y |= a << (shift+1)
        y |= a << shift
    return y

def force_disagreement(x):
    y = 0
    for shift in [6,4,2,0]:
        a = (x >> (shift+1)) & 1
        y |= a << (shift+1)
        y |= (1-a) << shift
    return y

def flip_agreement(x):
    return x ^ 0x55

def anchors(x):
    return "".join(str((x >> i) & 1) for i in [7,5,3,1])

def agreements(x):
    out = []
    for shift in [6,4,2,0]:
        a = (x >> (shift+1)) & 1
        b = (x >> shift) & 1
        out.append("1" if a == b else "0")
    return "".join(out)

tests = [0xA5, 0xFF, 0x00, 0x55, 0xAA]

print("="*110)
print("OLD vs NEW ODU MAPPING")
print("="*110)
print("x        old_odu        anchors agreements  AGREE byte/odu          FLIP byte/odu           DISAGREE byte/odu")
print("-"*110)

for x in tests:
    a = force_agreement(x)
    f = flip_agreement(x)
    d = force_disagreement(x)

    print(
        f"{b8(x)}  {odu_pair(x):<18} "
        f"{anchors(x)}     {agreements(x)}       "
        f"{b8(a)} {odu_pair(a):<18} "
        f"{b8(f)} {odu_pair(f):<18} "
        f"{b8(d)} {odu_pair(d):<18}"
    )

print()
print("INTERPRETATION")
print("-"*110)
print("""
OLD:
    byte is read directly as two Odu nibbles.

NEW:
    byte is interpreted as anchors + agreements.
    Relation instructions change the agreement structure while preserving anchors.

For A5:
    old:      A5 -> Òfún Òsé
    AGREE:    F0 -> Ògbè Òyèkú
    FLIP:     F0? or depends on current state
    DISAGREE: A5-style disagreement state

The new mapping does not replace the old Odu index.
It adds a relation-space layer before Odu interpretation.
""")
