import pandas as pd

WIDTH = 4
MOD = 1 << WIDTH
MASK = MOD - 1


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


def test_coordinate(name, coord_fn):
    coord_map = {}
    ambiguous = 0
    failures = 0
    rows = []

    for a in range(MOD):
        for b in range(MOD):
            state = relation_state(a, b)
            coord = coord_fn(a, b, state)

            if coord in coord_map and coord_map[coord] != state:
                ambiguous += 1
                ok = False
            else:
                ok = True

            coord_map[coord] = state

            rows.append({
                "test": name,
                "A": a,
                "B": b,
                "coord": coord,
                "Y": state[0],
                "R_A": state[1],
                "R_D": state[2],
                "R_0": state[3],
                "T": state[4],
                "ok": ok
            })

            if not ok:
                failures += 1

    print("\n====================================")
    print(f"TEST: {name}")
    print("====================================")
    print(f"Total states: {MOD * MOD}")
    print(f"Unique coordinates: {len(coord_map)}")
    print(f"Ambiguous coordinates: {ambiguous}")
    print(f"Failures: {failures}")

    if failures == 0:
        print("PASS: coordinate is lossless for relation state.")
    else:
        print("FAIL: coordinate is ambiguous.")

    return rows


all_rows = []

all_rows += test_coordinate(
    "coord_RA_RD",
    lambda a, b, s: (s[1], s[2])  # R_A, R_D
)

all_rows += test_coordinate(
    "coord_RA_RD_T",
    lambda a, b, s: (s[1], s[2], s[4])  # R_A, R_D, T
)

all_rows += test_coordinate(
    "coord_Y_RA_RD",
    lambda a, b, s: (s[0], s[1], s[2])  # Y, R_A, R_D
)

all_rows += test_coordinate(
    "coord_Y_RA_RD_T",
    lambda a, b, s: (s[0], s[1], s[2], s[4])  # Y, R_A, R_D, T
)

df = pd.DataFrame(all_rows)
df.to_csv("analysis/phi_p8_compressed_inverse_test.csv", index=False)

print("\nSaved: analysis/phi_p8_compressed_inverse_test.csv")
