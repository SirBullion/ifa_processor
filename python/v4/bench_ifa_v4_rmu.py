# ============================================================
# IFÁ V4 RMU Benchmark
#
# Measures:
# - total operations
# - hits
# - misses
# - hit rate
# - avoided RPC recomputations
# ============================================================

from ifa_v4_rmu import RelationMemoryUnit, DEPTH


def make_reuse_workload():
    base = [
        (13, 6),
        (7, 8),
        (1, 2),
        (3, 4),
        (9, 10),
        (11, 12),
        (15, 0),
        (5, 6),
    ]

    workload = []

    # repeat same relations many times
    for _ in range(8):
        workload.extend(base)

    return workload


def run_benchmark():
    workload = make_reuse_workload()
    rmu = RelationMemoryUnit(depth=DEPTH)

    recompute_without_rmu = len(workload)
    recompute_with_rmu = 0

    print("IFÁ V4 RMU BENCHMARK")
    print("=" * 70)

    for cycle, (A, B) in enumerate(workload):
        _, hit = rmu.access(A, B)

        if not hit:
            recompute_with_rmu += 1

        print(
            f"cycle={cycle:03d} "
            f"A=0x{A:02X} B=0x{B:02X} "
            f"{'HIT ' if hit else 'MISS'}"
        )

    saved = recompute_without_rmu - recompute_with_rmu

    print("\nSUMMARY")
    print("=" * 70)
    print("workload ops:", len(workload))
    print("RPC recomputes without RMU:", recompute_without_rmu)
    print("RPC recomputes with RMU:", recompute_with_rmu)
    print("RPC recomputes saved:", saved)
    print("RMU hits:", rmu.hits)
    print("RMU misses:", rmu.misses)
    print("RMU stores:", rmu.stores)
    print("RMU evictions:", rmu.evictions)
    print("RMU hit rate:", round(rmu.stats()["hit_rate"], 4))


if __name__ == "__main__":
    run_benchmark()
