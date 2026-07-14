import json
from pathlib import Path

WIDTH = 8
MASK = (1 << WIDTH) - 1
MOD = 1 << WIDTH


def relation_state(a, b):

    y = (a + b) & MASK
    ra = a & b
    rd = a ^ b
    r0 = (~(a | b)) & MASK

    diff = abs(a - b)
    wrap = MOD - diff
    t = min(diff, wrap)

    return {
        "Y": y,
        "R_A": ra,
        "R_D": rd,
        "R_0": r0,
        "T": t,
    }


SYMBOL_CODE = {
    "P": 1,
    "Q": 2,
    "R": 3,
    "S": 4,
}


def generate_states(lir):

    states = []

    for rule in lir["rules"]:

        A = SYMBOL_CODE[rule["if"]]
        B = SYMBOL_CODE[rule["then"]]

        rs = relation_state(A, B)

        states.append({

            "type": "RULE",

            "lhs": rule["if"],

            "rhs": rule["then"],

            **rs

        })

    for fact in lir["facts"]:

        A = SYMBOL_CODE[fact["symbol"]]
        B = 255 if fact["truth"] else 0

        rs = relation_state(A, B)

        states.append({

            "type": "FACT",

            "symbol": fact["symbol"],

            **rs

        })

    q = lir["query"]

    A = SYMBOL_CODE[q["symbol"]]
    B = 255 if q["truth"] else 0

    rs = relation_state(A, B)

    states.append({

        "type": "QUERY",

        "symbol": q["symbol"],

        **rs

    })

    return states


if __name__ == "__main__":

    lirs = json.loads(
        Path("benchmarks/logicbench/tiny_lir.json").read_text()
    )

    all_states = []

    for lir in lirs:

        all_states.append(generate_states(lir))

    out = Path("benchmarks/logicbench/relation_states.json")

    out.write_text(json.dumps(all_states, indent=2))

    print(json.dumps(all_states, indent=2))

    print()

    print("Saved:", out)
