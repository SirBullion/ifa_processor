#!/usr/bin/env python3
"""
IFÁ V5

Exact local Φ-P2 algebra.

Enumerates every one of the 16 ordered operand configurations:

    (A1,B1,A2,B2)

and derives

    Binary
        ↓
    Relation
        ↓
    Φ-P2
        ↓
    Relation

to determine the exact local transition algebra.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.v5.ifa_phi_p8 import phi_p2   # noqa: E402


RESULTS = PROJECT_ROOT / "python/v5/results"
RESULTS.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class LocalRelation:
    Y: int
    RA: int
    RD: int
    R0: int
    T: int

    def key(self):
        return (self.Y, self.RA, self.RD, self.R0, self.T)


def relation(a: int, b: int) -> LocalRelation:

    y = (a + b) & 1
    ra = a & b
    rd = a ^ b
    r0 = (~(a | b)) & 1
    t = rd ^ y

    return LocalRelation(y, ra, rd, r0, t)


def main():

    print("=" * 70)
    print("LOCAL Φ-P2 ALGEBRA")
    print("=" * 70)

    rows = []

    relation_to_relation = defaultdict(set)

    transition_vectors = Counter()

    source_relations = set()
    target_relations = set()

    for a in (0,1):
        for b in (0,1):

            src = relation(a,b)

            pa,pb = phi_p2(a,b)

            dst = relation(pa,pb)

            relation_to_relation[src.key()].add(dst.key())

            source_relations.add(src.key())
            target_relations.add(dst.key())

            delta = (
                src.Y ^ dst.Y,
                src.RA ^ dst.RA,
                src.RD ^ dst.RD,
                src.R0 ^ dst.R0,
                src.T ^ dst.T
            )

            transition_vectors[delta]+=1

            rows.append({
                "A":a,
                "B":b,
                "Anchor":pa,
                "Agreement":pb,
                "Y":src.Y,
                "RA":src.RA,
                "RD":src.RD,
                "R0":src.R0,
                "T":src.T,
                "Y2":dst.Y,
                "RA2":dst.RA,
                "RD2":dst.RD,
                "R02":dst.R0,
                "T2":dst.T
            })

    csv_file = RESULTS/"phi_p2_local_algebra.csv"

    with csv_file.open("w",newline="",encoding="utf8") as f:

        writer=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    branching=[]

    for src,dsts in relation_to_relation.items():

        branching.append({
            "source":src,
            "targets":len(dsts)
        })

    summary={

        "local_operand_states":4,

        "local_relation_states":len(source_relations),

        "local_target_states":len(target_relations),

        "distinct_relation_transitions":
            sum(len(v) for v in relation_to_relation.values()),

        "branching":

            branching,

        "transition_vectors":

            len(transition_vectors),

        "vectors":

            {
                str(k):v
                for k,v in transition_vectors.items()
            }

    }

    with (RESULTS/"phi_p2_local_algebra_summary.json").open(
        "w",
        encoding="utf8"
    ) as f:

        json.dump(summary,f,indent=2)

    print()

    print("Operand states              :",4)
    print("Relation states             :",len(source_relations))
    print("Target relation states      :",len(target_relations))

    print()

    print("Branching")

    print("----------------")

    for b in branching:

        print(
            b["source"],
            " -> ",
            b["targets"],
            "target(s)"
        )

    print()

    print("Distinct relation transitions :",
          summary["distinct_relation_transitions"])

    print("Transition vectors            :",
          len(transition_vectors))

    print()

    print("Saved:")
    print(csv_file)
    print(RESULTS/"phi_p2_local_algebra_summary.json")


if __name__=="__main__":
    main()
