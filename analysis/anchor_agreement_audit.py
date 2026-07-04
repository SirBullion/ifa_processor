#!/usr/bin/env python3

def aa_gate(a, b):
    anchor = a
    agreement = 1 if a == b else 0
    return anchor, agreement

def aa_inv(anchor, agreement):
    a = anchor
    if agreement == 1:
        b = a
    else:
        b = 1 - a
    return a, b

print("=" * 70)
print("ANCHOR–AGREEMENT GATE FORMAL AUDIT")
print("=" * 70)

print("""
Definition:

Φ : {0,1}² → {0,1}²

Φ(A,B) = (Anchor, Agreement)

Anchor    = A
Agreement = 1 if A = B
            0 if A ≠ B
""")

print("A B | Anchor Agreement | Recovered A B")
print("----|------------------|--------------")

failures = 0

for a in [0,1]:
    for b in [0,1]:
        anchor, agreement = aa_gate(a,b)
        ar, br = aa_inv(anchor, agreement)

        ok = (a,b) == (ar,br)

        if not ok:
            failures += 1

        print(f"{a} {b} |   {anchor}        {agreement}       |     {ar} {br}")

print()
print("Recovery failures:", failures)

if failures == 0:
    print("PASS: Anchor–Agreement mapping is reversible.")
else:
    print("FAIL: mapping is not reversible.")
