import json
from pathlib import Path
cases = [
    {
        "id": 1,
        "axiom": "modus_tollens",
        "context": "Liam had finished his work early for the day, which meant that he would typically have ordered pizza for dinner. However, he decided against ordering pizza.",
        "qa": [
            {"question": "Does this imply that liam didn't finish his work early?", "answer": "yes", "query": {"symbol": "P", "truth": False}},
            {"question": "Does this entail that liam finished his work early?", "answer": "no", "query": {"symbol": "P", "truth": True}},
        ],
        "symbols": {"P": "liam_finished_work_early", "Q": "liam_ordered_pizza"},
    },
    {
        "id": 3,
        "axiom": "modus_tollens",
        "context": "If Mason decides to leave his job, he will not receive any salary. However, Mason still receives his salary.",
        "qa": [
            {"question": "Does this infer that mason didn't leave his job?", "answer": "yes", "query": {"symbol": "P", "truth": False}}
        ],
        "symbols": {"P": "mason_left_job", "Q": "mason_receives_salary"},
    },
]
def build_lir(case, qa_index, qa):
    return {
        "lir_version": "0.1", "source": "LogicBench_tiny",
        "logic_type": "propositional_logic", "axiom": case["axiom"],
        "id": f"case_{case['id']}_qa_{qa_index}",
        "raw": {"context": case["context"], "question": qa["question"], "answer": qa["answer"]},
        "symbols": case["symbols"],
        "rules": [{"id": "R1", "type": "implies", "if": "P", "then": "Q"}],
        "facts": [{"symbol": "Q", "truth": False}],
        "query": qa["query"],
        "expected": qa["answer"].lower() == "yes",
    }
lirs = []
for case in cases:
    for i, qa in enumerate(case["qa"]):
        lirs.append(build_lir(case, i, qa))
out = Path("benchmarks/logicbench/tiny_lir.json")
out.write_text(json.dumps(lirs, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Saved {len(lirs)} LIR cases to {out}")
