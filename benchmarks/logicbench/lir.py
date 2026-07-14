import json
from pathlib import Path

ROOT = Path("benchmarks/LogicBench/data/LogicBench(Eval)")


def load_first_modus_tollens():
    path = ROOT / "BQA/propositional_logic/modus_tollens/data_instances.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    sample = data["samples"][0]
    qa = sample["qa_pairs"][0]

    return data, sample, qa


def build_lir_modus_tollens(data, sample, qa):
    """
    Manual LIR v0.1 for first Modus Tollens sample.

    Pattern:
        P -> Q
        not Q
        therefore not P
    """

    lir = {
        "lir_version": "0.1",
        "source": "LogicBench",
        "logic_type": data["type"],
        "axiom": data["axiom"],
        "id": f"{data['axiom']}_{sample['id']}_0",

        "raw": {
            "context": sample["context"],
            "question": qa["question"],
            "answer": qa["answer"],
        },

        "symbols": {
            "P": "liam_finished_work_early",
            "Q": "liam_ordered_pizza",
        },

        "rules": [
            {
                "id": "R1",
                "type": "implies",
                "if": "P",
                "then": "Q",
            }
        ],

        "facts": [
            {
                "symbol": "Q",
                "truth": False,
            }
        ],

        "query": {
            "symbol": "P",
            "truth": False,
        },

        "expected": qa["answer"].lower() == "yes",
    }

    return lir


if __name__ == "__main__":
    data, sample, qa = load_first_modus_tollens()
    lir = build_lir_modus_tollens(data, sample, qa)

    print(json.dumps(lir, indent=2, ensure_ascii=False))

    out = Path("benchmarks/logicbench/lir_modus_tollens_1.json")
    out.write_text(json.dumps(lir, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print(f"Saved: {out}")
