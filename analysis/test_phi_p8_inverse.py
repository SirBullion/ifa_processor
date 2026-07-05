import pandas as pd

WIDTH = 4
MOD = 1 << WIDTH

def relation_state(a, b, width=WIDTH):
    mask = (1 << width) - 1

    y = (a + b) & mask
    ra = a & b
    rd = a ^ b
    r0 = (~(a | b)) & mask

    diff = abs(a - b)
    wrap = (1 << width) - diff
    t = min(diff, wrap) & mask

    return y, ra, rd, r0, t

def phi_p8_coordinate(a, b, width=WIDTH):
    """
    First test coordinate:
    Store A,B directly as Φ-P8 coordinate.

    If this passes, it proves that a coordinate memory can reconstruct
    relation state losslessly when coordinate = canonical operand pair.
    Later we test compressed coordinates.
    """
    return (a, b)

def inverse_phi_p8(coord):
    return coord

rows = []
coord_map = {}

ambiguous = 0
failures = 0

for a in range(MOD):
    for b in range(MOD):
        original = relation_state(a, b)

        coord = phi_p8_coordinate(a, b)
        a2, b2 = inverse_phi_p8(coord)

        reconstructed = relation_state(a2, b2)

        ok = original == reconstructed

        if coord in coord_map and coord_map[coord] != original:
            ambiguous += 1

        coord_map[coord] = original

        if not ok:
            failures += 1

        rows.append({
            "A": a,
            "B": b,
            "coord": coord,
            "Y": original[0],
            "R_A": original[1],
            "R_D": original[2],
            "R_0": original[3],
            "T": original[4],
            "Y_rec": reconstructed[0],
            "R_A_rec": reconstructed[1],
            "R_D_rec": reconstructed[2],
            "R_0_rec": reconstructed[3],
            "T_rec": reconstructed[4],
            "ok": ok
        })

df = pd.DataFrame(rows)

print("====================================")
print("Φ-P8 INVERSE TEST")
print("====================================")
print(f"WIDTH: {WIDTH}")
print(f"Total states tested: {len(df)}")
print(f"Unique coordinates: {len(coord_map)}")
print(f"Ambiguous coordinates: {ambiguous}")
print(f"Reconstruction failures: {failures}")

if failures == 0 and ambiguous == 0:
    print("\nPASS: Φ-P8 coordinate reconstructs relation state losslessly.")
else:
    print("\nFAIL: Φ-P8 coordinate is not lossless.")

df.to_csv("analysis/phi_p8_inverse_test.csv", index=False)
print("\nSaved: analysis/phi_p8_inverse_test.csv")
