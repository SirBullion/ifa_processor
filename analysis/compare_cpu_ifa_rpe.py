import pandas as pd

WIDTHS = [2, 4, 8, 16, 32, 64, 128, 256]

rows = []

for w in WIDTHS:
    cpu_bits = w                       # CPU stores Y only
    ifa_full_bits = 5 * w              # Y + RA + RD + R0 + T
    ifa_compressed_bits = 3 * w + 2    # Y + primary + secondary/delta + mode

    rows.append({
        "WIDTH": w,
        "CPU_bits": cpu_bits,
        "IFA_full_REM_bits": ifa_full_bits,
        "IFA_RPE_compressed_bits": ifa_compressed_bits,
        "Full_REM_over_CPU": ifa_full_bits / cpu_bits,
        "RPE_over_CPU": ifa_compressed_bits / cpu_bits,
        "RPE_saves_vs_full_bits": ifa_full_bits - ifa_compressed_bits,
        "RPE_saves_vs_full_percent": round(
            100 * (ifa_full_bits - ifa_compressed_bits) / ifa_full_bits, 2
        )
    })

df = pd.DataFrame(rows)

print(df.to_string(index=False))

df.to_csv("analysis/cpu_vs_ifa_rpe_memory_comparison.csv", index=False)

print("\nSaved: analysis/cpu_vs_ifa_rpe_memory_comparison.csv")
