#!/usr/bin/env python3
import json, re, sys, hashlib
from pathlib import Path

WIDTH = 8
MASK = (1 << WIDTH) - 1
_STOPWORDS = {"If","However","Although","Despite","Because","Since","When","While",
              "Given","This","The","Does","Do","In","On","At","As","But","And","So","Yet","After","Before"}

def extract_subject(context):
    caps = re.findall(r"\b[A-Z][a-z]+\b", context)
    for w in caps:
        if w not in _STOPWORDS:
            return w
    return "unknown"

def content_hash(text, salt, width_bits=16):
    h = hashlib.sha256((salt + "::" + text).encode("utf-8")).digest()
    v = int.from_bytes(h[:2], "big") % ((1 << width_bits) - 1)
    return (v + 1) & MASK

def negation_polarity(question):
    q = question.lower()
    neg_markers = ["n't", "not ", "didn't", "doesn't", "won't", "wasn't"]
    return any(m in q for m in neg_markers)

def normalize_to_lir(row, axiom, sample_id):
    if axiom == "modus_tollens":
        ctx = row["context"]
        subject = extract_subject(ctx)
        P_content = content_hash(ctx, "P")
        Q_content = content_hash(ctx, "Q")
        expected_neg = negation_polarity(row["question"])
        predicted_answer = "yes" if expected_neg else "no"
        answer_consistent = (predicted_answer == row["answer"].lower())
        return {
            "axiom": axiom, "sample_id": sample_id, "subject": subject,
            "symbols": {"P": P_content, "Q": Q_content},
            "rules": [{"type": "implies", "if": "P", "then": "Q"}],
            "facts": [{"symbol": "Q", "truth": False}],
            "query": {"symbol": "P", "truth": False},
            "question": row["question"], "answer": row["answer"].lower(),
            "answer_consistent_with_axiom": answer_consistent,
            "context_preview": ctx[:100],
        }
    raise ValueError(f"Unsupported axiom: {axiom}")

def load_rows(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = []
    for sample in data["samples"]:
        for qa in sample["qa_pairs"]:
            rows.append({"sample_id": sample["id"], "context": sample["context"],
                         "question": qa["question"], "answer": qa["answer"]})
    return data["axiom"], rows

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 semantic_normalizer.py <data_instances.json>")
        sys.exit(1)
    axiom, rows = load_rows(sys.argv[1])
    lirs = [normalize_to_lir(r, axiom, r["sample_id"]) for r in rows]
    out = Path("benchmarks/logicbench/normalized_lir.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(lirs, indent=2), encoding="utf-8")
    inconsistent = [l for l in lirs if not l["answer_consistent_with_axiom"]]
    print(f"Normalized rows: {len(lirs)}")
    print(f"Saved: {out}")
    print(f"Answer/axiom-polarity mismatches: {len(inconsistent)} / {len(lirs)}")
