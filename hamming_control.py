import pandas as pd
from scipy.stats import ttest_ind, pearsonr

df = pd.read_csv("ifa_same_width_control.csv")

# one row per candidate
cand = df[["candidate", "is_prime"]].drop_duplicates().copy()

cand["hamming_weight"] = cand["candidate"].apply(lambda x: int(x).bit_count())
cand["zero_bits"] = 64 - cand["hamming_weight"]

print("=== Candidate Hamming Weight by Class ===")
print(cand.groupby("is_prime")[["hamming_weight", "zero_bits"]].describe())

prime = cand[cand.is_prime == 1]
comp  = cand[cand.is_prime == 0]

print("\n=== t-test: Hamming Weight ===")
print(ttest_ind(prime.hamming_weight, comp.hamming_weight))

print("\n=== Mean Hamming Weight ===")
print(cand.groupby("is_prime")[["hamming_weight", "zero_bits"]].mean())

# merge hamming weight back into relation dataset
df = df.merge(cand[["candidate", "hamming_weight", "zero_bits"]], on="candidate", how="left")

print("\n=== Correlation with Relation Features ===")
for col in ["P_A", "P_D", "P_0"]:
    r, p = pearsonr(df["hamming_weight"], df[col])
    print(f"hamming_weight vs {col}: r={r:.4f}, p={p:.3e}")

df.to_csv("ifa_same_width_control_with_hamming.csv", index=False)
print("\nSaved: ifa_same_width_control_with_hamming.csv")
