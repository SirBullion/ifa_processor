#!/usr/bin/env python3

from collections import Counter
import math


# ============================================================
# IFÁ ALGEBRA AUDIT
# P2, P4, P8 vs ordinary CPU operations
# ============================================================

def bits(x, n):
    return [(x >> i) & 1 for i in reversed(range(n))]


def bitstr(x, n):
    return format(x, f"0{n}b")


# ------------------------------------------------------------
# Ifá P2
# A' = A
# B' = ~(A XOR B)
# ------------------------------------------------------------

def p2_pair(a, b):
    ap = a
    bp = 1 ^ (a ^ b)
    return ap, bp


def p_even(x, n):
    """
    Apply P2 independently to adjacent bit pairs.
    Bits are treated MSB to LSB.
    """
    bs = bits(x, n)
    out = []

    for i in range(0, n, 2):
        a, b = bs[i], bs[i + 1]
        ap, bp = p2_pair(a, b)
        out.extend([ap, bp])

    y = 0
    for b in out:
        y = (y << 1) | b

    return y


def xor_imm(x, n, imm):
    return x ^ imm


def add_imm(x, n, imm):
    return (x + imm) % (1 << n)


def permutation_table(fn, n):
    return {x: fn(x) for x in range(1 << n)}


def is_injective(table):
    return len(set(table.values())) == len(table)


def inverse_table(table):
    return {v: k for k, v in table.items()}


def compose_table(t1, t2):
    """
    composition t1 after t2: x -> t1[t2[x]]
    """
    return {x: t1[t2[x]] for x in t1}


def identity_table(n):
    return {x: x for x in range(1 << n)}


def permutation_order(table, n, max_power=10000):
    ident = identity_table(n)
    cur = table.copy()

    for k in range(1, max_power + 1):
        if cur == ident:
            return k
        cur = compose_table(table, cur)

    return None


def cycles(table, n):
    seen = set()
    out = []

    for x in range(1 << n):
        if x in seen:
            continue

        cyc = []
        cur = x

        while cur not in seen:
            seen.add(cur)
            cyc.append(cur)
            cur = table[cur]

        out.append(cyc)

    return out


def hamming_distance(a, b):
    return (a ^ b).bit_count()


def hamming_profile(table):
    return Counter(hamming_distance(x, y) for x, y in table.items())


def fixed_points(table):
    return [x for x, y in table.items() if x == y]


def entropy_unique_outputs(table):
    c = Counter(table.values())
    total = sum(c.values())

    h = 0.0
    for count in c.values():
        p = count / total
        h -= p * math.log2(p)

    return h, len(c)


def print_section(title):
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)


def audit_operation(name, fn, n):
    table = permutation_table(fn, n)
    cyc = cycles(table, n)
    order = permutation_order(table, n)
    fixed = fixed_points(table)
    hp = hamming_profile(table)
    h, unique = entropy_unique_outputs(table)

    print_section(f"AUDIT: {name} on {n} bits")

    print(f"states               : {1 << n}")
    print(f"injective            : {is_injective(table)}")
    print(f"unique outputs       : {unique}")
    print(f"entropy output       : {h:.6f} bits")
    print(f"permutation order    : {order}")
    print(f"cycle count          : {len(cyc)}")
    print(f"cycle length profile : {dict(Counter(len(c) for c in cyc))}")
    print(f"fixed points         : {len(fixed)}")
    print(f"hamming profile      : {dict(hp)}")

    print()
    print("sample mapping:")
    for x in range(min(16, 1 << n)):
        print(f"  {bitstr(x,n)} -> {bitstr(table[x],n)}")

    print()
    print("first cycles:")
    for c in cyc[:8]:
        print("  " + " -> ".join(bitstr(v, n) for v in c))

    return {
        "name": name,
        "n": n,
        "states": 1 << n,
        "injective": is_injective(table),
        "unique_outputs": unique,
        "entropy": h,
        "order": order,
        "cycle_count": len(cyc),
        "cycle_profile": dict(Counter(len(c) for c in cyc)),
        "fixed_points": len(fixed),
        "hamming_profile": dict(hp),
    }


def compare_operations():
    results = []

    for n in [2, 4, 8]:
        results.append(audit_operation(f"Ifa_P{n}", lambda x, n=n: p_even(x, n), n))

    results.append(audit_operation("XOR_IMM_A5", lambda x: xor_imm(x, 8, 0xA5), 8))
    results.append(audit_operation("ADD_IMM_01", lambda x: add_imm(x, 8, 0x01), 8))
    results.append(audit_operation("ADD_IMM_A5", lambda x: add_imm(x, 8, 0xA5), 8))

    print_section("SUMMARY COMPARISON")

    header = (
        f"{'operation':<14} {'bits':>4} {'states':>8} {'inj':>5} "
        f"{'order':>8} {'cycles':>8} {'fixed':>8} {'cycle_profile'}"
    )
    print(header)
    print("-" * len(header))

    for r in results:
        print(
            f"{r['name']:<14} {r['n']:>4} {r['states']:>8} "
            f"{str(r['injective']):>5} {str(r['order']):>8} "
            f"{r['cycle_count']:>8} {r['fixed_points']:>8} {r['cycle_profile']}"
        )

    print_section("INTERPRETATION")

    print("""
1. At the gate level, Ifá P2 is reducible to ordinary Boolean logic:

       A' = A
       B' = NOT(A XOR B)

   So the silicon-level primitives are conventional.

2. At the transformation level, P2/P4/P8 are reversible permutations.

3. P8 is not the same kind of operation as ADD.
   ADD_IMM_01 forms one 256-cycle rotation over the 8-bit state space.
   P8 forms many short cycles because it acts independently on bit-pairs.

4. This supports the architectural distinction:

       conventional CPU: arithmetic-centered
       Ifá CPU: transformation / Odu-state-centered

5. The novelty is not that the transistor gates are physically new.
   The novelty is that the architecture exposes a different native operation
   and gives binary states an Odu semantic interpretation.
""")


if __name__ == "__main__":
    compare_operations()
