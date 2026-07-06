#!/usr/bin/env python3

def b8(x):
    return format(x, "08b")

def bit(x, i):
    return (x >> i) & 1

def relation_compare8(A, B):
    """
    Relation-derived comparator.

    Work from MSB to LSB.

    At each bit:
        RA = agreement = NOT(A XOR B)
        A_OVER_B = A AND NOT(B)
        B_OVER_A = NOT(A) AND B

    The first differing bit decides greater/less.
    """

    equal_so_far = 1
    gt = 0
    lt = 0

    RA = 0
    RD = 0
    A_OVER_B = 0
    B_OVER_A = 0

    for i in reversed(range(8)):
        a = bit(A, i)
        b = bit(B, i)

        rd = a ^ b
        ra = 1 ^ rd

        a_over_b = a & (1 ^ b)
        b_over_a = (1 ^ a) & b

        RA |= ra << i
        RD |= rd << i
        A_OVER_B |= a_over_b << i
        B_OVER_A |= b_over_a << i

        if equal_so_far:
            if a_over_b:
                gt = 1
                equal_so_far = 0
            elif b_over_a:
                lt = 1
                equal_so_far = 0
            else:
                equal_so_far = equal_so_far & ra

    eq = equal_so_far

    return eq, gt, lt, RA, RD, A_OVER_B, B_OVER_A

failures = 0
tests = 0

print("=" * 90)
print("RELATION-DERIVED COMPARE AUDIT")
print("=" * 90)
print("Testing all 256 x 256 byte pairs")
print()

for A in range(256):
    for B in range(256):
        eq, gt, lt, RA, RD, A_OVER_B, B_OVER_A = relation_compare8(A, B)

        exp_eq = 1 if A == B else 0
        exp_gt = 1 if A > B else 0
        exp_lt = 1 if A < B else 0

        tests += 1

        if eq != exp_eq or gt != exp_gt or lt != exp_lt:
            failures += 1
            if failures <= 20:
                print("FAIL")
                print("A        ", b8(A))
                print("B        ", b8(B))
                print("EQ GT LT ", eq, gt, lt)
                print("EXP      ", exp_eq, exp_gt, exp_lt)
                print("RA       ", b8(RA))
                print("RD       ", b8(RD))
                print("A_OVER_B ", b8(A_OVER_B))
                print("B_OVER_A ", b8(B_OVER_A))
                print()

print("Total tests:", tests)
print("Failures:", failures)

print()
print("=" * 90)
print("SAMPLE RELATION COMPARE")
print("=" * 90)

samples = [
    (0xA5, 0xA5),
    (0xA5, 0x5A),
    (0x33, 0x55),
    (0xF0, 0xA5),
    (0x00, 0x01),
    (0xFF, 0x01),
]

for A, B in samples:
    eq, gt, lt, RA, RD, A_OVER_B, B_OVER_A = relation_compare8(A, B)

    print(f"A={b8(A)} B={b8(B)}")
    print(f"EQ={eq} GT={gt} LT={lt}")
    print(f"AGREEMENT    = {b8(RA)}")
    print(f"DISAGREEMENT = {b8(RD)}")
    print(f"A_OVER_B     = {b8(A_OVER_B)}")
    print(f"B_OVER_A     = {b8(B_OVER_A)}")
    print("-" * 60)

print()
print("=" * 90)
print("CONCLUSION")
print("=" * 90)

if failures == 0:
    print("""
PASS.

8-bit COMPARE can be derived from relation primitives without subtraction.

Per bit:

    R_A = NOT(A XOR B)        agreement
    R_D = A XOR B             disagreement
    A_OVER_B = A AND NOT(B)   directional greater relation
    B_OVER_A = NOT(A) AND B   directional lesser relation

From MSB to LSB:

    The first disagreement decides GT or LT.
    If no disagreement occurs, EQ = 1.

This means COMPARE is naturally relation-native.
""")
else:
    print("FAIL: relation-derived COMPARE did not match ordinary comparison.")
