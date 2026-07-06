#!/usr/bin/env python3

def b8(x):
    return format(x, "08b")

def bit(x, i):
    return (x >> i) & 1

def relation_full_adder_bit(a, b, cin):
    # Relation primitives
    rd = a ^ b              # disagreement
    ra = 1 ^ rd             # agreement
    r1 = a & b              # shared-one
    r0 = (1 ^ a) & (1 ^ b)  # shared-zero

    # Relation-derived full adder
    s = rd ^ cin
    cout = r1 | (rd & cin)

    return s, cout, ra, rd, r1, r0

def relation_add8(A, B):
    carry = 0
    result = 0

    RA = 0
    RD = 0
    R1 = 0
    R0 = 0
    CARRY_TRACE = 0

    for i in range(8):
        a = bit(A, i)
        b = bit(B, i)

        s, carry, ra, rd, r1, r0 = relation_full_adder_bit(a, b, carry)

        result |= s << i
        RA |= ra << i
        RD |= rd << i
        R1 |= r1 << i
        R0 |= r0 << i
        CARRY_TRACE |= carry << i

    return result, carry, RA, RD, R1, R0, CARRY_TRACE

failures = 0
tests = 0

print("=" * 90)
print("RELATION-DERIVED ADD AUDIT")
print("=" * 90)
print("Testing all 256 x 256 byte pairs")
print()

for A in range(256):
    for B in range(256):
        result, cout, RA, RD, R1, R0, CARRY_TRACE = relation_add8(A, B)

        expected = A + B
        expected_result = expected & 0xFF
        expected_carry = 1 if expected > 0xFF else 0

        tests += 1

        if result != expected_result or cout != expected_carry:
            failures += 1
            if failures <= 20:
                print("FAIL")
                print("A       ", b8(A))
                print("B       ", b8(B))
                print("RESULT  ", b8(result), "carry", cout)
                print("EXPECT  ", b8(expected_result), "carry", expected_carry)
                print("RA      ", b8(RA))
                print("RD      ", b8(RD))
                print("R1      ", b8(R1))
                print("R0      ", b8(R0))
                print("CARRYTR ", b8(CARRY_TRACE))
                print()

print("Total tests:", tests)
print("Failures:", failures)

print()
print("=" * 90)
print("SAMPLE RELATION ADD")
print("=" * 90)

samples = [
    (0x0A, 0x05),
    (0xA5, 0x5A),
    (0xFF, 0x01),
    (0x33, 0x55),
    (0xF0, 0xA5),
]

for A, B in samples:
    result, cout, RA, RD, R1, R0, CARRY_TRACE = relation_add8(A, B)

    print(f"A={b8(A)} B={b8(B)}")
    print(f"RESULT       = {b8(result)} carry={cout}")
    print(f"AGREEMENT    = {b8(RA)}")
    print(f"DISAGREEMENT = {b8(RD)}")
    print(f"SHARED_ONE   = {b8(R1)}")
    print(f"SHARED_ZERO  = {b8(R0)}")
    print(f"CARRY_TRACE  = {b8(CARRY_TRACE)}")
    print("-" * 60)

print()
print("=" * 90)
print("CONCLUSION")
print("=" * 90)

if failures == 0:
    print("""
PASS.

8-bit ADD can be derived from relation primitives:

    R_D = A XOR B                 disagreement
    R_A = NOT(A XOR B)            agreement
    R_1 = A AND B                 shared-one
    R_0 = NOT(A OR B)             shared-zero

Then per bit:

    SUM  = R_D XOR Cin
    Cout = R_1 OR (R_D AND Cin)

This means ADD does not need to be treated as a primitive ALU operation.
It can be constructed as a relation algorithm.
""")
else:
    print("FAIL: relation-derived ADD did not match ordinary addition.")
