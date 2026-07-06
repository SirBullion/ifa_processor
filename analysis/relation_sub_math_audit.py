#!/usr/bin/env python3

def b8(x):
    return format(x, "08b")

def bit(x, i):
    return (x >> i) & 1

def relation_full_subtractor_bit(a, b, bin_):
    # Relation primitives
    rd = a ^ b              # disagreement
    ra = 1 ^ rd             # agreement
    r1 = a & b              # shared-one
    r0 = (1 ^ a) & (1 ^ b)  # shared-zero

    # Extra directional relation for borrow:
    # b is 1 while a is 0
    b_over_a = (1 ^ a) & b

    # Relation-derived subtractor
    diff = rd ^ bin_
    bout = b_over_a | (ra & bin_)

    return diff, bout, ra, rd, r1, r0, b_over_a

def relation_sub8(A, B):
    borrow = 0
    result = 0

    RA = 0
    RD = 0
    R1 = 0
    R0 = 0
    B_OVER_A = 0
    BORROW_TRACE = 0

    for i in range(8):
        a = bit(A, i)
        b = bit(B, i)

        diff, borrow, ra, rd, r1, r0, b_over_a = relation_full_subtractor_bit(a, b, borrow)

        result |= diff << i
        RA |= ra << i
        RD |= rd << i
        R1 |= r1 << i
        R0 |= r0 << i
        B_OVER_A |= b_over_a << i
        BORROW_TRACE |= borrow << i

    return result, borrow, RA, RD, R1, R0, B_OVER_A, BORROW_TRACE

failures = 0
tests = 0

print("=" * 90)
print("RELATION-DERIVED SUB AUDIT")
print("=" * 90)
print("Testing all 256 x 256 byte pairs")
print()

for A in range(256):
    for B in range(256):
        result, borrow, RA, RD, R1, R0, B_OVER_A, BORROW_TRACE = relation_sub8(A, B)

        expected = (A - B) & 0xFF
        expected_borrow = 1 if A < B else 0

        tests += 1

        if result != expected or borrow != expected_borrow:
            failures += 1
            if failures <= 20:
                print("FAIL")
                print("A        ", b8(A))
                print("B        ", b8(B))
                print("RESULT   ", b8(result), "borrow", borrow)
                print("EXPECT   ", b8(expected), "borrow", expected_borrow)
                print("RA       ", b8(RA))
                print("RD       ", b8(RD))
                print("R1       ", b8(R1))
                print("R0       ", b8(R0))
                print("B_OVER_A ", b8(B_OVER_A))
                print("BORROWTR ", b8(BORROW_TRACE))
                print()

print("Total tests:", tests)
print("Failures:", failures)

print()
print("=" * 90)
print("SAMPLE RELATION SUB")
print("=" * 90)

samples = [
    (0x10, 0x01),
    (0xA5, 0x05),
    (0x00, 0x01),
    (0x33, 0x55),
    (0xF0, 0xA5),
]

for A, B in samples:
    result, borrow, RA, RD, R1, R0, B_OVER_A, BORROW_TRACE = relation_sub8(A, B)

    print(f"A={b8(A)} B={b8(B)}")
    print(f"RESULT       = {b8(result)} borrow={borrow}")
    print(f"AGREEMENT    = {b8(RA)}")
    print(f"DISAGREEMENT = {b8(RD)}")
    print(f"SHARED_ONE   = {b8(R1)}")
    print(f"SHARED_ZERO  = {b8(R0)}")
    print(f"B_OVER_A     = {b8(B_OVER_A)}")
    print(f"BORROW_TRACE = {b8(BORROW_TRACE)}")
    print("-" * 60)

print()
print("=" * 90)
print("CONCLUSION")
print("=" * 90)

if failures == 0:
    print("""
PASS.

8-bit SUB can be derived from relation primitives:

    R_D = A XOR B                 disagreement
    R_A = NOT(A XOR B)            agreement
    B_OVER_A = NOT(A) AND B       directional borrow relation

Then per bit:

    DIFF = R_D XOR Bin
    Bout = B_OVER_A OR (R_A AND Bin)

This means SUB also does not need to be treated as a primitive ALU operation.
It can be constructed as a relation algorithm.
""")
else:
    print("FAIL: relation-derived SUB did not match ordinary subtraction.")
