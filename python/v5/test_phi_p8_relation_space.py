#!/usr/bin/env python3
"""
IFÁ V5 full-pipeline experiment:

    Binary operands
        ↓
    Φ-P8 ⊗ Φ-P8
        ↓
    Anchor–Agreement coordinates
        ↓
    Relation frame

Canonical relation frame:

    Y  = (A + B) mod 2^8
    RA = A AND B
    RD = A XOR B
    R0 = NOT(A OR B)
    T  = RD XOR Y

This test compares:

    1. Direct binary relation space
    2. Φ-P8-transformed relation space

It also checks whether the transformed relation frame alone is injective and
whether preserving the original operands restores reversibility.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from python.v5.ifa_phi_p8 import (  # noqa: E402
    bit_string,
    phi_p8,
    phi_p8_inverse,
)


WIDTH = 8
MASK = (1 << WIDTH) - 1

RESULTS_DIR = PROJECT_ROOT / "python" / "v5" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class RelationFrame:
    y: int
    ra: int
    rd: int
    r0: int
    t: int

    def packed(self) -> int:
        """
        Pack five 8-bit fields into one 40-bit integer.

        Layout:

            [Y | RA | RD | R0 | T]
        """
        value = self.y

        for field in (self.ra, self.rd, self.r0, self.t):
            value = (value << WIDTH) | field

        return value

    def binary_tuple(self) -> tuple[str, str, str, str, str]:
        return (
            bit_string(self.y),
            bit_string(self.ra),
            bit_string(self.rd),
            bit_string(self.r0),
            bit_string(self.t),
        )


@dataclass(frozen=True)
class PipelineRecord:
    a: int
    b: int
    phi_a: int
    phi_b: int
    direct_frame: RelationFrame
    phi_frame: RelationFrame


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def relation_frame(a: int, b: int) -> RelationFrame:
    y = (a + b) & MASK
    ra = a & b
    rd = a ^ b
    r0 = (~(a | b)) & MASK
    t = rd ^ y

    return RelationFrame(
        y=y,
        ra=ra,
        rd=rd,
        r0=r0,
        t=t,
    )


def full_pipeline(a: int, b: int) -> PipelineRecord:
    phi_a = phi_p8(a)
    phi_b = phi_p8(b)

    return PipelineRecord(
        a=a,
        b=b,
        phi_a=phi_a,
        phi_b=phi_b,
        direct_frame=relation_frame(a, b),
        phi_frame=relation_frame(phi_a, phi_b),
    )


def frame_key(frame: RelationFrame) -> tuple[int, int, int, int, int]:
    return (
        frame.y,
        frame.ra,
        frame.rd,
        frame.r0,
        frame.t,
    )


def exhaustive_pipeline() -> list[PipelineRecord]:
    records: list[PipelineRecord] = []

    for a in range(256):
        for b in range(256):
            record = full_pipeline(a, b)

            require(
                phi_p8_inverse(record.phi_a) == a,
                f"Φ-P8 inverse failed for A={a}",
            )

            require(
                phi_p8_inverse(record.phi_b) == b,
                f"Φ-P8 inverse failed for B={b}",
            )

            records.append(record)

    return records


def analyse_collisions(
    records: list[PipelineRecord],
    use_phi_frame: bool,
) -> dict[str, object]:
    classes: defaultdict[
        tuple[int, int, int, int, int],
        list[tuple[int, int]],
    ] = defaultdict(list)

    for record in records:
        frame = (
            record.phi_frame
            if use_phi_frame
            else record.direct_frame
        )

        classes[frame_key(frame)].append((record.a, record.b))

    collision_classes = {
        key: values
        for key, values in classes.items()
        if len(values) > 1
    }

    collision_histogram = Counter(
        len(values)
        for values in classes.values()
    )

    largest_collision = max(
        len(values)
        for values in classes.values()
    )

    return {
        "unique_frames": len(classes),
        "collision_class_count": len(collision_classes),
        "largest_collision": largest_collision,
        "collision_histogram": dict(
            sorted(collision_histogram.items())
        ),
        "classes": classes,
        "collision_classes": collision_classes,
    }


def transport_statistics(
    records: list[PipelineRecord],
    use_phi_frame: bool,
) -> dict[str, object]:
    values = Counter()

    for record in records:
        frame = (
            record.phi_frame
            if use_phi_frame
            else record.direct_frame
        )
        values[frame.t] += 1

    ordered = sorted(
        values.items(),
        key=lambda item: (-item[1], item[0]),
    )

    return {
        "unique_transport_values": len(values),
        "most_common": {
            "value": ordered[0][0],
            "binary": bit_string(ordered[0][0]),
            "frequency": ordered[0][1],
        },
        "least_common": {
            "value": ordered[-1][0],
            "binary": bit_string(ordered[-1][0]),
            "frequency": ordered[-1][1],
        },
        "frequency": {
            bit_string(value): frequency
            for value, frequency in sorted(values.items())
        },
    }


def compare_frame_spaces(
    direct_analysis: dict[str, object],
    phi_analysis: dict[str, object],
) -> dict[str, object]:
    direct_keys = set(direct_analysis["classes"])
    phi_keys = set(phi_analysis["classes"])

    return {
        "direct_unique_frames": len(direct_keys),
        "phi_unique_frames": len(phi_keys),
        "common_frames": len(direct_keys & phi_keys),
        "direct_only_frames": len(direct_keys - phi_keys),
        "phi_only_frames": len(phi_keys - direct_keys),
        "frame_sets_equal": direct_keys == phi_keys,
    }


def test_preserved_state_reversibility(
    records: list[PipelineRecord],
) -> None:
    """
    The relation frame can be many-to-one.

    The reversible V5 embedding therefore preserves the transformed operands:

        |A,B,0>
            →
        |A,B,Φ(A),Φ(B),Relation(Φ(A),Φ(B))>

    This test confirms that preserving Φ(A),Φ(B) allows exact reconstruction
    of A and B.
    """
    seen_states: set[
        tuple[
            int,
            int,
            int,
            int,
            int,
            int,
            int,
        ]
    ] = set()

    for record in records:
        state = (
            record.phi_a,
            record.phi_b,
            record.phi_frame.y,
            record.phi_frame.ra,
            record.phi_frame.rd,
            record.phi_frame.r0,
            record.phi_frame.t,
        )

        require(
            state not in seen_states,
            (
                "Preserved-state collision for "
                f"A={record.a}, B={record.b}"
            ),
        )

        seen_states.add(state)

        recovered_a = phi_p8_inverse(record.phi_a)
        recovered_b = phi_p8_inverse(record.phi_b)

        require(
            recovered_a == record.a,
            "Failed to reconstruct A",
        )

        require(
            recovered_b == record.b,
            "Failed to reconstruct B",
        )

    require(
        len(seen_states) == 65_536,
        "Preserved pipeline state is not injective",
    )


def write_pipeline_csv(
    records: list[PipelineRecord],
) -> None:
    path = RESULTS_DIR / "phi_p8_relation_pipeline.csv"

    with path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "A_decimal",
            "A_binary",
            "B_decimal",
            "B_binary",
            "Phi_A_decimal",
            "Phi_A_binary",
            "Phi_B_decimal",
            "Phi_B_binary",
            "Direct_Y",
            "Direct_RA",
            "Direct_RD",
            "Direct_R0",
            "Direct_T",
            "Phi_Y",
            "Phi_RA",
            "Phi_RD",
            "Phi_R0",
            "Phi_T",
        ]

        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )
        writer.writeheader()

        for record in records:
            direct = record.direct_frame.binary_tuple()
            transformed = record.phi_frame.binary_tuple()

            writer.writerow(
                {
                    "A_decimal": record.a,
                    "A_binary": bit_string(record.a),
                    "B_decimal": record.b,
                    "B_binary": bit_string(record.b),
                    "Phi_A_decimal": record.phi_a,
                    "Phi_A_binary": bit_string(record.phi_a),
                    "Phi_B_decimal": record.phi_b,
                    "Phi_B_binary": bit_string(record.phi_b),
                    "Direct_Y": direct[0],
                    "Direct_RA": direct[1],
                    "Direct_RD": direct[2],
                    "Direct_R0": direct[3],
                    "Direct_T": direct[4],
                    "Phi_Y": transformed[0],
                    "Phi_RA": transformed[1],
                    "Phi_RD": transformed[2],
                    "Phi_R0": transformed[3],
                    "Phi_T": transformed[4],
                }
            )


def write_collision_csv(
    filename: str,
    collision_classes: dict[
        tuple[int, int, int, int, int],
        list[tuple[int, int]],
    ],
) -> None:
    path = RESULTS_DIR / filename

    with path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "Y",
            "RA",
            "RD",
            "R0",
            "T",
            "collision_size",
            "input_pairs",
        ]

        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )
        writer.writeheader()

        for key, pairs in sorted(
            collision_classes.items(),
            key=lambda item: (-len(item[1]), item[0]),
        ):
            y, ra, rd, r0, t = key

            formatted_pairs = " ".join(
                f"({bit_string(a)},{bit_string(b)})"
                for a, b in pairs
            )

            writer.writerow(
                {
                    "Y": bit_string(y),
                    "RA": bit_string(ra),
                    "RD": bit_string(rd),
                    "R0": bit_string(r0),
                    "T": bit_string(t),
                    "collision_size": len(pairs),
                    "input_pairs": formatted_pairs,
                }
            )


def compact_qubit_count(unique_states: int) -> int:
    if unique_states <= 1:
        return 0

    return math.ceil(math.log2(unique_states))


def main() -> None:
    print("=" * 72)
    print("IFÁ V5: BINARY → Φ-P8 → RELATION-SPACE TEST")
    print("=" * 72)

    print("\nEnumerating all 65,536 ordered byte pairs...")
    records = exhaustive_pipeline()

    print("Analysing direct binary relation space...")
    direct_analysis = analyse_collisions(
        records,
        use_phi_frame=False,
    )

    print("Analysing Φ-P8 relation space...")
    phi_analysis = analyse_collisions(
        records,
        use_phi_frame=True,
    )

    print("Testing reversible preserved-state embedding...")
    test_preserved_state_reversibility(records)

    direct_transport = transport_statistics(
        records,
        use_phi_frame=False,
    )

    phi_transport = transport_statistics(
        records,
        use_phi_frame=True,
    )

    comparison = compare_frame_spaces(
        direct_analysis,
        phi_analysis,
    )

    tensor_dimension = 2 ** (WIDTH * 5)
    phi_unique = int(phi_analysis["unique_frames"])
    direct_unique = int(direct_analysis["unique_frames"])

    summary = {
        "width": WIDTH,
        "ordered_input_pairs": len(records),
        "pipeline": [
            "Binary operands",
            "Φ-P8 tensor Φ-P8",
            "Anchor–Agreement coordinates",
            "Relation frame",
        ],
        "relation_definition": {
            "Y": "(A + B) mod 256",
            "RA": "A AND B",
            "RD": "A XOR B",
            "R0": "NOT(A OR B)",
            "T": "RD XOR Y",
        },
        "direct_relation_space": {
            "unique_frames": direct_unique,
            "collision_class_count": direct_analysis[
                "collision_class_count"
            ],
            "largest_collision": direct_analysis[
                "largest_collision"
            ],
            "collision_histogram": direct_analysis[
                "collision_histogram"
            ],
            "compact_qubits": compact_qubit_count(direct_unique),
            "transport": direct_transport,
        },
        "phi_p8_relation_space": {
            "unique_frames": phi_unique,
            "collision_class_count": phi_analysis[
                "collision_class_count"
            ],
            "largest_collision": phi_analysis[
                "largest_collision"
            ],
            "collision_histogram": phi_analysis[
                "collision_histogram"
            ],
            "compact_qubits": compact_qubit_count(phi_unique),
            "transport": phi_transport,
        },
        "comparison": comparison,
        "full_tensor_dimension": tensor_dimension,
        "phi_reachable_occupancy": (
            phi_unique / tensor_dimension
        ),
        "preserved_state_injective": True,
        "preserved_state_count": 65_536,
        "reversible_embedding": (
            "|A,B,0> → "
            "|A,B,Φ(A),Φ(B),Relation(Φ(A),Φ(B))>"
        ),
    }

    write_pipeline_csv(records)

    write_collision_csv(
        "direct_relation_collisions.csv",
        direct_analysis["collision_classes"],
    )

    write_collision_csv(
        "phi_p8_relation_collisions.csv",
        phi_analysis["collision_classes"],
    )

    summary_path = (
        RESULTS_DIR / "phi_p8_relation_summary.json"
    )

    with summary_path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(summary, handle, indent=2)

    print("\n" + "=" * 72)
    print("IFÁ V5 Φ-P8 RELATION-SPACE REPORT")
    print("=" * 72)
    print(f"Operand width                    : {WIDTH} bits")
    print(f"Ordered input pairs              : {len(records):,}")
    print("Φ-P8 inverse reconstruction      : PASS")
    print("Preserved pipeline injective     : PASS")
    print()
    print("DIRECT BINARY RELATION SPACE")
    print(
        "Unique relation frames          : "
        f"{direct_unique:,}"
    )
    print(
        "Collision classes               : "
        f"{direct_analysis['collision_class_count']:,}"
    )
    print(
        "Largest collision               : "
        f"{direct_analysis['largest_collision']}"
    )
    print(
        "Compact relation qubits         : "
        f"{compact_qubit_count(direct_unique)}"
    )
    print()
    print("Φ-P8 RELATION SPACE")
    print(
        "Unique relation frames          : "
        f"{phi_unique:,}"
    )
    print(
        "Collision classes               : "
        f"{phi_analysis['collision_class_count']:,}"
    )
    print(
        "Largest collision               : "
        f"{phi_analysis['largest_collision']}"
    )
    print(
        "Compact relation qubits         : "
        f"{compact_qubit_count(phi_unique)}"
    )
    print(
        "Unique transport values         : "
        f"{phi_transport['unique_transport_values']}"
    )
    print()
    print("SPACE COMPARISON")
    print(
        "Common frames                   : "
        f"{comparison['common_frames']:,}"
    )
    print(
        "Direct-only frames              : "
        f"{comparison['direct_only_frames']:,}"
    )
    print(
        "Φ-P8-only frames                : "
        f"{comparison['phi_only_frames']:,}"
    )
    print(
        "Frame sets identical            : "
        f"{comparison['frame_sets_equal']}"
    )
    print(
        "Full five-register dimension    : "
        f"{tensor_dimension:,}"
    )
    print(
        "Φ-P8 relation occupancy         : "
        f"{100 * phi_unique / tensor_dimension:.12f}%"
    )
    print("=" * 72)

    print("\nSaved:")
    print(RESULTS_DIR / "phi_p8_relation_pipeline.csv")
    print(RESULTS_DIR / "direct_relation_collisions.csv")
    print(RESULTS_DIR / "phi_p8_relation_collisions.csv")
    print(summary_path)

    print(
        "\nPASS: Binary → Φ-P8 → Relation Frame "
        "pipeline completed."
    )


if __name__ == "__main__":
    main()
