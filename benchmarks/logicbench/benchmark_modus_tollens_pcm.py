import json
from pathlib import Path
from collections import Counter

DATA = Path("benchmarks/LogicBench/data/LogicBench(Eval)/BQA/propositional_logic/modus_tollens/data_instances.json")

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


def phi_coordinate(a, b):
    _, ra, rd, _, t = relation_state(a, b)
    return (ra, rd, t)


def symbol_code(symbol):
    """
    Stable symbolic encoding for logic symbols.
    P -> 1
    Q -> 2
    NOT_P -> 129
    NOT_Q -> 130

    This is the first simple symbolic-to-coordinate bridge.
    Later the assembler will assign these codes.
    """
    table = {
        "P": 0x01,
        "Q": 0x02,
        "NOT_P": 0x81,
        "NOT_Q": 0x82,
    }
    return table[symbol]


def modus_tollens_coordinate():
    """
    Modus Tollens pattern:

        P -> Q
        not Q
        therefore not P

    We encode the reusable reasoning state as three Φ-P coordinates:
        rule_coord      = coord(P, Q)
        fact_coord      = coord(Q, NOT_Q)
        conclusion_coord= coord(P, NOT_P)

    This is now coordinate-based, not just axiom-name based.
    """
    rule_coord = phi_coordinate(symbol_code("P"), symbol_code("Q"))
    fact_coord = phi_coordinate(symbol_code("Q"), symbol_code("NOT_Q"))
    conclusion_coord = phi_coordinate(symbol_code("P"), symbol_code("NOT_P"))

    return (rule_coord, fact_coord, conclusion_coord)


def load_rows():
    data = json.loads(DATA.read_text(encoding="utf-8"))

    rows = []
    for sample in data["samples"]:
        for qa_id, qa in enumerate(sample["qa_pairs"]):
            rows.append({
                "axiom": data["axiom"],
                "sample_id": sample["id"],
                "qa_id": qa_id,
                "context": sample["context"],
                "question": qa["question"],
                "answer": qa["answer"].lower(),
            })

    return rows


def run():
    rows = load_rows()

    cpu_recomputes = 0
    ifa_rpc_exec = 0
    pcm_hits = 0
    pcm = set()
    coord_counter = Counter()

    for row in rows:
        cpu_recomputes += 1

        key = modus_tollens_coordinate()
        coord_counter[key] += 1

        if key in pcm:
            pcm_hits += 1
        else:
            ifa_rpc_exec += 1
            pcm.add(key)

    total = len(rows)
    reuse_ratio = pcm_hits / total if total else 0

    print()
    print("======================================")
    print("LOGICBENCH MODUS TOLLENS PCM BENCH")
    print("======================================")
    print(f"Cases                 : {total}")
    print(f"CPU recomputes        : {cpu_recomputes}")
    print(f"Ifá RPC executions    : {ifa_rpc_exec}")
    print(f"PCM coordinate hits   : {pcm_hits}")
    print(f"Unique PCM keys       : {len(pcm)}")
    print(f"Reuse ratio           : {reuse_ratio:.3f}")
    print(f"Reuse percent         : {reuse_ratio*100:.2f}%")
    print()
    print("PCM key used:")
    for k in pcm:
        print(k)


if __name__ == "__main__":
    run()
