#!/usr/bin/env python3
"""
IFÁ Processor V5
Phase B3 — Transport-vector closure

Tests whether the 13 carry-aware Φ-P2 transport vectors are closed under XOR.

Input:
    python/v5/results/phi_p2_theorem_13_vectors.csv

Outputs:
    python/v5/results/transport_vector_xor_table.csv
    python/v5/results/transport_vector_closure_failures.csv
    python/v5/results/transport_vector_closure_summary.json

Transport-vector field order:
    ΔY[1:0], ΔCout, ΔRA[1:0], ΔRD[1:0],
    ΔR0[1:0], ΔT[1:0]

Total encoded width:
    2 + 1 + 2 + 2 + 2 + 2 = 11 bits
"""

from __future__ import annotations

import csv
import json
from itertools import product
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "python" / "v5" / "results"

INPUT_FILE = RESULTS_DIR / "phi_p2_theorem_13_vectors.csv"
XOR_TABLE_FILE = RESULTS_DIR / "transport_vector_xor_table.csv"
FAILURE_FILE = RESULTS_DIR / "transport_vector_closure_failures.csv"
SUMMARY_FILE = RESULTS_DIR / "transport_vector_closure_summary.json"


FIELD_WIDTHS = (
    ("Delta_Y", 2),
    ("Delta_Cout", 1),
    ("Delta_RA", 2),
    ("Delta_RD", 2),
    ("Delta_R0", 2),
    ("Delta_T", 2),
)

TOTAL_WIDTH = sum(width for _, width in FIELD_WIDTHS)


def parse_binary(value: str, width: int) -> int:
    """Parse a binary field and verify its declared width."""
    text = str(value).strip()

    if text.startswith("0b"):
        text = text[2:]

    if not text:
        raise ValueError("Empty binary field")

    if any(bit not in "01" for bit in text):
        raise ValueError(f"Not a binary value: {value!r}")

    if len(text) > width:
        raise ValueError(
            f"Value {value!r} exceeds declared width {width}"
        )

    return int(text, 2)


def encode_fields(fields: tuple[int, ...]) -> int:
    """Pack all transport-vector fields into one 11-bit integer."""
    encoded = 0

    for value, (_, width) in zip(fields, FIELD_WIDTHS):
        if not 0 <= value < (1 << width):
            raise ValueError(
                f"Field value {value} does not fit width {width}"
            )

        encoded = (encoded << width) | value

    return encoded


def decode_fields(encoded: int) -> tuple[int, ...]:
    """Decode one packed 11-bit vector into its six fields."""
    values_reversed = []
    remaining = encoded

    for _, width in reversed(FIELD_WIDTHS):
        mask = (1 << width) - 1
        values_reversed.append(remaining & mask)
        remaining >>= width

    return tuple(reversed(values_reversed))


def field_string(fields: tuple[int, ...]) -> str:
    """Return a readable field-level representation."""
    pieces = []

    for value, (name, width) in zip(fields, FIELD_WIDTHS):
        pieces.append(f"{name}={value:0{width}b}")

    return " | ".join(pieces)


def vector_bits(encoded: int) -> str:
    return format(encoded, f"0{TOTAL_WIDTH}b")


def read_vectors() -> list[int]:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing input file:\n{INPUT_FILE}\n\n"
            "Run derive_phi_p2_carry_theorems.py first."
        )

    vectors: list[int] = []

    with INPUT_FILE.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as handle:
        reader = csv.DictReader(handle)

        missing = [
            name
            for name, _ in FIELD_WIDTHS
            if name not in (reader.fieldnames or [])
        ]

        if missing:
            raise ValueError(
                "Input CSV is missing fields: "
                + ", ".join(missing)
            )

        for row in reader:
            fields = tuple(
                parse_binary(row[name], width)
                for name, width in FIELD_WIDTHS
            )

            vectors.append(encode_fields(fields))

    unique_vectors = sorted(set(vectors))

    if len(unique_vectors) != 13:
        raise AssertionError(
            "Expected exactly 13 unique vectors, "
            f"found {len(unique_vectors)}"
        )

    return unique_vectors


def gf2_rank(values: list[int]) -> int:
    """Calculate binary vector-space rank using Gaussian elimination."""
    basis = [0] * TOTAL_WIDTH

    for value in values:
        x = value

        while x:
            pivot = x.bit_length() - 1

            if basis[pivot]:
                x ^= basis[pivot]
            else:
                basis[pivot] = x
                break

    return sum(value != 0 for value in basis)


def xor_closure(seed: set[int]) -> set[int]:
    """
    Compute the smallest XOR-closed set containing the seed vectors.

    Since XOR is associative and self-inverse, this is the GF(2)
    linear span of the seed set.
    """
    closure = {0}

    for vector in seed:
        additions = {
            existing ^ vector
            for existing in closure
        }
        closure |= additions

    return closure


def main() -> None:
    vectors = read_vectors()
    vector_set = set(vectors)

    labels = {
        vector: f"V{index:02d}"
        for index, vector in enumerate(vectors)
    }

    xor_rows: list[dict[str, object]] = []
    failure_rows: list[dict[str, object]] = []

    ordered_pairs = 0
    closed_pairs = 0

    produced_counter: dict[int, int] = {}

    for left, right in product(vectors, repeat=2):
        ordered_pairs += 1
        result = left ^ right
        is_member = result in vector_set

        if is_member:
            closed_pairs += 1

        produced_counter[result] = produced_counter.get(result, 0) + 1

        row = {
            "left_id": labels[left],
            "left_bits": vector_bits(left),
            "right_id": labels[right],
            "right_bits": vector_bits(right),
            "xor_bits": vector_bits(result),
            "xor_member": is_member,
            "xor_member_id": labels.get(result, ""),
        }

        xor_rows.append(row)

        if not is_member:
            failure_rows.append(
                {
                    **row,
                    "left_fields": field_string(
                        decode_fields(left)
                    ),
                    "right_fields": field_string(
                        decode_fields(right)
                    ),
                    "xor_fields": field_string(
                        decode_fields(result)
                    ),
                }
            )

    distinct_pairwise_results = set(produced_counter)
    missing_pairwise_results = (
        distinct_pairwise_results - vector_set
    )

    full_closure = xor_closure(vector_set)
    rank = gf2_rank(vectors)

    zero_vector = 0
    has_identity = zero_vector in vector_set

    is_closed = closed_pairs == ordered_pairs

    expected_span_size = 1 << rank

    if len(full_closure) != expected_span_size:
        raise AssertionError(
            "GF(2) closure size does not match calculated rank"
        )

    with XOR_TABLE_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(xor_rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(xor_rows)

    failure_fields = [
        "left_id",
        "left_bits",
        "right_id",
        "right_bits",
        "xor_bits",
        "xor_member",
        "xor_member_id",
        "left_fields",
        "right_fields",
        "xor_fields",
    ]

    with FAILURE_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=failure_fields,
        )
        writer.writeheader()
        writer.writerows(failure_rows)

    summary = {
        "phase": "B3",
        "operation": "XOR",
        "transport_vector_count": len(vectors),
        "encoded_width_bits": TOTAL_WIDTH,
        "ordered_pairs_tested": ordered_pairs,
        "closed_pairs": closed_pairs,
        "failed_pairs": len(failure_rows),
        "closure_fraction": closed_pairs / ordered_pairs,
        "is_closed_under_xor": is_closed,
        "contains_zero_identity": has_identity,
        "distinct_pairwise_xor_results":
            len(distinct_pairwise_results),
        "new_pairwise_results":
            len(missing_pairwise_results),
        "gf2_rank": rank,
        "generated_xor_closure_size": len(full_closure),
        "expected_closure_size_from_rank":
            expected_span_size,
        "vectors": [
            {
                "id": labels[vector],
                "bits": vector_bits(vector),
                "fields": field_string(
                    decode_fields(vector)
                ),
            }
            for vector in vectors
        ],
        "new_pairwise_vectors": [
            {
                "bits": vector_bits(vector),
                "fields": field_string(
                    decode_fields(vector)
                ),
            }
            for vector in sorted(
                missing_pairwise_results
            )
        ],
    }

    with SUMMARY_FILE.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(summary, handle, indent=2)

    print("=" * 80)
    print("IFÁ V5: TRANSPORT-VECTOR XOR CLOSURE")
    print("=" * 80)

    print()
    print("VECTOR SET")
    print("-" * 80)
    print(f"Transport vectors              : {len(vectors)}")
    print(f"Encoded width                  : {TOTAL_WIDTH} bits")
    print(f"Contains zero vector           : {has_identity}")

    print()
    print("PAIRWISE XOR TEST")
    print("-" * 80)
    print(f"Ordered pairs tested           : {ordered_pairs}")
    print(f"Results inside original set    : {closed_pairs}")
    print(f"Results outside original set   : {len(failure_rows)}")
    print(
        "Closure fraction               : "
        f"{closed_pairs / ordered_pairs:.6%}"
    )
    print(f"Closed under XOR               : {is_closed}")

    print()
    print("GENERATED STRUCTURE")
    print("-" * 80)
    print(
        "Distinct pairwise XOR results  : "
        f"{len(distinct_pairwise_results)}"
    )
    print(
        "New pairwise vectors           : "
        f"{len(missing_pairwise_results)}"
    )
    print(f"GF(2) rank                     : {rank}")
    print(
        "Complete XOR closure size      : "
        f"{len(full_closure)}"
    )

    print()
    if is_closed:
        print(
            "RESULT: The 13 vectors are closed under XOR."
        )
    else:
        print(
            "RESULT: The 13 vectors are NOT closed under XOR."
        )
        print(
            "Their smallest XOR-closed completion contains "
            f"{len(full_closure)} vectors."
        )

    print()
    print("Saved:")
    print(XOR_TABLE_FILE)
    print(FAILURE_FILE)
    print(SUMMARY_FILE)


if __name__ == "__main__":
    main()
