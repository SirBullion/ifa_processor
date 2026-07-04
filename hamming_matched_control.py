import pandas as pd
import random
from scipy.stats import ttest_ind

random.seed(42)

START = 4294967000
END   = 4294969000

# Load existing candidate labels
df0 = pd.read_csv("ifa_same_width_control_with_hamming.csv")
cand = df0[["candidate", "is_prime", "hamming_weight"]].drop_duplicates()

primes = cand[cand.is_prime == 1]
comps  = cand[cand.is_prime == 0]

# Match composites to primes by same hamming weight
matched_rows = []

for _, p in primes.iterrows():
    hw = p.hamming_weight
    possible = comps[comps.hamming_weight == hw]

    if len(possible) == 0:
        continue

    c = possible.sample(1, random_state=random.randint(0, 999999)).iloc[0]

    matched_rows.append(p)
    matched_rows.append(c)

matched = pd.DataFrame(matched_rows)

print("Matched candidates:", len(matched))
print(matched.groupby("is_prime")["hamming_weight"].describe())

rows = []

for _, row in matched.iterrows():
    candidate = int(row.candidate)
    is_prime = int(row.is_prime)
    hw = int(row.hamming_weight)

    for _ in range(10):
        r = random.getrandbits(64) | 1

        ra = candidate & r
        rd = candidate ^ r
        r0 = (~candidate & ~r) & ((1 << 64) - 1)

        rows.append({
            "candidate": candidate,
            "is_prime": is_prime,
            "hamming_weight": hw,
            "random_odd": r,
            "P_A": ra.bit_count(),
            "P_D": rd.bit_count(),
            "P_0": r0.bit_count(),
        })

df = pd.DataFrame(rows)

print("\n=== Matched Relation Means ===")
print(df.groupby("is_prime")[["P_A", "P_D", "P_0"]].mean())

print("\n=== Matched t-tests ===")
prime = df[df.is_prime == 1]
comp  = df[df.is_prime == 0]

for col in ["P_A", "P_D", "P_0"]:
    print(col, ttest_ind(prime[col], comp[col]))

df.to_csv("ifa_hamming_matched_control.csv", index=False)
print("\nSaved: ifa_hamming_matched_control.csv")

