import json
from pathlib import Path
from collections import Counter

WIDTH = 8
MASK = (1 << WIDTH) - 1
MOD = 1 << WIDTH

CODE = {
    "RULE": 0x10,
    "FACT": 0x20,
    "QUERY": 0x30,

    "implies": 0x01,
    "true": 0x7F,
    "false": 0x80,

    "P": 0x01,
    "Q": 0x02,
    "R": 0x03,
    "S": 0x04,
}


def relation_state(a, b):
    y = (a + b) & MASK
    ra = a & b
    rd = a ^ b
    r0 = (~(a | b)) & MASK

    diff = abs(a - b)
    wrap = MOD - diff
    t = min(diff, wrap) & MASK

    return y, ra, rd, r0, t


def phi_coord(a, b):
    _, ra, rd, _, t = relation_state(a, b)
    return (ra, rd, t)


def encode_object(obj):
    if obj["type"] == "RULE":
        # RULE implies P Q
        return (
            phi_coord(CODE["RULE"], CODE[obj["relation"]]),
            phi_coord(CODE[obj["lhs"]], CODE[obj["rhs"]]),
        )

    if obj["type"] == "FACT":
        truth_code = CODE["true"] if obj["truth"] else CODE["false"]
        return (
            phi_coord(CODE["FACT"], CODE[obj["symbol"]]),
            phi_coord(CODE[obj["symbol"]], truth_code),
        )

    if obj["type"] == "QUERY":
        truth_code = CODE["true"] if obj["truth"] else CODE["false"]
        return (
            phi_coord(CODE["QUERY"], CODE[obj["symbol"]]),
            phi_coord(CODE[obj["symbol"]], truth_code),
        )

    raise ValueError(f"Unknown object type: {obj['type']}")


def main():
    relation_db = json.loads(
        Path("benchmarks/logicbench/relation_objects.json").read_text()
    )

    encoded_cases = []
    counter = Counter()

    for case in relation_db:
        encoded = []
        for obj in case:
            coord = encode_object(obj)
            encoded.append({
                "object": obj,
                "phi_coordinate": coord,
            })
            counter[str(coord)] += 1

        encoded_cases.append(encoded)

    out = Path("benchmarks/logicbench/phi_coordinates.json")
    out.write_text(json.dumps(encoded_cases, indent=2), encoding="utf-8")

    total = sum(counter.values())
    unique = len(counter)
    hits = total - unique

    print("Φ-P coordinate encoding complete")
    print("--------------------------------")
    print(f"Cases: {len(encoded_cases)}")
    print(f"Coordinate objects: {total}")
    print(f"Unique coordinates: {unique}")
    print(f"Reuse hits: {hits}")
    print(f"Reuse percent: {hits / total * 100:.2f}%")
    print()
    print(json.dumps(encoded_cases[0], indent=2))
    print()
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
