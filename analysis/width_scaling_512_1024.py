import pandas as pd

WIDTHS = [256, 512, 1024, 2048]

rows = []

for w in WIDTHS:
    cpu_bits = w
    full_rem_bits = 5 * w
    rmu_bits = 3 * w + 2

    rows.append({
        "width": w,
        "cpu_bits": cpu_bits,
        "full_rem_bits": full_rem_bits,
        "rmu_bits": rmu_bits,
        "full_rem_over_cpu": full_rem_bits / cpu_bits,
        "rmu_over_cpu": rmu_bits / cpu_bits,
        "rmu_saves_bits": full_rem_bits - rmu_bits,
        "rmu_saves_percent": 100 * (full_rem_bits - rmu_bits) / full_rem_bits
    })

df = pd.DataFrame(rows)

print(df.to_string(index=False))

df.to_csv("analysis/width_scaling_512_1024.csv", index=False)

print("\nSaved: analysis/width_scaling_512_1024.csv")
