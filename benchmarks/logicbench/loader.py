import json
from pathlib import Path


ROOT = Path("benchmarks/LogicBench/data/LogicBench(Eval)")


def load_logicbench_file(path):
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))

    rows = []
    logic_type = data.get("type")
    axiom = data.get("axiom")

    for sample in data.get("samples", []):
        sample_id = sample.get("id")
        context = sample.get("context", "")

        for qid, qa in enumerate(sample.get("qa_pairs", [])):
            rows.append({
                "logic_type": logic_type,
                "axiom": axiom,
                "sample_id": sample_id,
                "qa_id": qid,
                "context": context,
                "question": qa.get("question", ""),
                "answer": qa.get("answer", ""),
            })

    return rows


if __name__ == "__main__":
    p = ROOT / "BQA/propositional_logic/modus_tollens/data_instances.json"
    rows = load_logicbench_file(p)

    print(f"Loaded rows: {len(rows)}")
    print()

    for r in rows[:5]:
        print("AXIOM:", r["axiom"])
        print("CONTEXT:", r["context"])
        print("QUESTION:", r["question"])
        print("ANSWER:", r["answer"])
        print("-" * 80)
