from pathlib import Path


def run_ifaasm(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()

    symbols = {}
    rules = []
    facts = {}
    assertions = []
    trace = []

    for raw in lines:
        line = raw.split(";")[0].strip()
        if not line:
            continue

        parts = line.split()
        op = parts[0]

        if op == "SYM":
            symbols[parts[1]] = True

        elif op == "RULE_IMP":
            rules.append((parts[1], parts[2]))
            trace.append(f"RULE: {parts[1]} -> {parts[2]}")

        elif op == "FACT":
            facts[parts[1]] = True
            trace.append(f"FACT: {parts[1]} = true")

        elif op == "FACT_NOT":
            facts[parts[1]] = False
            trace.append(f"FACT: {parts[1]} = false")

        elif op == "INFER_MT":
            p, q = parts[1], parts[2]
            if (p, q) in rules and facts.get(q) is False:
                facts[p] = False
                trace.append(f"MODUS TOLLENS: {p}->{q}, not {q}; therefore not {p}")

        elif op == "ASSERT":
            assertions.append((parts[1], True))

        elif op == "ASSERT_NOT":
            assertions.append((parts[1], False))

        elif op == "PRINT":
            pass

        elif op == "HALT":
            break

        else:
            trace.append(f"UNKNOWN OP: {op}")

    passed = True
    for sym, expected in assertions:
        got = facts.get(sym)
        ok = got == expected
        trace.append(f"ASSERT {sym} expected={expected} got={got} ok={ok}")
        passed = passed and ok

    return passed, facts, trace


if __name__ == "__main__":
    path = "benchmarks/logicbench/modus_tollens_1.ifaasm"
    passed, facts, trace = run_ifaasm(path)

    print("=== IFÁ LOGIC ASM SIM ===")
    for t in trace:
        print(t)

    print()
    print("FACTS:", facts)
    print("PASS:", passed)
