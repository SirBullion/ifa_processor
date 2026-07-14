#!/usr/bin/env python3
import json, re
from pathlib import Path

BASE = Path("LogicBench/data/LogicBench(Eval)/BQA/propositional_logic")
NEG_MARKERS = ["n't", "not ", "won't", "wasn't", "isn't", "doesn't"]

def is_negated(text):
    return any(m in text.lower() for m in NEG_MARKERS)

def derive_modus_tollens(sample, qa):
    return "yes" if (not is_negated(qa["question"])) == False else "no"

def derive_hypothetical_syllogism(sample, qa):
    m = re.match(r"^\s*if (.+?),\s*does this .+? that (.+?)\??\s*$", qa["question"], re.IGNORECASE)
    if not m: return None
    a, c = m.group(1), m.group(2)
    return "yes" if (not is_negated(a)) and (not is_negated(c)) else "no"

def derive_constructive_dilemma(sample, qa):
    m = re.match(r"^.*\(a\)\s*(.+?)\s+and\s+\(b\)\s*(.+?)\s*$", qa["question"], re.IGNORECASE)
    if not m: return None
    a, b = m.group(1), m.group(2)
    return "yes" if (not is_negated(a)) and (not is_negated(b)) else "no"

def derive_disjunctive_syllogism(sample, qa):
    m = re.match(r"^.*?(?:mean|imply|infer|entail)s?\s+that\s+(.+?)\??\s*$", qa["question"], re.IGNORECASE)
    claim = m.group(1) if m else qa["question"]
    return "yes" if not is_negated(claim) else "no"

DERIVERS = {
    "modus_tollens": derive_modus_tollens,
    "hypothetical_syllogism": derive_hypothetical_syllogism,
    "constructive_dilemma": derive_constructive_dilemma,
    "disjunctive_syllogism": derive_disjunctive_syllogism,
}

def run_axiom(axiom):
    data = json.loads((BASE / axiom / "data_instances.json").read_text())
    deriver = DERIVERS[axiom]
    total = correct = unparsed = 0
    mismatches = []
    for sample in data["samples"]:
        for qa in sample["qa_pairs"]:
            total += 1
            computed = deriver(sample, qa)
            da = qa["answer"].strip().lower()
            if computed is None:
                unparsed += 1
                mismatches.append((sample["id"], qa["question"], da, "UNPARSED"))
            elif computed == da:
                correct += 1
            else:
                mismatches.append((sample["id"], qa["question"], da, computed))
    return {"axiom": axiom, "total": total, "correct": correct, "unparsed": unparsed,
            "accuracy": 100*correct/total if total else 0, "mismatches": mismatches}

def main():
    results = [run_axiom(ax) for ax in DERIVERS]
    grand_total = grand_correct = 0
    for r in results:
        print(f"\n[{r['axiom']}] {r['correct']}/{r['total']} = {r['accuracy']:.2f}%")
        for sid, q, da, ca in r["mismatches"][:10]:
            print(f"  sample {sid}: \"{q}\" dataset={da} computed={ca}")
        grand_total += r["total"]; grand_correct += r["correct"]
    print(f"\nOVERALL: {grand_correct}/{grand_total} ({100*grand_correct/grand_total:.2f}%)")
    out = Path("analysis/logicbench_v37_results.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print("Saved:", out)

if __name__ == "__main__":
    main()
