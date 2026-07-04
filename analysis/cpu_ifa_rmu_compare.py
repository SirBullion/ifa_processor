import pandas as pd
import matplotlib.pyplot as plt

WIDTHS = [2, 4, 8, 16, 32, 64, 128, 256]
CYCLES = [1, 2, 4, 8, 16, 32]

rows = []

for w in WIDTHS:
    cpu_bits = w
    ifa_full_bits = 5 * w
    ifa_rmu_bits = 3 * w + 2   # compressed RMU/RPE model

    for c in CYCLES:
        # simple timing model
        # CPU recomputes relation each cycle
        cpu_ops = c * 16

        # Ifa reads/rotates relation state
        ifa_ops = c * 4

        rows.append({
            "width": w,
            "cycles": c,

            "cpu_memory_bits": cpu_bits,
            "ifa_full_rem_bits": ifa_full_bits,
            "ifa_rmu_compressed_bits": ifa_rmu_bits,

            "full_rem_over_cpu": ifa_full_bits / cpu_bits,
            "rmu_over_cpu": ifa_rmu_bits / cpu_bits,

            "cpu_ops": cpu_ops,
            "ifa_ops": ifa_ops,
            "ops_saved": cpu_ops - ifa_ops,
            "speedup_model": cpu_ops / ifa_ops
        })

df = pd.DataFrame(rows)

print("\n=== MEMORY COMPARISON ===")
print(df[df["cycles"] == 1][[
    "width",
    "cpu_memory_bits",
    "ifa_full_rem_bits",
    "ifa_rmu_compressed_bits",
    "full_rem_over_cpu",
    "rmu_over_cpu"
]].to_string(index=False))

print("\n=== TIME / OPERATION COMPARISON ===")
print(df[df["width"] == 4][[
    "cycles",
    "cpu_ops",
    "ifa_ops",
    "ops_saved",
    "speedup_model"
]].to_string(index=False))

df.to_csv("analysis/cpu_ifa_rmu_compare.csv", index=False)
print("\nSaved: analysis/cpu_ifa_rmu_compare.csv")

# Plot memory overhead
mem = df[df["cycles"] == 1]

plt.figure()
plt.plot(mem["width"], mem["full_rem_over_cpu"], marker="o", label="Full REM / CPU")
plt.plot(mem["width"], mem["rmu_over_cpu"], marker="o", label="Compressed RMU / CPU")
plt.xlabel("Word width (bits)")
plt.ylabel("Memory overhead vs CPU")
plt.title("CPU vs Ifa Memory Overhead")
plt.legend()
plt.grid(True)
plt.savefig("analysis/cpu_ifa_memory_overhead.png", dpi=200)

# Plot operation model
time = df[df["width"] == 4]

plt.figure()
plt.plot(time["cycles"], time["cpu_ops"], marker="o", label="CPU recomputation ops")
plt.plot(time["cycles"], time["ifa_ops"], marker="o", label="Ifa RMU relation ops")
plt.xlabel("Cycles")
plt.ylabel("Operation model")
plt.title("CPU vs Ifa Relation Reuse Cost")
plt.legend()
plt.grid(True)
plt.savefig("analysis/cpu_ifa_time_model.png", dpi=200)

print("Saved plots:")
print("analysis/cpu_ifa_memory_overhead.png")
print("analysis/cpu_ifa_time_model.png")
