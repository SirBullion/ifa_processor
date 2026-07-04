import itertools
import pandas as pd

# ============================================================
# TEST 1:
# Φ + P COMBINED RECOVERY TEST
#
# x → Φ(x) → P(Φ(x)) → P⁻¹ → Φ⁻¹ → x
# ============================================================

# ----------------------------
# Basic helpers
# ----------------------------

def not_bit(x):
    return "1" if x == "0" else "0"

def xor_bit(a, b):
    return str(int(a) ^ int(b))

def xnor_bit(a, b):
    return str(1 - (int(a) ^ int(b)))

def hamming(a, b):
    return sum(x != y for x, y in zip(a, b))

# ----------------------------
# Φ Anchor–Agreement Transform
# (A,B) → (A, A==B)
# ----------------------------

def phi_pair(pair):
    A, B = pair
    anchor = A
    agreement = xnor_bit(A, B)
    return anchor + agreement

def phi_inv_pair(pair):
    anchor, agreement = pair

    if agreement == "1":
        B = anchor
    else:
        B = not_bit(anchor)

    return anchor + B

def phi_bits(bits):
    out = ""
    for i in range(0, len(bits), 2):
        out += phi_pair(bits[i:i+2])
    return out

def phi_inv_bits(bits):
    out = ""
    for i in range(0, len(bits), 2):
        out += phi_inv_pair(bits[i:i+2])
    return out

# ----------------------------
# P C4 Rotation
# 00 → 01 → 10 → 11 → 00
# P⁻¹ = P³
# ----------------------------

P_map = {
    "00": "01",
    "01": "10",
    "10": "11",
    "11": "00",
}

P_inv_map = {v: k for k, v in P_map.items()}

def P_pair(pair):
    return P_map[pair]

def P_inv_pair(pair):
    return P_inv_map[pair]

def P_bits(bits):
    out = ""
    for i in range(0, len(bits), 2):
        out += P_pair(bits[i:i+2])
    return out

def P_inv_bits(bits):
    out = ""
    for i in range(0, len(bits), 2):
        out += P_inv_pair(bits[i:i+2])
    return out

# ----------------------------
# Test all 256 8-bit addresses
# ----------------------------

rows = []

for i in range(256):
    x = format(i, "08b")

    phi_x = phi_bits(x)
    p_phi_x = P_bits(phi_x)

    inv_p = P_inv_bits(p_phi_x)
    recovered = phi_inv_bits(inv_p)

    rows.append({
        "Input": x,
        "Phi": phi_x,
        "P_after_Phi": p_phi_x,
        "P_inverse": inv_p,
        "Recovered": recovered,
        "Recovery_OK": recovered == x
    })

combined_df = pd.DataFrame(rows)

print("=" * 100)
print("TEST 1: Φ + P COMBINED RECOVERY")
print("=" * 100)

print("Total states:", len(combined_df))
print("Recovery failures:", (~combined_df["Recovery_OK"]).sum())

print("\nSample:")
print(combined_df.head(16).to_string(index=False))

combined_df.to_csv("phi_P_combined_recovery_test.csv", index=False)
combined_df.to_excel("phi_P_combined_recovery_test.xlsx", index=False)

print("\nSaved:")
print("phi_P_combined_recovery_test.csv / .xlsx")


# ============================================================
# TEST 2:
# BIT-FLIP DIFFUSION / SECURITY-STYLE TEST
#
# x → Φ → P
# flip one bit in input
# compare output Hamming distance
# ============================================================

def F(bits):
    """
    Combined forward transform.
    """
    return P_bits(phi_bits(bits))

diffusion_rows = []

for i in range(256):
    x = format(i, "08b")
    y = F(x)

    for bit_pos in range(8):
        x_list = list(x)
        x_list[bit_pos] = not_bit(x_list[bit_pos])
        x_flip = "".join(x_list)

        y_flip = F(x_flip)

        diffusion_rows.append({
            "Input": x,
            "Input_Flipped": x_flip,
            "Flipped_Position": bit_pos,
            "Output": y,
            "Output_After_Input_Flip": y_flip,
            "Input_Hamming": hamming(x, x_flip),
            "Output_Hamming": hamming(y, y_flip),
            "Diffusion_Gain": hamming(y, y_flip) - 1
        })

diffusion_df = pd.DataFrame(diffusion_rows)

print("\n" + "=" * 100)
print("TEST 2: BIT-FLIP DIFFUSION TEST")
print("=" * 100)

print("Total tests:", len(diffusion_df))
print("\nOutput Hamming distance counts:")
print(diffusion_df["Output_Hamming"].value_counts().sort_index())

print("\nMean output Hamming distance:", diffusion_df["Output_Hamming"].mean())
print("Min output Hamming distance:", diffusion_df["Output_Hamming"].min())
print("Max output Hamming distance:", diffusion_df["Output_Hamming"].max())

print("\nBy flipped bit position:")
print(
    diffusion_df
    .groupby("Flipped_Position")["Output_Hamming"]
    .agg(["count", "mean", "min", "max"])
)

diffusion_df.to_csv("phi_P_bitflip_diffusion_test.csv", index=False)
diffusion_df.to_excel("phi_P_bitflip_diffusion_test.xlsx", index=False)

print("\nSaved:")
print("phi_P_bitflip_diffusion_test.csv / .xlsx")
