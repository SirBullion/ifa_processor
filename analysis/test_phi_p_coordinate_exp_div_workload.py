import pandas as pd

WIDTH = 8
MOD = 1 << WIDTH
MASK = MOD - 1

BASE = 3
DIVISOR = 7
STEPS = 32

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

def inverse_from_coord(c):
    """
    Search inverse for WIDTH=8.
    Reconstruct relation state from (R_A, R_D, T).
    """
    target_ra, target_rd, target_t = c

    for a in range(MOD):
        for b in range(MOD):
            y, ra, rd, r0, t = relation_state(a, b)
            if (ra, rd, t) == (target_ra, target_rd, target_t):
                return y, ra, rd, r0, t

    return None

rows = []
pcm = {}   # Phi-P Coordinate Memory

x = 5

for step in range(STEPS):
    # Exponential-like branch
    exp_next = (x * BASE) & MASK

    # Division branch
    q = x // DIVISOR
    r = x % DIVISOR

    # Pair 1: exponent relation
    c_exp = coord(x, BASE)
    pcm[("exp", step)] = c_exp
    rec_exp = inverse_from_coord(c_exp)

    # Pair 2: division relation
    c_div = coord(x, DIVISOR)
    pcm[("div", step)] = c_div
    rec_div = inverse_from_coord(c_div)

    rows.append({
        "step": step,
        "x": x,
        "base": BASE,
        "divisor": DIVISOR,

        "exp_next": exp_next,
        "quotient": q,
        "remainder": r,

        "exp_coord_RA": c_exp[0],
        "exp_coord_RD": c_exp[1],
        "exp_coord_T": c_exp[2],

        "div_coord_RA": c_div[0],
        "div_coord_RD": c_div[1],
        "div_coord_T": c_div[2],

        "exp_reconstruct_ok": rec_exp is not None,
        "div_reconstruct_ok": rec_div is not None,

        "exp_Y_rec": rec_exp[0] if rec_exp else None,
        "div_Y_rec": rec_div[0] if rec_div else None,
    })

    # Chain update: exponential output becomes next x
    x = exp_next

df = pd.DataFrame(rows)

print(df.to_string(index=False))

print("\nSUMMARY")
print("-------")
print(f"Steps: {STEPS}")
print(f"PCM entries stored: {len(pcm)}")
print(f"All exp reconstructions OK: {df.exp_reconstruct_ok.all()}")
print(f"All div reconstructions OK: {df.div_reconstruct_ok.all()}")

df.to_csv("analysis/phi_p_coordinate_exp_div_workload.csv", index=False)

print("\nSaved: analysis/phi_p_coordinate_exp_div_workload.csv")
