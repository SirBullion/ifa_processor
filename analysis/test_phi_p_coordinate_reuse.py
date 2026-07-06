import pandas as pd
from collections import Counter, defaultdict

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


rows = []
coord_counter = Counter()
coord_locations = defaultdict(list)

x = 5

for step in range(STEPS):
    exp_next = (x * BASE) & MASK

    q = x // DIVISOR
    r = x % DIVISOR

    workloads = [
        ("exp", x, BASE),
        ("div", x, DIVISOR),
    ]

    for branch, a, b in workloads:
        c = coord(a, b)

        coord_counter[c] += 1
        coord_locations[c].append((step, branch, a, b))

        rows.append({
            "step": step,
            "branch": branch,
            "A": a,
            "B": b,
            "coordinate": c,
            "R_A": c[0],
            "R_D": c[1],
            "T": c[2],
            "seen_count_after": coord_counter[c],
            "is_reuse": coord_counter[c] > 1,
            "exp_next": exp_next,
            "quotient": q,
            "remainder": r,
        })

    x = exp_next


df = pd.DataFrame(rows)

total_coords = len(df)
unique_coords = len(coord_counter)
reused_events = sum(count - 1 for count in coord_counter.values() if count > 1)
reused_unique_coords = sum(1 for count in coord_counter.values() if count > 1)
hit_rate = reused_events / total_coords

summary = pd.DataFrame([{
    "width": WIDTH,
    "steps": STEPS,
    "total_coordinate_events": total_coords,
    "unique_coordinates": unique_coords,
    "reused_events": reused_events,
    "unique_reused_coordinates": reused_unique_coords,
    "coordinate_hit_rate": hit_rate,
    "reuse_percent": hit_rate * 100,
}])

reuse_rows = []
for c, count in coord_counter.items():
    if count > 1:
        reuse_rows.append({
            "coordinate": c,
            "R_A": c[0],
            "R_D": c[1],
            "T": c[2],
            "count": count,
            "locations": coord_locations[c],
        })

reuse_df = pd.DataFrame(reuse_rows).sort_values(
    by="count", ascending=False
) if reuse_rows else pd.DataFrame()

print("\n=== COORDINATE REUSE SUMMARY ===")
print(summary.to_string(index=False))

print("\n=== REUSED COORDINATES ===")
if len(reuse_df) > 0:
    print(reuse_df.to_string(index=False))
else:
    print("No repeated coordinates found.")

df.to_csv("analysis/phi_p_coordinate_reuse_trace.csv", index=False)
summary.to_csv("analysis/phi_p_coordinate_reuse_summary.csv", index=False)
reuse_df.to_csv("analysis/phi_p_coordinate_reuse_repeated.csv", index=False)

print("\nSaved:")
print("analysis/phi_p_coordinate_reuse_trace.csv")
print("analysis/phi_p_coordinate_reuse_summary.csv")
print("analysis/phi_p_coordinate_reuse_repeated.csv")
