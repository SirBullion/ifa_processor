import pandas as pd
from collections import Counter, defaultdict

WIDTH = 8
MOD = 1 << WIDTH
MASK = MOD - 1

STEPS = 64
MODULES = 8

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

# repeated modular-robot sensor states
module_state = [20, 20, 21, 21, 80, 80, 120, 120]

rows = []
counter = Counter()
locations = defaultdict(list)

for step in range(STEPS):
    # slow drift every 8 steps, but repeated pairs remain common
    if step > 0 and step % 8 == 0:
        module_state = [(x + 1) & MASK for x in module_state]

    for i in range(MODULES):
        for j in range(i + 1, MODULES):
            a = module_state[i]
            b = module_state[j]
            c = coord(a, b)

            counter[c] += 1
            locations[c].append((step, i, j, a, b))

            rows.append({
                "step": step,
                "module_i": i,
                "module_j": j,
                "A": a,
                "B": b,
                "R_A": c[0],
                "R_D": c[1],
                "T": c[2],
                "coordinate": c,
                "seen_count_after": counter[c],
                "is_reuse": counter[c] > 1,
            })

df = pd.DataFrame(rows)

total = len(df)
unique = len(counter)
reuse_events = sum(v - 1 for v in counter.values() if v > 1)
unique_reused = sum(1 for v in counter.values() if v > 1)
hit_rate = reuse_events / total

summary = pd.DataFrame([{
    "width": WIDTH,
    "steps": STEPS,
    "modules": MODULES,
    "total_coordinate_events": total,
    "unique_coordinates": unique,
    "reused_events": reuse_events,
    "unique_reused_coordinates": unique_reused,
    "coordinate_hit_rate": hit_rate,
    "reuse_percent": hit_rate * 100,
}])

reuse_rows = []
for c, count in counter.items():
    if count > 1:
        reuse_rows.append({
            "coordinate": c,
            "R_A": c[0],
            "R_D": c[1],
            "T": c[2],
            "count": count,
            "first_locations": locations[c][:5],
        })

reuse_df = pd.DataFrame(reuse_rows).sort_values(
    by="count", ascending=False
)

print("\n=== ROBOT COORDINATE REUSE SUMMARY ===")
print(summary.to_string(index=False))

print("\n=== TOP REUSED COORDINATES ===")
print(reuse_df.head(20).to_string(index=False))

df.to_csv("analysis/phi_p_robot_reuse_trace.csv", index=False)
summary.to_csv("analysis/phi_p_robot_reuse_summary.csv", index=False)
reuse_df.to_csv("analysis/phi_p_robot_reuse_repeated.csv", index=False)

print("\nSaved:")
print("analysis/phi_p_robot_reuse_trace.csv")
print("analysis/phi_p_robot_reuse_summary.csv")
print("analysis/phi_p_robot_reuse_repeated.csv")

