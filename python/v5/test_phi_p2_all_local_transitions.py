#!/usr/bin/env python3
"""
IFÁ V5: all 16 ordered local operand-state transitions.

Local ordered operand states:

    00, 01, 10, 11

All possible ordered transitions:

    4 source states × 4 destination states = 16 transitions

The experiment records:

    source operand state
    source relation state
    destination operand state
    destination relation state
    XOR transition vector
    whether Φ-P2 actually induces the transition

Important distinction
---------------------

There are 16 mathematically possible ordered transitions between local operand
states, but canonical Φ-P2 generates only four of them:

    00 -> 01
    01 -> 00
    10 -> 10
    11 -> 11
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


from python.v5.ifa_phi_p8 import phi_p2  # noqa: E402


RESULTS_DIR = PROJECT_ROOT / "python" / "v5" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class LocalRelation:
    y: int
    ra: int
    rd: int
    r0: int
    t: int

    def key(self) -> tuple[int, int, int, int, int]:
        return (
            self.y,
            self.ra,
            self.rd,
            self.r0,
            self.t,
        )

    def label(self) -> str:
        if self.ra == 1:
            return "BOTH_ONE"

        if self.r0 == 1:
            return "BOTH_ZERO"

        if self.rd == 1:
            return "DISAGREE"

        return "INVALID"


def local_relation(a: int, b: int) -> LocalRelation:
    """
    One-bit relation definition.

        Y  = (A + B) mod 2
        RA = A AND B
        RD = A XOR B
        R0 = NOT(A OR B)
        T  = RD XOR Y

    For a one-bit addition, Y = RD and therefore T = 0.
    """
    y = (a + b) & 1
    ra = a & b
    rd = a ^ b
    r0 = (~(a | b)) & 1
    t = rd ^ y

    return LocalRelation(
        y=y,
        ra=ra,
        rd=rd,
        r0=r0,
        t=t,
    )


def operand_string(a: int, b: int) -> str:
    return f"{a}{b}"


def transition_vector(
    source: LocalRelation,
    destination: LocalRelation,
) -> tuple[int, int, int, int, int]:
    return (
        source.y ^ destination.y,
        source.ra ^ destination.ra,
        source.rd ^ destination.rd,
        source.r0 ^ destination.r0,
        source.t ^ destination.t,
    )


def phi_destination(a: int, b: int) -> tuple[int, int]:
    return phi_p2(a, b)


def main() -> None:
    print("=" * 78)
    print("IFÁ V5: ALL 16 LOCAL OPERAND-STATE TRANSITIONS")
    print("=" * 78)

    operand_states = [
        (0, 0),
        (0, 1),
        (1, 0),
        (1, 1),
    ]

    rows: list[dict[str, object]] = []

    relation_transition_counts: Counter[
        tuple[
            tuple[int, int, int, int, int],
            tuple[int, int, int, int, int],
        ]
    ] = Counter()

    vector_counts: Counter[
        tuple[int, int, int, int, int]
    ] = Counter()

    phi_rows: list[dict[str, object]] = []

    source_relation_targets: defaultdict[
        tuple[int, int, int, int, int],
        set[tuple[int, int, int, int, int]],
    ] = defaultdict(set)

    phi_induced_count = 0

    for source_a, source_b in operand_states:
        source_relation = local_relation(source_a, source_b)

        expected_phi_a, expected_phi_b = phi_destination(
            source_a,
            source_b,
        )

        for destination_a, destination_b in operand_states:
            destination_relation = local_relation(
                destination_a,
                destination_b,
            )

            delta = transition_vector(
                source_relation,
                destination_relation,
            )

            is_phi_induced = (
                destination_a == expected_phi_a
                and destination_b == expected_phi_b
            )

            if is_phi_induced:
                phi_induced_count += 1

            relation_transition = (
                source_relation.key(),
                destination_relation.key(),
            )

            relation_transition_counts[relation_transition] += 1
            vector_counts[delta] += 1

            source_relation_targets[
                source_relation.key()
            ].add(destination_relation.key())

            row = {
                "source_A": source_a,
                "source_B": source_b,
                "source_operand": operand_string(
                    source_a,
                    source_b,
                ),
                "source_relation_label": source_relation.label(),
                "source_Y": source_relation.y,
                "source_RA": source_relation.ra,
                "source_RD": source_relation.rd,
                "source_R0": source_relation.r0,
                "source_T": source_relation.t,
                "destination_A": destination_a,
                "destination_B": destination_b,
                "destination_operand": operand_string(
                    destination_a,
                    destination_b,
                ),
                "destination_relation_label":
                    destination_relation.label(),
                "destination_Y": destination_relation.y,
                "destination_RA": destination_relation.ra,
                "destination_RD": destination_relation.rd,
                "destination_R0": destination_relation.r0,
                "destination_T": destination_relation.t,
                "delta_Y": delta[0],
                "delta_RA": delta[1],
                "delta_RD": delta[2],
                "delta_R0": delta[3],
                "delta_T": delta[4],
                "phi_p2_induced": is_phi_induced,
            }

            rows.append(row)

            if is_phi_induced:
                phi_rows.append(row)

    require_transition_count = len(rows)

    if require_transition_count != 16:
        raise AssertionError(
            f"Expected 16 transitions, got {require_transition_count}"
        )

    if phi_induced_count != 4:
        raise AssertionError(
            f"Expected 4 Φ-P2 transitions, got {phi_induced_count}"
        )

    all_transitions_path = (
        RESULTS_DIR / "phi_p2_all_16_local_transitions.csv"
    )

    with all_transitions_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)

    phi_transitions_path = (
        RESULTS_DIR / "phi_p2_induced_local_transitions.csv"
    )

    with phi_transitions_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(phi_rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(phi_rows)

    relation_transitions_serialized = []

    for (source, destination), multiplicity in sorted(
        relation_transition_counts.items()
    ):
        relation_transitions_serialized.append(
            {
                "source_relation": source,
                "destination_relation": destination,
                "operand_transition_multiplicity": multiplicity,
            }
        )

    vector_rows = []

    for vector, multiplicity in sorted(vector_counts.items()):
        vector_rows.append(
            {
                "delta_Y": vector[0],
                "delta_RA": vector[1],
                "delta_RD": vector[2],
                "delta_R0": vector[3],
                "delta_T": vector[4],
                "multiplicity": multiplicity,
            }
        )

    vector_path = RESULTS_DIR / "phi_p2_all_transition_vectors.csv"

    with vector_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(vector_rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(vector_rows)

    summary = {
        "local_operand_states": 4,
        "all_ordered_operand_transitions": len(rows),
        "phi_p2_induced_operand_transitions": phi_induced_count,
        "local_relation_states": 3,
        "distinct_relation_level_transitions": len(
            relation_transition_counts
        ),
        "distinct_xor_transition_vectors": len(vector_counts),
        "relation_transition_multiplicities":
            relation_transitions_serialized,
        "source_relation_target_counts": [
            {
                "source_relation": source,
                "target_count": len(targets),
                "targets": sorted(targets),
            }
            for source, targets in sorted(
                source_relation_targets.items()
            )
        ],
        "phi_p2_mapping": [
            {
                "source": row["source_operand"],
                "destination": row["destination_operand"],
                "source_relation":
                    row["source_relation_label"],
                "destination_relation":
                    row["destination_relation_label"],
            }
            for row in phi_rows
        ],
    }

    summary_path = (
        RESULTS_DIR / "phi_p2_all_local_transitions_summary.json"
    )

    with summary_path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(summary, handle, indent=2)

    print("\nALL ORDERED OPERAND TRANSITIONS")
    print("-" * 78)
    print("Source Destination | Source relation -> Destination relation | Φ-P2")

    for row in rows:
        marker = "YES" if row["phi_p2_induced"] else "no"

        print(
            f"  {row['source_operand']}       "
            f"{row['destination_operand']}      | "
            f"{row['source_relation_label']:<9} -> "
            f"{row['destination_relation_label']:<9} | "
            f"{marker}"
        )

    print("\nΦ-P2-INDUCED TRANSITIONS")
    print("-" * 78)

    for row in phi_rows:
        print(
            f"{row['source_operand']} -> "
            f"{row['destination_operand']}    "
            f"{row['source_relation_label']} -> "
            f"{row['destination_relation_label']}"
        )

    print("\nSUMMARY")
    print("-" * 78)
    print("Local operand states                 :", 4)
    print("All ordered operand transitions      :", len(rows))
    print("Φ-P2-induced operand transitions     :", phi_induced_count)
    print("Local relation states                :", 3)
    print(
        "Distinct relation-level transitions :",
        len(relation_transition_counts),
    )
    print(
        "Distinct XOR transition vectors     :",
        len(vector_counts),
    )

    print("\nSaved:")
    print(all_transitions_path)
    print(phi_transitions_path)
    print(vector_path)
    print(summary_path)


if __name__ == "__main__":
    main()
