#!/usr/bin/env python3
import json
from pathlib import Path

WIDTH = 8
MASK = (1 << WIDTH) - 1
MOD = 1 << WIDTH
TRUE_CODE = 255
FALSE_CODE = 0
SYMBOL_CODE = {"P": 1, "Q": 2, "R": 3, "S": 4}

def relation_state(a, b):
    y = (a + b) & MASK
    ra = a & b
    rd = a ^ b
    r0 = (~(a | b)) & MASK
    diff = abs(a - b)
    wrap = MOD - diff
    t = min(diff, wrap)
    return {"Y": y, "R_A": ra, "R_D": rd, "R_0": r0, "T": t}

def truth_code(b):
    return TRUE_CODE if b else FALSE_CODE

def generate_states(lir):
    states = []
    for rule in lir["rules"]:
        A = SYMBOL_CODE[rule["if"]]; B = SYMBOL_CODE[rule["then"]]
        states.append({"type": "RULE", "lhs": rule["if"], "rhs": rule["then"], **relation_state(A, B)})
    for fact in lir["facts"]:
        A = SYMBOL_CODE[fact["symbol"]]; B = truth_code(fact["truth"])
        states.append({"type": "FACT", "symbol": fact["symbol"], **relation_state(A, B)})
    q = lir["query"]
    A = SYMBOL_CODE[q["symbol"]]; B = truth_code(q["truth"])
    states.append({"type": "QUERY", "symbol": q["symbol"], **relation_state(A, B)})
    return states

def derive_modus_tollens(lir):
    rule = lir["rules"][0]
    fact = lir["facts"][0]
    if fact["symbol"] != rule["then"] or fact["truth"] is not False:
        raise ValueError(f"LIR {lir.get('id')} does not match the modus-tollens shape.")
    derived_P_truth = False
    A = SYMBOL_CODE[rule["if"]]
    derived_state = relation_state(A, truth_code(derived_P_truth))
    q = lir["query"]
    claimed_state = relation_state(SYMBOL_CODE[q["symbol"]], truth_code(q["truth"]))
    claim_is_correct = (q["truth"] == derived_P_truth)
    return {
        "derived_P_truth": derived_P_truth, "derived_state": derived_state,
        "claimed_state": claimed_state, "states_match": derived_state == claimed_state,
        "claim_is_correct": claim_is_correct,
        "computed_answer": "yes" if claim_is_correct else "no",
    }

def verify_row(lir):
    result = derive_modus_tollens(lir)
    dataset_answer = lir["raw"]["answer"].strip().lower()
    return {
        "id": lir["id"], "question": lir["raw"]["question"],
        "dataset_answer": dataset_answer,
        "computed_answer": result["computed_answer"],
        "derived_P_truth": result["derived_P_truth"],
        "pass": result["computed_answer"] == dataset_answer and result["claim_is_correct"] == lir["expected"],
    }

def run():
    lirs = json.loads(Path("benchmarks/logicbench/tiny_lir.json").read_text())
    all_states = [generate_states(l) for l in lirs]
    Path("benchmarks/logicbench/relation_states.json").write_text(json.dumps(all_states, indent=2))
    results = [verify_row(l) for l in lirs]
    Path("benchmarks/logicbench/derivation_results.json").write_text(json.dumps(results, indent=2))
    print("======================================")
    print("MODUS TOLLENS: RELATION-GATE DERIVATION")
    print("======================================")
    n_pass = sum(r["pass"] for r in results)
    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        print(f"[{status}] {r['id']}  Q: {r['question']}")
        print(f"  dataset={r['dataset_answer']}  computed={r['computed_answer']}  derived_P={r['derived_P_truth']}")
    print(f"\nResult: {n_pass}/{len(results)} rows verified correctly.")

if __name__ == "__main__":
    run()
