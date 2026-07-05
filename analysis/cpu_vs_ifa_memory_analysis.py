import pandas as pd

def relation_state(A, B, width=4):
    mask = (1 << width) - 1

    Y  = (A + B) & mask
    RA = A & B
    RD = A ^ B
    R0 = (~A & ~B) & mask

    # transport chain
    t = 0
    T = 0
    for i in range(width):
        ai = (A >> i) & 1
        bi = (B >> i) & 1

        agree = ai & bi
        disagree = ai ^ bi

        t_next = agree | (disagree & t)

        if t_next:
            T |= (1 << i)

        t = t_next

    return Y, RA, RD, R0, T


rows = []

# --------------------------------------------------
# ANALYSIS 1: EASY CASE
# --------------------------------------------------

A = 13
B = 6
width = 4

Y, RA, RD, R0, T = relation_state(A, B, width)

# CPU does ADD, later recomputes AND/XOR/transport
cpu_add_ops = 40
cpu_recompute_ops = 16
cpu_total = cpu_add_ops + cpu_recompute_ops

# Ifa stores relation state once, later reads it
ifa_add_ops = 40
ifa_recompute_ops = 0
ifa_total = ifa_add_ops

rows.append({
    "analysis": "easy_relation_reuse",
    "A": A,
    "B": B,
    "Y": Y,
    "Agreement_RA": RA,
    "Disagreement_RD": RD,
    "Toggle_R0": R0,
    "Transport_T": T,
    "CPU_ops": cpu_total,
    "IFA_ops": ifa_total,
    "Ops_saved": cpu_total - ifa_total,
    "CPU_memory_state_bits": width,
    "IFA_REM_state_bits": 5 * width,
    "Memory_overhead_x": 5,
    "CPU_recomputes_relation": 1,
    "IFA_reads_relation": 1
})

# --------------------------------------------------
# ANALYSIS 2: COMPLEX BARREL LOOP CASE
# --------------------------------------------------

RA_mem = 0x4
RD_mem = 0xB
T_mem  = 0xC
R0_mem = 0x0

odu_new_ra = 0x2

cpu_ops_total = 0
ifa_ops_total = 0

for cycle in range(8):

    # CPU equivalent:
    # must select/recompute relation-like values repeatedly
    cpu_ops_this_cycle = 16
    cpu_ops_total += cpu_ops_this_cycle

    # Ifa RBL:
    # hardwired output + register rotation + one merge XOR
    ifa_ops_this_cycle = 4
    ifa_ops_total += ifa_ops_this_cycle

    Y_rel = RA_mem

    rows.append({
        "analysis": "complex_relation_barrel_loop",
        "cycle": cycle,
        "A": None,
        "B": None,
        "Y": Y_rel,
        "Agreement_RA": RA_mem,
        "Disagreement_RD": RD_mem,
        "Toggle_R0": R0_mem,
        "Transport_T": T_mem,
        "CPU_ops": cpu_ops_total,
        "IFA_ops": ifa_ops_total,
        "Ops_saved": cpu_ops_total - ifa_ops_total,
        "CPU_memory_state_bits": width,
        "IFA_REM_state_bits": 5 * width,
        "Memory_overhead_x": 5,
        "CPU_recomputes_relation": 1,
        "IFA_reads_relation": 1
    })

    next_RA = RD_mem ^ odu_new_ra

    R0_mem = RA_mem
    T_mem  = R0_mem
    RD_mem = T_mem
    RA_mem = next_RA


df = pd.DataFrame(rows)

df.to_csv("analysis/cpu_vs_ifa_memory_analysis.csv", index=False)

print(df)

print("\nSUMMARY")
print("-------")
print("Saved: analysis/cpu_vs_ifa_memory_analysis.csv")

easy = df[df.analysis == "easy_relation_reuse"].iloc[0]
print("\nEasy case:")
print(f"CPU ops = {easy.CPU_ops}")
print(f"Ifa ops = {easy.IFA_ops}")
print(f"Ops saved = {easy.Ops_saved}")

complex_last = df[df.analysis == "complex_relation_barrel_loop"].iloc[-1]
print("\nComplex case:")
print(f"CPU cumulative ops = {complex_last.CPU_ops}")
print(f"Ifa cumulative ops = {complex_last.IFA_ops}")
print(f"Ops saved = {complex_last.Ops_saved}")
