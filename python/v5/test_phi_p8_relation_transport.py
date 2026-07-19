#!/usr/bin/env python3
"""
Experiment:

    Binary
        ↓
    Relation frame

versus

    Binary
        ↓
    Φ-P8
        ↓
    Relation frame

This classifies exactly how Φ-P8 transports relation states.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.v5.ifa_phi_p8 import phi_p8, bit_string   # noqa: E402


WIDTH = 8
MASK = 0xFF

RESULTS = PROJECT_ROOT / "python/v5/results"
RESULTS.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Relation:
    Y: int
    RA: int
    RD: int
    R0: int
    T: int

    def key(self):
        return (self.Y, self.RA, self.RD, self.R0, self.T)


def relation(a: int, b: int) -> Relation:

    y = (a + b) & MASK
    ra = a & b
    rd = a ^ b
    r0 = (~(a | b)) & MASK
    t = rd ^ y

    return Relation(y, ra, rd, r0, t)


def main():

    print("=" * 72)
    print("Φ-P8 RELATION TRANSPORT ANALYSIS")
    print("=" * 72)

    identical = 0
    changed = 0

    component_change = Counter()

    transport_vectors = Counter()

    relation_transport = Counter()

    rows = []

    for a in range(256):
        for b in range(256):

            r1 = relation(a, b)

            pa = phi_p8(a)
            pb = phi_p8(b)

            r2 = relation(pa, pb)

            if r1 == r2:
                identical += 1
            else:
                changed += 1

            if r1.Y != r2.Y:
                component_change["Y"] += 1

            if r1.RA != r2.RA:
                component_change["RA"] += 1

            if r1.RD != r2.RD:
                component_change["RD"] += 1

            if r1.R0 != r2.R0:
                component_change["R0"] += 1

            if r1.T != r2.T:
                component_change["T"] += 1

            delta = (
                r1.Y ^ r2.Y,
                r1.RA ^ r2.RA,
                r1.RD ^ r2.RD,
                r1.R0 ^ r2.R0,
                r1.T ^ r2.T,
            )

            transport_vectors[delta] += 1

            relation_transport[(r1.key(), r2.key())] += 1

            rows.append({
                "A": bit_string(a),
                "B": bit_string(b),
                "PhiA": bit_string(pa),
                "PhiB": bit_string(pb),
                "Y": bit_string(r1.Y),
                "RA": bit_string(r1.RA),
                "RD": bit_string(r1.RD),
                "R0": bit_string(r1.R0),
                "T": bit_string(r1.T),
                "Y2": bit_string(r2.Y),
                "RA2": bit_string(r2.RA),
                "RD2": bit_string(r2.RD),
                "R02": bit_string(r2.R0),
                "T2": bit_string(r2.T),
            })

    csv_file = RESULTS / "phi_p8_relation_transport.csv"

    with csv_file.open("w", newline="", encoding="utf8") as f:

        writer = csv.DictWriter(
            f,
            fieldnames=list(rows[0].keys())
        )

        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "pairs": 65536,
        "unchanged_relation_frames": identical,
        "changed_relation_frames": changed,
        "component_changes": dict(component_change),
        "unique_transport_vectors": len(transport_vectors),
        "largest_transport_vector_frequency":
            transport_vectors.most_common(1)[0],
        "unique_relation_transitions":
            len(relation_transport),
    }

    with (RESULTS / "phi_p8_relation_transport_summary.json").open(
        "w",
        encoding="utf8"
    ) as f:
        json.dump(summary, f, indent=2)

    print()
    print("Pairs tested                 :", 65536)
    print("Relation unchanged           :", identical)
    print("Relation changed             :", changed)
    print()

    print("Component changes")
    print("-----------------")

    for k in ("Y", "RA", "RD", "R0", "T"):
        print(f"{k:3s}: {component_change[k]}")

    print()
    print("Unique transport vectors     :", len(transport_vectors))
    print("Unique relation transitions  :", len(relation_transport))

    print()
    print("Most common transport vector")
    print("----------------------------")

    delta, freq = transport_vectors.most_common(1)[0]

    print("ΔY :", bit_string(delta[0]))
    print("ΔRA:", bit_string(delta[1]))
    print("ΔRD:", bit_string(delta[2]))
    print("ΔR0:", bit_string(delta[3]))
    print("ΔT :", bit_string(delta[4]))
    print("Frequency:", freq)

    print()
    print("Saved:")
    print(csv_file)
    print(RESULTS / "phi_p8_relation_transport_summary.json")


if __name__ == "__main__":
    main()
