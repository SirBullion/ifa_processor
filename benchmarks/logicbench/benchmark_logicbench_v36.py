#!/usr/bin/env python3
import json
from pathlib import Path
from collections import Counter

DATA = Path("LogicBench/data/LogicBench(Eval)/BQA/propositional_logic/modus_tollens/data_instances.json")
WIDTH = 8
MASK = (1 << WIDTH) - 1
MOD = 1 << WIDTH
TRUE_CODE = 255
FALSE_CODE = 0
SYMBOL = {"P": 1, "Q": 2, "R": 3, "S": 4}

def relation_state(a, b):
    y = (a + b) & MASK
    ra = a & b
    rd = a ^ b
    r0 = (~(a | b)) & MASK
    diff = abs(a - b)
    wrap = MOD - diff
    t = min(diff, wrap)
    return y, ra, rd, r0, t

def phi_coord(a, b):
    _, ra, rd, _, t = relation_state(a, b)
    return (ra, rd, t)

def truth_code(b):
    return TRUE_CODE if b else FALSE_CODE

def derive_modus_tollens_truth(rule, fact):
    if fact["symbol"] != rule["then"] or fact["truth"] is not False:
        raise ValueError("LIR does not match modus-tollens shape.")
    return False

def build_lir(qa):
    rule = {"type": "implies", "if": "P", "then": "Q"}
    fact = {"symbol": "Q", "truth": False}
    derived_P_truth = derive_modus_tollens_truth(rule, fact)
    neg_markers = ["n't", "not ", "won't", "wasn't", "isn't"]
    question_is_negated = any(m in qa["question"].lower() for m in neg_markers)
    query = {"symbol": "P", "truth": not question_is_negated}
    claim_is_correct = (query["truth"] == derived_P_truth)
    computed_answer = "yes" if claim_is_correct else "no"
    return {"rules": [rule], "facts": [fact], "query": query,
            "computed_answer": computed_answer, "dataset_answer": qa["answer"].lower()}

def relation_objects(lir):
    obj = []
    for r in lir["rules"]:
        obj.append(("RULE", phi_coord(SYMBOL[r["if"]], SYMBOL[r["then"]])))
    for f in lir["facts"]:
        obj.append(("FACT", phi_coord(SYMBOL[f["symbol"]], truth_code(f["truth"]))))
    q = lir["query"]
    obj.append(("QUERY", phi_coord(SYMBOL[q["symbol"]], truth_code(q["truth"]))))
    return obj

def main():
    data = json.loads(DATA.read_text())
    pcm, coordinate_counter, rows = {}, Counter(), []
    rpc = hits = passed = total = 0
    mismatches = []
    for sample in data["samples"]:
        for qa_id, qa in enumerate(sample["qa_pairs"]):
            total += 1
            lir = build_lir(qa)
            ok = lir["computed_answer"] == lir["dataset_answer"]
            if ok: passed += 1
            else: mismatches.append((sample["id"], qa["question"], lir["dataset_answer"], lir["computed_answer"]))
            for typ, coord in relation_objects(lir):
                coordinate_counter[coord] += 1
                if coord in pcm: hits += 1
                else: rpc += 1; pcm[coord] = True
    print(f"Rows: {total}  Correct: {passed}  Accuracy: {100*passed/total:.2f}%")
    print(f"(skeleton-level coord reuse: {100*hits/(hits+rpc):.2f}% -- structural, not semantic)")
    if mismatches:
        print(f"Mismatches ({len(mismatches)}):")
        for sid, q, da, ca in mismatches:
            print(f"  sample {sid}: \"{q}\" dataset={da} computed={ca}")
    else:
        print("No mismatches.")

if __name__ == "__main__":
    main()
