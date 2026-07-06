#!/usr/bin/env python3

def b8(x):
    return format(x, "08b")

def bit(x, i):
    return (x >> i) & 1

def relation_full_adder_bit(a, b, cin):
    rd = a ^ b
    r1 = a & b

    s = rd ^ cin
    cout = r1 | (rd & cin)

    return s, cout

def relation_add8(A, B):
    carry = 0
    result = 0

    for i in range(8):
        a = bit(A, i)
        b = bit(B, i)

        s, carry = relation_full_adder_bit(a, b, carry)
        result |= s << i

    return result & 0xFF, carry

def relation_mul8(A, B):
    """
    Relation-derived multiplication:
        multiply = repeated conditional shifted relation-add

    This tests low 8-bit product.
    """
    acc = 0
    add_count = 0

    for i in range(8):
        if bit(B, i):
            shifted = (A << i) & 0xFF
            acc, _ = relation_add8(acc, shifted)
            add_count += 1

    return acc & 0xFF, add_count

failures = 0
tests = 0

print("=" * 90)
print("RELATION-DERIVED MUL AUDIT")
print("=" * 90)
print("Testing all 256 x 256 byte pairs")
print()

for A in range(256):
    for B in range(256):
        result, add_count = relation_mul8(A, B)

        expected = (A * B) & 0xFF

        tests += 1

        if result != expected:
            failures += 1
            if failures <= 20:
                print("FAIL")
                print("A       ", b8(A))
                print("B       ", b8(B))
                print("RESULT  ", b8(result))
                print("EXPECT  ", b8(expected))
                print("ADDCOUNT", add_count)
                print()

print("Total tests:", tests)
print("Failures:", failures)

print()
print("=" * 90)
print("SAMPLE RELATION MUL")
print("=" * 90)

samples = [
    (0x03, 0x05),
    (0x0A, 0x05),
    (0x0F, 0x0F),
    (0xA5, 0x03),
    (0x33, 0x05),
    (0xFF, 0x02),
]

for A, B in samples:
    result, add_count = relation_mul8(A, B)
    expected = (A * B) & 0xFF

    print(f"A={b8(A)} B={b8(B)}")
    print(f"RESULT   = {b8(result)}")
    print(f"EXPECTED = {b8(expected)}")
    print(f"RELATION_ADD_COUNT = {add_count}")
    print("-" * 60)

print()
print("=" * 90)
print("CONCLUSION")
print("=" * 90)

if failures == 0:
    print("""
PASS.

8-bit MUL can be constructed from relation-derived ADD.

This is not yet a primitive one-cycle multiplier.
It proves that multiplication can be built as a relation algorithm:

    MUL(A,B)
        = repeated shifted Relation-ADD

So far:

    ADD      derived from relation primitives
    SUB      derived from relation primitives
    COMPARE  derived from relation primitives
    MUL      derived from relation-derived ADD

This supports the RAU/RPC idea:
arithmetic can be built from relation extraction and relation propagation.
""")
else:
    print("FAIL: relation-derived MUL did not match ordinary multiplication.")
