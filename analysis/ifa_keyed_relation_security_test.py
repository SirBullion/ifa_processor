#!/usr/bin/env python3
from collections import Counter

def bits(x):
    return [(x >> i) & 1 for i in reversed(range(8))]

def to_int(bs):
    y = 0
    for b in bs:
        y = (y << 1) | b
    return y

def bstr(x):
    return format(x, "08b")

def kstr(k):
    return format(k, "04b")

def aa_encode(x):
    bs = bits(x)
    out = []
    for i in range(0,8,2):
        a = bs[i]
        b = bs[i+1]
        agreement = 1 if a == b else 0
        out.extend([a, agreement])
    return to_int(out)

def aa_decode(y):
    bs = bits(y)
    out = []
    for i in range(0,8,2):
        anchor = bs[i]
        agreement = bs[i+1]
        b = anchor if agreement else 1-anchor
        out.extend([anchor, b])
    return to_int(out)

def key_relation(y, key4):
    """
    y is anchor-agreement byte:
        bits: A g0 C g1 E g2 G g3
    key masks only agreement bits.
    """
    bs = bits(y)
    key_bits = [(key4 >> i) & 1 for i in reversed(range(4))]

    bs[1] ^= key_bits[0]
    bs[3] ^= key_bits[1]
    bs[5] ^= key_bits[2]
    bs[7] ^= key_bits[3]

    return to_int(bs)

def encrypt(x, key4):
    y = aa_encode(x)
    return key_relation(y, key4)

def decrypt(c, key4):
    y = key_relation(c, key4)
    return aa_decode(y)

print("="*80)
print("KEYED RELATION TRANSFORM SECURITY TEST")
print("="*80)

# 1. Correctness
failures = 0
tests = 0

for x in range(256):
    for k in range(16):
        c = encrypt(x, k)
        xr = decrypt(c, k)
        tests += 1
        if xr != x:
            failures += 1
            print("FAIL", bstr(x), kstr(k), bstr(c), bstr(xr))
            break

print("Correctness tests:", tests)
print("Correctness failures:", failures)

# 2. Wrong-key ambiguity
print()
print("="*80)
print("WRONG-KEY RECOVERY TEST")
print("="*80)

wrong_same = 0
wrong_tests = 0

for x in range(256):
    for k in range(16):
        c = encrypt(x, k)
        for k2 in range(16):
            if k2 == k:
                continue
            xr = decrypt(c, k2)
            wrong_tests += 1
            if xr == x:
                wrong_same += 1

print("Wrong-key tests:", wrong_tests)
print("Wrong-key recovered original:", wrong_same)

# 3. Candidate plaintext count if key unknown
print()
print("="*80)
print("UNKNOWN-KEY CANDIDATE COUNT")
print("="*80)

candidate_hist = Counter()

for x in range(256):
    for k in range(16):
        c = encrypt(x, k)
        candidates = set(decrypt(c, kk) for kk in range(16))
        candidate_hist[len(candidates)] += 1

print("Candidate count histogram:", dict(sorted(candidate_hist.items())))

# 4. Sample
print()
print("="*80)
print("SAMPLE")
print("="*80)

x = 0xA5
key = 0b1011
c = encrypt(x, key)

print("Plaintext :", bstr(x))
print("Key       :", kstr(key))
print("Cipher    :", bstr(c))
print("Recovered :", bstr(decrypt(c, key)))

print()
print("Wrong-key candidates:")
for kk in range(16):
    print(kstr(kk), "->", bstr(decrypt(c, kk)))

print()
print("="*80)
print("INTERPRETATION")
print("="*80)
print("""
This is not full encryption yet, because anchors remain visible.

But it is the first keyed security layer:
    - Φ-P8 maps bits into anchor/agreement coordinates.
    - The key masks only the agreement channel.
    - Correct key recovers the original.
    - Wrong key gives another plausible state.

Security direction:
    1. mask agreement channel,
    2. then also permute/mix anchors,
    3. then stack rounds for diffusion.
""")
