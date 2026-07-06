import numpy as np
import pandas as pd
from collections import Counter, defaultdict

WIDTH = 8
MASK = (1 << WIDTH) - 1

N = 8
np.random.seed(42)

# ----------------------------------------------------
# Random matrices
# ----------------------------------------------------

A = np.random.randint(0, 32, (N, N), dtype=np.uint16)
B = np.random.randint(0, 32, (N, N), dtype=np.uint16)

# ----------------------------------------------------
# Relation functions
# ----------------------------------------------------

def relation_state(a, b):

    y = (a + b) & MASK
    ra = a & b
    rd = a ^ b
    r0 = (~(a | b)) & MASK

    diff = abs(int(a) - int(b))
    wrap = (1 << WIDTH) - diff
    t = min(diff, wrap)

    return y, ra, rd, r0, t


def coordinate(a, b):
    _, ra, rd, _, t = relation_state(a, b)
    return (ra, rd, t)


# ----------------------------------------------------
# Statistics
# ----------------------------------------------------

coord_counter = Counter()
coord_locations = defaultdict(list)

relation_counter = Counter()

C = np.zeros((N, N), dtype=np.uint16)

relation_events = 0

# ----------------------------------------------------
# Matrix multiplication
# ----------------------------------------------------

for i in range(N):

    for j in range(N):

        total = 0

        for k in range(N):

            a = int(A[i, k])
            b = int(B[k, j])

            total += a * b

            relation_events += 1

            c = coordinate(a, b)

            coord_counter[c] += 1
            coord_locations[c].append((i, j, k))

            relation_counter[(a, b)] += 1

        C[i, j] = total & MASK

# ----------------------------------------------------
# Results
# ----------------------------------------------------

total_coords = relation_events
unique_coords = len(coord_counter)

reuse_events = sum(v - 1 for v in coord_counter.values() if v > 1)

unique_reused = sum(1 for v in coord_counter.values() if v > 1)

hit_rate = reuse_events / total_coords

summary = pd.DataFrame([{
    "Matrix_Size": N,
    "Total_Relation_Events": relation_events,
    "Unique_Coordinates": unique_coords,
    "Coordinate_Reuses": reuse_events,
    "Reuse_Hit_Rate": hit_rate,
    "Reuse_Percent": hit_rate * 100
}])

reuse_rows = []

for c, count in coord_counter.items():

    if count > 1:

        reuse_rows.append({

            "Coordinate": c,

            "R_A": c[0],

            "R_D": c[1],

            "T": c[2],

            "Count": count,

            "First_Locations": coord_locations[c][:5]

        })

reuse_df = pd.DataFrame(reuse_rows)

reuse_df = reuse_df.sort_values("Count", ascending=False)

# ----------------------------------------------------

print()

print("======================================")
print("IFA MATRIX MULTIPLICATION REUSE REPORT")
print("======================================")

print(summary.to_string(index=False))

print()

print("Top reused coordinates")

print(reuse_df.head(20).to_string(index=False))

print()

summary.to_csv(
    "analysis/matrix_reuse_summary.csv",
    index=False
)

reuse_df.to_csv(
    "analysis/matrix_reuse_details.csv",
    index=False
)

print("Saved:")
print(" analysis/matrix_reuse_summary.csv")
print(" analysis/matrix_reuse_details.csv")

