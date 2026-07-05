import pandas as pd

WIDTH = 8
MOD = 1 << WIDTH
MASK = MOD - 1

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

coord_map = {}
ambiguous = 0
failures = 0
examples = []

for a in range(MOD):
    for b in range(MOD):
        state = relation_state(a, b)
        c = coord(a, b)

        if c in coord_map and coord_map[c] != state:
            ambiguous += 1
            failures += 1
            if len(examples) < 10:
                examples.append((a, b, c, coord_map[c], state))
        else:
            coord_map[c] = state

print("====================================")
print("Φ-P Coordinate Inverse WIDTH=8")
print("====================================")
print(f"Total states tested: {MOD * MOD}")
print(f"Unique coordinates: {len(coord_map)}")
print(f"Ambiguous coordinates: {ambiguous}")
print(f"Failures: {failures}")

if failures == 0:
    print("\nPASS: (R_A, R_D, T) is lossless for WIDTH=8.")
else:
    print("\nFAIL: coordinate is ambiguous for WIDTH=8.")
    print("\nExamples:")
    for ex in examples:
        print(ex)

pd.DataFrame([
    {
        "width": WIDTH,
        "total_states": MOD * MOD,
        "unique_coordinates": len(coord_map),
        "ambiguous_coordinates": ambiguous,
        "failures": failures,
        "passed": failures == 0
    }
]).to_csv("analysis/phi_p8_width8_inverse_summary.csv", index=False)

print("\nSaved: analysis/phi_p8_width8_inverse_summary.csv")
