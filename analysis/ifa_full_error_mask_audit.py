#!/usr/bin/env python3

def bits(x, n):
    return [(x >> i) & 1 for i in reversed(range(n))]

def to_int(bs):
    y = 0
    for b in bs:
        y = (y << 1) | b
    return y

def bstr(x):
    return format(x, "08b")

# Current P2:
# A' = A
# B' = NOT(A XOR B)
def p2(a, b):
    return a, 1 ^ (a ^ b)

def p8(x):
    bs = bits(x, 8)
    out = []
    for i in range(0, 8, 2):
        out.extend(p2(bs[i], bs[i + 1]))
    return to_int(out)

# Current P8 is self-inverse
def p8_inv(y):
    return p8(y)

# Linear error transport T8
def t8(e):
    out = 0
    for shift in [6, 4, 2, 0]:
        ea = (e >> (shift + 1)) & 1
        eb = (e >> shift) & 1

        da = ea
        db = ea ^ eb

        out |= da << (shift + 1)
        out |= db << shift

    return out

failures = 0
tests = 0

for x in range(256):
    y = p8(x)

    for e in range(256):
        y_err = y ^ e
        x_err = p8_inv(y_err)

        delta = x ^ x_err
        e_rec = t8(delta)

        y_corr = y_err ^ e_rec
        x_final = p8_inv(y_corr)

        tests += 1

        if e_rec != e or y_corr != y or x_final != x:
            failures += 1
            if failures <= 20:
                print(
                    "FAIL",
                    "x", bstr(x),
                    "e", bstr(e),
                    "delta", bstr(delta),
                    "e_rec", bstr(e_rec),
                    "x_final", bstr(x_final)
                )

print("=" * 80)
print("FULL ERROR MASK AUDIT")
print("=" * 80)
print("Total tests:", tests)
print("Failures:", failures)

if failures == 0:
    print("PASS: all 65,536 input/error-mask corrections succeeded.")
else:
    print("FAIL: correction mismatch detected.")
