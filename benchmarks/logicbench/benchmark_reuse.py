from run_ifaasm_logic import run_ifaasm


def benchmark(program):
    passed, facts, trace = run_ifaasm(program)

    rpc_exec = 0
    reuse_hits = 0
    cache = set()

    for t in trace:
        if t.startswith("RULE:"):
            rule = t.replace("RULE:", "").strip()

            if rule in cache:
                reuse_hits += 1
            else:
                rpc_exec += 1
                cache.add(rule)

    total = rpc_exec + reuse_hits

    print()
    print("======================================")
    print("IFÁ LOGIC REUSE BENCHMARK")
    print("======================================")
    print(f"Program            : {program}")
    print(f"PASS               : {passed}")
    print(f"RPC Executions     : {rpc_exec}")
    print(f"Reuse Hits         : {reuse_hits}")

    if total:
        print(f"Reuse Ratio        : {reuse_hits/total:.3f}")

    print(f"Unique Relations   : {len(cache)}")


if __name__ == "__main__":
    benchmark("benchmarks/logicbench/modus_tollens_1.ifaasm")
