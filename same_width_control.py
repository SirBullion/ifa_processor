import pandas as pd
import random
from sympy import isprime
from scipy.stats import ttest_ind

random.seed(42)

df0 = pd.read_csv("ifa_prime_dataset_100.csv")

candidates = df0[["candidate", "is_prime"]].drop_duplicates()

rows = []

for _, row in candidates.iterrows():
    c = int(row["candidate"])
    is_p = int(row["is_prime"])

    for _ in range(10):
        r = random.getrandbits(64) | 1  # random odd 64-bit

        ra = c & r
        rd = c ^ r
        r0 = (~c & ~r) & ((1 << 64) - 1)

        rows.append({
            "candidate": c,
            "is_prime": is_p,
            "random_odd": r,
            "P_A": ra.bit_count(),
            "P_D": rd.bit_count(),
            "P_0": r0.bit_count(),
        })

df = pd.DataFrame(rows)

print("=== Same-width control means ===")
print(df.groupby("is_prime")[["P_A", "P_D", "P_0"]].mean())

prime = df[df.is_prime == 1]
comp = df[df.is_prime == 0]

print("\n=== t-tests ===")
for col in ["P_A", "P_D", "P_0"]:
    print(col, ttest_ind(prime[col], comp[col]))

df.to_csv("ifa_same_width_control.csv", index=False)
print("\nSaved: ifa_same_width_control.csv")
