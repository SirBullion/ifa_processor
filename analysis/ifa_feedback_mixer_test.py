#!/usr/bin/env python3
from collections import Counter

KEY = 0b10101010  # Ofun Meji

def b8(x):
    return format(x, "08b")

def rotl(x, r):
    return ((x << r) | (x >> (8-r))) & 0xFF

def hd(a,b):
    return (a ^ b).bit_count()

def ofun_feedback_mix(x, rounds=4):
    """
    Separate feedback mixer.
    P8 is not modified.

    state feeds back each round:
        state = state XOR key
        state = state XOR rotl(state, 1)
        state = state XOR rotl(state, 3)
        state = state XOR round_constant
    """
    state = x

    for r in range(rounds):
        state ^= KEY
        state ^= rotl(state, 1)
        state ^= rotl(state, 3)
        state ^= ((r * 0x3D) + 0x17) & 0xFF

    return state & 0xFF

print("="*80)
print("IFÁ SEPARATE FEEDBACK MIXER TEST")
print("="*80)
print("Key: Ofun Meji =", b8(KEY))
print()

for rounds in [1,2,3,4,5,6,8]:
    hist = Counter()
    total = 0
    tests = 0

    for x in range(256):
        y = ofun_feedback_mix(x, rounds)
        for k in range(8):
            x2 = x ^ (1 << k)
            y2 = ofun_feedback_mix(x2, rounds)
            d = hd(y,y2)
            hist[d] += 1
            total += d
            tests += 1

    print(f"rounds={rounds}")
    print("  tests:", tests)
    print("  mean avalanche:", total/tests)
    print("  histogram:", dict(sorted(hist.items())))
    print()

print("="*80)
print("INTERPRETATION")
print("="*80)
print("""
This treats feedback as a separate architectural block:

    Φ-P8  ->  Relation Unit  ->  Feedback Mixer  ->  Output

If avalanche improves toward 4.0, then the security/diffusion role belongs
to the feedback mixer, not to Φ-P8 itself.
""")
