import json
import sys
import hashlib
from pathlib import Path
from collections import Counter

WIDTH = 8
MASK = (1 << WIDTH) - 1
MOD = 1 << WIDTH

def relation_state(a, b):
    y = (a + b) & MASK
    ra = a & b
    rd = a ^ b
    r0 = (~(a | b)) & MASK
    diff = abs(a - b)
    wrap = MOD - diff
    t = min(diff, wrap) & MASK
    return y, ra, rd, r0, t

def phi_coord(a, b):
    _, ra, rd, _, t = relation_state(a, b)
    return (ra, rd, t)

def byte_hash(text, salt):
    h = hashlib.sha256((salt + "::" + text).encode("utf-8")).digest()
    v = h[0]
    return v if v != 0 else 1

def not_code(x):
    return x ^ 0x80

def skeleton_key(axiom):
    return ("SKELETON", axiom)

def instance_key(axiom, context, question):
    # Honest per-row encoding: varies with actual LogicBench text.
    # This does not claim semantic parsing yet; it prevents fake constant reuse.
    base = context + " " + question

    P = byte_hash(base, "P")
    Q = byte_hash(base, "Q")
    R = byte_hash(base, "R")
    S = byte_hash(base, "S")

    if axiom == "modus_tollens":
        return (
            phi_coord(P, Q),
            phi_coord(Q, not_code(Q)),
            phi_coord(P, not_code(P)),
        )

    if axiom == "hypothetical_syllogism":
        return (
            phi_coord(P, Q),
            phi_coord(Q, R),
            phi_coord(P, R),
        )

    if axiom == "disjunctive_syllogism":
        return (
            phi_coord(P, Q),
            phi_coord(not_code(P), Q),
        )

    if axiom == "constructive_dilemma":
        return (
            phi_coord(P, Q),
            phi_coord(R, S),
            phi_coord(P, R),
        )

    return ("UNSUPPORTED", axiom, byte_hash(base, "fallback"))

def measure(keys):
    seen = set()
    hits = 0
    execs = 0

    for k in keys:
        if k in seen:
            hits += 1
        else:
            execs += 1
            seen.add(k)

    total = len(keys)
    return {
        "total": total,
        "execs": execs,
        "hits": hits,
        "unique": len(seen),
        "reuse_ratio": hits / total if total else 0,
    }

def run(json_file):
    data = json.loads(Path(json_file).read_text(encoding="utf-8"))
    axiom = data["axiom"]

    rows = []
    for sample in data["samples"]:
        for qa in sample["qa_pairs"]:
            rows.append((sample["context"], qa["question"], qa["answer"]))

    skeleton_keys = [skeleton_key(axiom) for _ in rows]
    instance_keys = [instance_key(axiom, c, q) for c, q, _ in rows]

    sk = measure(skeleton_keys)
    ik = measure(instance_keys)

    print()
    print("======================================")
    print("HONEST LOGICBENCH PCM BENCHMARK")
    print("======================================")
    print("Axiom:", axiom)
    print("Cases:", len(rows))

    print()
    print("[1] Skeleton / rule-shape reuse")
    print(f"Unique keys       : {sk['unique']}")
    print(f"RPC executions    : {sk['execs']}")
    print(f"Reuse hits        : {sk['hits']}")
    print(f"Reuse percent     : {sk['reuse_ratio']*100:.2f}%")

    print()
    print("[2] Instance coordinate reuse")
    print(f"Unique keys       : {ik['unique']}")
    print(f"RPC executions    : {ik['execs']}")
    print(f"Reuse hits        : {ik['hits']}")
    print(f"Reuse percent     : {ik['reuse_ratio']*100:.2f}%")

    print()
    print("Interpretation:")
    print("Skeleton reuse measures repeated logical form.")
    print("Instance reuse measures repeated concrete coordinate states.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 benchmark_logicbench_pcm_honest.py <data_instances.json>")
        sys.exit(1)

    run(sys.argv[1])
