#!/usr/bin/env python3
from collections import Counter

def bits(x):
    return [(x >> i) & 1 for i in reversed(range(8))]

def to_int(bs):
    y = 0
    for b in bs:
        y = (y << 1) | b
    return y & 0xFF

def bstr(x):
    return format(x, "08b")

def aa_encode(x):
    bs = bits(x)
    out = []
    for i in range(0,8,2):
        a,b = bs[i], bs[i+1]
        agree = 1 if a == b else 0
        out.extend([a, agree])
    return to_int(out)

def aa_decode(y):
    bs = bits(y)
    out = []
    for i in range(0,8,2):
        a = bs[i]
        agree = bs[i+1]
        b = a if agree else 1-a
        out.extend([a,b])
    return to_int(out)

def mask_agreements(y, k4):
    bs = bits(y)
    kb = [(k4 >> i) & 1 for i in reversed(range(4))]
    bs[1] ^= kb[0]
    bs[3] ^= kb[1]
    bs[5] ^= kb[2]
    bs[7] ^= kb[3]
    return to_int(bs)

# Reversible diffusion mixer:
# triangular XOR network, self-invertible with inverse below.
def mix(x):
    b = bits(x)

    # output bits depend on multiple earlier bits
    y = [0]*8
    y[0] = b[0]
    y[1] = b[1] ^ b[0]
    y[2] = b[2] ^ b[1]
    y[3] = b[3] ^ b[2]
    y[4] = b[4] ^ b[3]
    y[5] = b[5] ^ b[4]
    y[6] = b[6] ^ b[5]
    y[7] = b[7] ^ b[6]
    return to_int(y)

def inv_mix(x):
    y = bits(x)
    b = [0]*8

    b[0] = y[0]
    b[1] = y[1] ^ b[0]
    b[2] = y[2] ^ b[1]
    b[3] = y[3] ^ b[2]
    b[4] = y[4] ^ b[3]
    b[5] = y[5] ^ b[4]
    b[6] = y[6] ^ b[5]
    b[7] = y[7] ^ b[6]

    return to_int(b)

def round_enc(x, k4):
    y = aa_encode(x)
    y = mask_agreements(y, k4)
    y = aa_decode(y)
    y = mix(y)
    return y

def round_dec(x, k4):
    y = inv_mix(x)
    y = aa_encode(y)
    y = mask_agreements(y, k4)
    y = aa_decode(y)
    return y

def enc(x, keys):
    y = x
    for k in keys:
        y = round_enc(y, k)
    return y

def dec(c, keys):
    y = c
    for k in reversed(keys):
        y = round_dec(y, k)
    return y

def hd(a,b):
    return (a ^ b).bit_count()

keysets = {
    "1_round": [0xB],
    "2_round": [0xB,0x6],
    "4_round": [0xB,0x6,0xD,0x3],
    "8_round": [0xB,0x6,0xD,0x3,0x9,0xC,0x5,0xA],
}

print("="*80)
print("KEYED Φ-P8 + REVERSIBLE DIFFUSION TEST")
print("="*80)

# Mixer sanity
mix_fail = 0
for x in range(256):
    if inv_mix(mix(x)) != x:
        mix_fail += 1

print("Mixer inverse failures:", mix_fail)

for name, keys in keysets.items():
    failures = 0
    for x in range(256):
        c = enc(x, keys)
        xr = dec(c, keys)
        if xr != x:
            failures += 1

    hist = Counter()
    total = 0
    tests = 0

    for x in range(256):
        y = enc(x, keys)
        for bit in range(8):
            x2 = x ^ (1 << bit)
            y2 = enc(x2, keys)
            d = hd(y,y2)
            hist[d] += 1
            total += d
            tests += 1

    print()
    print(name)
    print("-"*40)
    print("keys:", [format(k,"04b") for k in keys])
    print("correctness failures:", failures)
    print("tests:", tests)
    print("average output bit changes:", total/tests)
    print("histogram:", dict(sorted(hist.items())))

print()
print("Interpretation:")
print("If diffusion improves above 1.0 and approaches 4.0,")
print("the reversible mixer is successfully coupling bits across the state.")
