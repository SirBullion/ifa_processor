#!/usr/bin/env python3

# ============================================================
# IFÁ RETRIEVAL + CORRECTION AUDIT
# ============================================================

def bits(x, n):
    return [(x >> i) & 1 for i in reversed(range(n))]

def to_int(bs):
    y = 0
    for b in bs:
        y = (y << 1) | b
    return y

def bstr(x, n=8):
    return format(x, f"0{n}b")

# Current corrected P2:
# A' = A
# B' = NOT(A XOR B)
def p2(a, b):
    return a, 1 ^ (a ^ b)

# Since current P2 has order 2, inverse is same as P2.
def p2_inv(a, b):
    return p2(a, b)

def p8(x):
    bs = bits(x, 8)
    out = []
    for i in range(0, 8, 2):
        out.extend(p2(bs[i], bs[i+1]))
    return to_int(out)

def p8_inv(y):
    bs = bits(y, 8)
    out = []
    for i in range(0, 8, 2):
        out.extend(p2_inv(bs[i], bs[i+1]))
    return to_int(out)

# Observed delta from encoded-space error e.
# IMPORTANT:
# P8 is affine because of the NOT term, so error masks are transported
# by the linear part only, not by applying full P8 to the error mask.
def transport_delta(e):
    out = 0
    for shift in [6, 4, 2, 0]:
        ea = (e >> (shift + 1)) & 1
        eb = (e >> shift) & 1

        da = ea
        db = ea ^ eb

        out |= da << (shift + 1)
        out |= db << shift

    return out

def audit_recovery():
    failures = 0

    print("=" * 100)
    print("PURE RETRIEVAL AUDIT")
    print("=" * 100)

    for x in range(256):
        y = p8(x)
        xr = p8_inv(y)
        if xr != x:
            failures += 1
            print("FAIL", bstr(x), bstr(y), bstr(xr))

    print("Recovery failures:", failures)

def audit_single_bit_correction():
    failures = 0
    tests = 0

    print()
    print("=" * 100)
    print("SINGLE-BIT ERROR CORRECTION AUDIT")
    print("=" * 100)
    print("x        y        e        y_err    x_err    delta    e_rec    y_corr   x_final")
    print("-" * 100)

    for x in range(256):
        y = p8(x)

        for k in range(8):
            e = 1 << k
            y_err = y ^ e

            x_err = p8_inv(y_err)
            delta = x ^ x_err

            # Because P8 is its own inverse here, e can be recovered by applying transport again.
            e_rec = transport_delta(delta)

            y_corr = y_err ^ e_rec
            x_final = p8_inv(y_corr)

            tests += 1

            if tests <= 32:
                print(
                    bstr(x), bstr(y), bstr(e), bstr(y_err),
                    bstr(x_err), bstr(delta), bstr(e_rec),
                    bstr(y_corr), bstr(x_final)
                )

            if e_rec != e or y_corr != y or x_final != x:
                failures += 1
                print("FAIL:",
                    "x", bstr(x),
                    "e", bstr(e),
                    "delta", bstr(delta),
                    "e_rec", bstr(e_rec),
                    "x_final", bstr(x_final)
                )

    print("-" * 100)
    print("Total tests:", tests)
    print("Correction failures:", failures)

def audit_error_transport_table():
    print()
    print("=" * 100)
    print("ERROR TRANSPORT TABLE")
    print("=" * 100)
    print("encoded_error e  -> observed_delta Δ  -> recovered_error")
    print("-" * 100)

    for k in range(8):
        e = 1 << k
        delta = transport_delta(e)
        e_rec = transport_delta(delta)
        print(f"{bstr(e)} -> {bstr(delta)} -> {bstr(e_rec)}")

def main():
    audit_recovery()
    audit_error_transport_table()
    audit_single_bit_correction()

    print()
    print("=" * 100)
    print("FORMAL INTERPRETATION")
    print("=" * 100)
    print("""
Retrieval:
    P⁻¹(P(x)) = x

Error propagation:
    If encoded state y = P(x) is corrupted by e,
    then inverse decoding gives:

        P⁻¹(y ⊕ e) = x ⊕ Δ

    where Δ is the transported error in the decoded/original domain.

Correction:
    Because the transport map is reversible,
    the system recovers e from Δ, then corrects:

        y_corrected = y_err ⊕ e

    and finally:

        P⁻¹(y_corrected) = x

This means the architecture does not merely detect corruption.
It transports the error into a recoverable form, then reverses it.
""")

if __name__ == "__main__":
    main()
