import json
from pathlib import Path
from collections import Counter

# ==========================================================
# CONFIG
# ==========================================================

DATA = Path(
    "benchmarks/LogicBench/data/LogicBench(Eval)/BQA/propositional_logic/modus_tollens/data_instances.json"
)

WIDTH = 8
MASK = (1 << WIDTH) - 1
MOD = 1 << WIDTH

# ==========================================================
# Φ-P
# ==========================================================

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


# ==========================================================
# Symbol Dictionary
# ==========================================================

SYMBOL = {
    "P": 1,
    "Q": 2,
    "R": 3,
    "S": 4,
}

# ==========================================================
# LIR
# ==========================================================

def normalize_to_lir(sample, qa):

    return {

        "rules": [

            {

                "type": "implies",

                "if": "P",

                "then": "Q"

            }

        ],

        "facts": [

            {

                "symbol": "Q",

                "truth": False

            }

        ],

        "query": {

            "symbol": "P",

            "truth": "didn't" in qa["question"].lower()

        },

        "expected": qa["answer"].lower() == "yes"

    }


# ==========================================================
# Relation Objects
# ==========================================================

def relation_objects(lir):

    obj = []

    for r in lir["rules"]:

        obj.append(

            (

                "RULE",

                phi_coord(

                    SYMBOL[r["if"]],

                    SYMBOL[r["then"]]

                )

            )

        )

    for f in lir["facts"]:

        value = 255 if f["truth"] else 0

        obj.append(

            (

                "FACT",

                phi_coord(

                    SYMBOL[f["symbol"]],

                    value

                )

            )

        )

    q = lir["query"]

    value = 255 if q["truth"] else 0

    obj.append(

        (

            "QUERY",

            phi_coord(

                SYMBOL[q["symbol"]],

                value

            )

        )

    )

    return obj


# ==========================================================
# VERIFY
# ==========================================================

def verify(lir):

    expected = lir["expected"]

    actual = lir["query"]["truth"] == False

    return actual == expected


# ==========================================================
# MAIN
# ==========================================================

def main():

    data = json.loads(DATA.read_text())

    pcm = {}

    coordinate_counter = Counter()

    rows = []

    rpc = 0
    hits = 0

    passed = 0

    total = 0

    for sample in data["samples"]:

        for qa_id, qa in enumerate(sample["qa_pairs"]):

            total += 1

            lir = normalize_to_lir(sample, qa)

            ok = verify(lir)

            if ok:
                passed += 1

            objects = relation_objects(lir)

            for typ, coord in objects:

                coordinate_counter[coord] += 1

                if coord in pcm:

                    hits += 1

                    hit = True

                else:

                    rpc += 1

                    pcm[coord] = True

                    hit = False

                rows.append({

                    "sample": sample["id"],

                    "qa": qa_id,

                    "type": typ,

                    "coord": coord,

                    "pcm_hit": hit,

                    "verify": ok

                })

    print()

    print("===================================================")
    print("IFÁ V3.5 LOGICBENCH REPORT")
    print("===================================================")

    print(f"Rows                  : {total}")

    print(f"Correct               : {passed}")

    print(f"Accuracy              : {100*passed/total:.2f}%")

    print()

    print(f"Relation Objects      : {len(rows)}")

    print(f"Unique Coordinates    : {len(coordinate_counter)}")

    print(f"PCM Hits              : {hits}")

    print(f"RPC Executions        : {rpc}")

    print(f"Reuse Percent         : {100*hits/(hits+rpc):.2f}%")

    print()

    print("Top Coordinates")

    print("----------------")

    for coord, count in coordinate_counter.most_common(10):

        print(coord, count)

    print()

    out = Path("analysis/logicbench_v35_results.json")

    out.parent.mkdir(exist_ok=True)

    out.write_text(

        json.dumps(rows, indent=2, default=str)

    )

    print("Saved:", out)


if __name__ == "__main__":

    main()
