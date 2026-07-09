# ============================================================
# IFÁ V4 vs Classical CPU Benchmark
#
# Compares:
#   CPU-style recomputation
#   V4 RMU relation reuse
#
# Workloads:
#   1. no_reuse
#   2. high_reuse
#   3. complex_transform
# ============================================================

from ifa_v4_rmu import RelationMemoryUnit, compute_frame, DEPTH, MASK


# ------------------------------------------------------------
# Transform helpers
# ------------------------------------------------------------

def ogunda_shift(x):
    return (x + 1) & MASK


def otura_shift(x):
    return (x + 4) & MASK


def complement(x):
    return x ^ MASK


def reversal(x):
    bits = f"{x:08b}"
    return int(bits[::-1], 2)


# ------------------------------------------------------------
# Workload generators
# ------------------------------------------------------------

def workload_no_reuse():
    pairs = []
    for a in range(0, 256, 17):
        for b in range(0, 256, 31):
            pairs.append((a, b))
    return pairs[:64]


def workload_high_reuse():
    base = [
        (0x0D, 0x06),
        (0x07, 0x08),
        (0x01, 0x02),
        (0x03, 0x04),
        (0x09, 0x0A),
        (0x0B, 0x0C),
        (0x0F, 0x00),
        (0x05, 0x06),
    ]

    pairs = []
    for _ in range(8):
        pairs.extend(base)

    return pairs


def workload_complex_transform():
    seeds = [
        (0x0D, 0x06),
        (0x07, 0x08),
        (0x21, 0x42),
        (0x33, 0xCC),
        (0x55, 0xAA),
        (0x81, 0x18),
        (0xF0, 0x0F),
        (0xA5, 0x5A),
    ]

    pairs = []

    for a, b in seeds:
        pairs.append((a, b))

        pairs.append((ogunda_shift(a), ogunda_shift(b)))
        pairs.append((otura_shift(a), otura_shift(b)))
        pairs.append((complement(a), complement(b)))
        pairs.append((reversal(a), reversal(b)))

        # repeat original and transformed patterns
        pairs.append((a, b))
        pairs.append((ogunda_shift(a), ogunda_shift(b)))
        pairs.append((otura_shift(a), otura_shift(b)))

    # repeat whole structured workload twice
    return pairs * 2


# ------------------------------------------------------------
# Cost models
# ------------------------------------------------------------

def cpu_cost(workload):
    """
    CPU recomputes relation every time.
    """
    return {
        "ops": len(workload),
        "rpc_exec": len(workload),
        "memory_lookup": 0,
        "memory_store": 0,
        "hits": 0,
        "misses": len(workload),
    }


def v4_cost(workload, depth=DEPTH):
    """
    V4 uses RMU lookup.
    Miss = compute + store.
    Hit  = reuse.
    """
    rmu = RelationMemoryUnit(depth=depth)

    rpc_exec = 0

    for a, b in workload:
        _, hit = rmu.access(a, b)

        if not hit:
            rpc_exec += 1

    return {
        "ops": len(workload),
        "rpc_exec": rpc_exec,
        "memory_lookup": len(workload),
        "memory_store": rmu.stores,
        "hits": rmu.hits,
        "misses": rmu.misses,
        "evictions": rmu.evictions,
        "hit_rate": rmu.stats()["hit_rate"],
    }


def estimate_cycles_cpu(cost):
    """
    Simple CPU estimate:
      each request recomputes relation.
    """
    RPC_COST = 10
    return cost["rpc_exec"] * RPC_COST


def estimate_cycles_v4(cost):
    """
    Simple V4 estimate:
      lookup cost = 1
      hit cost    = lookup only
      miss cost   = lookup + RPC + store
    """
    LOOKUP_COST = 1
    RPC_COST = 10
    STORE_COST = 1

    return (
        cost["memory_lookup"] * LOOKUP_COST
        + cost["rpc_exec"] * RPC_COST
        + cost["memory_store"] * STORE_COST
    )


# ------------------------------------------------------------
# Benchmark runner
# ------------------------------------------------------------

def run_case(name, workload):
    cpu = cpu_cost(workload)
    v4 = v4_cost(workload)

    cpu_cycles = estimate_cycles_cpu(cpu)
    v4_cycles = estimate_cycles_v4(v4)

    saved_rpc = cpu["rpc_exec"] - v4["rpc_exec"]
    saved_cycles = cpu_cycles - v4_cycles

    saved_pct = (saved_cycles / cpu_cycles) * 100 if cpu_cycles else 0.0

    print("\n" + "=" * 80)
    print(f"WORKLOAD: {name}")
    print("=" * 80)

    print(f"Total operations        : {len(workload)}")

    print("\nCPU MODEL")
    print("-" * 80)
    print(f"RPC recomputes          : {cpu['rpc_exec']}")
    print(f"Estimated cycles        : {cpu_cycles}")

    print("\nV4 MODEL")
    print("-" * 80)
    print(f"RMU hits                : {v4['hits']}")
    print(f"RMU misses              : {v4['misses']}")
    print(f"RMU stores              : {v4['memory_store']}")
    print(f"RMU evictions           : {v4['evictions']}")
    print(f"Hit rate                : {v4['hit_rate']:.4f}")
    print(f"RPC recomputes          : {v4['rpc_exec']}")
    print(f"Estimated cycles        : {v4_cycles}")

    print("\nADVANTAGE")
    print("-" * 80)
    print(f"RPC recomputes saved    : {saved_rpc}")
    print(f"Estimated cycles saved  : {saved_cycles}")
    print(f"Estimated cycle saving  : {saved_pct:.2f}%")

    return {
        "name": name,
        "ops": len(workload),
        "cpu_cycles": cpu_cycles,
        "v4_cycles": v4_cycles,
        "saved_cycles": saved_cycles,
        "saved_pct": saved_pct,
        "hit_rate": v4["hit_rate"],
    }


def main():
    print("IFÁ V4 vs CPU COMPLEX BENCHMARK")
    print("=" * 80)

    results = []

    results.append(run_case("NO_REUSE", workload_no_reuse()))
    results.append(run_case("HIGH_REUSE", workload_high_reuse()))
    results.append(run_case("COMPLEX_TRANSFORM", workload_complex_transform()))

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    for r in results:
        print(
            f"{r['name']:20s} "
            f"ops={r['ops']:3d} "
            f"hit_rate={r['hit_rate']:.4f} "
            f"cpu_cycles={r['cpu_cycles']:5d} "
            f"v4_cycles={r['v4_cycles']:5d} "
            f"saved={r['saved_cycles']:5d} "
            f"saving={r['saved_pct']:6.2f}%"
        )


if __name__ == "__main__":
    main()
