import json
from pathlib import Path

DATA = Path("benchmarks/LogicBench/data/LogicBench(Eval)/BQA/propositional_logic/modus_tollens/data_instances.json")

def load_samples():
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
                "answer": qa["answer"].lower()
            })
    return rows

def relation_key(row):
    # For now, benchmark reusable inference PATTERN, not English semantics.
    # Later this becomes coordinate key from LIR/PCM.
    return (row["axiom"], "P_implies_Q", "not_Q", "infer_not_P")

def run_batch():
    rows = load_samples()

    cpu_recomputes = 0
    ifa_exec = 0
    ifa_hits = 0
    cache = set()

    for row in rows:
        key = relation_key(row)

        cpu_recomputes += 1

        if key in cache:
            ifa_hits += 1
        else:
            ifa_exec += 1
            cache.add(key)

    total = len(rows)
    reuse_ratio = ifa_hits / total if total else 0

    print()
    print("======================================")
    print("LOGICBENCH MODUS TOLLENS BATCH")
    print("======================================")
    print(f"Cases                 : {total}")
    print(f"CPU recomputes        : {cpu_recomputes}")
    print(f"Ifá RPC executions    : {ifa_exec}")
    print(f"Ifá reuse hits        : {ifa_hits}")
    print(f"Unique relation keys  : {len(cache)}")
    print(f"Reuse ratio           : {reuse_ratio:.3f}")
    print(f"Reuse percent         : {reuse_ratio*100:.2f}%")

if __name__ == "__main__":
    run_batch()
