import random
import pandas as pd

WIDTH = 16
MOD = 1 << WIDTH
MASK = MOD - 1
N_RANDOM = 200_000

random.seed(42)

def relation_state(a, b):
    y = (a + b) & MASK
    ra = a & b
    rd = a ^ b
    r0 = (~(a | b)) & MASK

    diff = abs(a - b)
    wrap = MOD - diff
    t = min(diff, wrap) & MASK

    return y, ra, rd, r0, t

def coord(a, b):
    y, ra, rd, r0, t = relation_state(a, b)
    return (ra, rd, t)

tests = []

edges = [
    0, 1, 2, 3,
    MASK,
    MASK - 1,
    MASK >> 1,
    1 << (WIDTH - 1),
    (1 << (WIDTH - 1)) - 1,
]

for a in edges:
    for b in edges:
        tests.append((a, b))

for _ in range(N_RANDOM):
    tests.append((random.randrange(MOD), random.randrange(MOD)))

coord_map = {}
ambiguous = 0
examples = []

for a, b in tests:
    state = relation_state(a, b)
    c = coord(a, b)

    if c in coord_map and coord_map[c] != state:
        ambiguous += 1
        if len(examples) < 10:
            examples.append({
                "A": a,
                "B": b,
                "coord": c,
                "previous_state": coord_map[c],
                "current_state": state,
            })
    else:
        coord_map[c] = state

print("====================================")
print("Φ-P Coordinate Inverse WIDTH=16 sampled")
print("====================================")
print(f"Tests run: {len(tests)}")
print(f"Unique coordinates: {len(coord_map)}")
print(f"Ambiguous coordinates: {ambiguous}")

if ambiguous == 0:
    print("\nPASS: no ambiguity found in WIDTH=16 sampled test.")
else:
    print("\nFAIL: ambiguity found.")
    for ex in examples:
        print(ex)

pd.DataFrame([{
    "width": WIDTH,
    "tests_run": len(tests),
    "unique_coordinates": len(coord_map),
    "ambiguous_coordinates": ambiguous,
    "passed": ambiguous == 0
}]).to_csv("analysis/phi_p16_sampled_inverse_summary.csv", index=False)

print("\nSaved: analysis/phi_p16_sampled_inverse_summary.csv")
