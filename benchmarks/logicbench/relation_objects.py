import json
from pathlib import Path


def relation_objects(lir):

    objects = []

    for rule in lir["rules"]:

        objects.append({

            "type": "RULE",

            "relation": rule["type"],

            "lhs": rule["if"],

            "rhs": rule["then"]

        })

    for fact in lir["facts"]:

        objects.append({

            "type": "FACT",

            "symbol": fact["symbol"],

            "truth": fact["truth"]

        })

    objects.append({

        "type": "QUERY",

        "symbol": lir["query"]["symbol"],

        "truth": lir["query"]["truth"]

    })

    return objects


if __name__ == "__main__":

    lirs = json.loads(
        Path("benchmarks/logicbench/normalized_lir.json").read_text()
    )

    relation_db = []

    for lir in lirs:

        relation_db.append(relation_objects(lir))

    out = Path("benchmarks/logicbench/relation_objects.json")

    out.write_text(
        json.dumps(relation_db, indent=2)
    )

    print("Objects:", len(relation_db))

    print()

    print(json.dumps(relation_db[0], indent=2))

    print()

    print("Saved:", out)
