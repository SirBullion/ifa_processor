#!/usr/bin/env python3
"""
IFÁ Processor V5
Phase B4 — Transport Closure Algebra

The 13 physically observed Φ-P2 transport vectors are not closed
under XOR. They generate a rank-5 GF(2) vector space containing
32 vectors.

This script:

    1. Reads the 13 observed transport vectors.
    2. Finds a canonical independent basis.
    3. Generates the complete 32-vector XOR closure.
    4. Assigns each closure vector five-bit basis coordinates.
    5. Marks which vectors are physically observed.
    6. Constructs the complete 32 × 32 XOR Cayley table.
    7. Verifies identity, inverses, associativity and commutativity.
    8. Determines minimal generating subsets among the 13 vectors.

Inputs:
    python/v5/results/phi_p2_theorem_13_vectors.csv

Outputs:
    transport_closure_32_vectors.csv
    transport_closure_cayley_table.csv
    transport_observed_coordinate_table.csv
    transport_minimal_bases.csv
    transport_closure_algebra_summary.json
"""

from __future__ import annotations

import csv
import json
from itertools import combinations
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "python" / "v5" / "results"

INPUT_FILE = RESULTS_DIR / "phi_p2_theorem_13_vectors.csv"

CLOSURE_FILE = RESULTS_DIR / "transport_closure_32_vectors.csv"
CAYLEY_FILE = RESULTS_DIR / "transport_closure_cayley_table.csv"
OBSERVED_FILE = RESULTS_DIR / "transport_observed_coordinate_table.csv"
BASES_FILE = RESULTS_DIR / "transport_minimal_bases.csv"
SUMMARY_FILE = RESULTS_DIR / "transport_closure_algebra_summary.json"


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
    text = str(value).strip()

    if text.startswith("0b"):
        text = text[2:]

    if not text:
        raise ValueError("Empty binary value")

    if any(bit not in "01" for bit in text):
        raise ValueError(f"Invalid binary value: {value!r}")

    if len(text) > width:
        raise ValueError(
            f"Value {value!r} exceeds width {width}"
        )

    return int(text, 2)


def encode_fields(fields: tuple[int, ...]) -> int:
    encoded = 0

    for value, (_, width) in zip(fields, FIELD_WIDTHS):
        encoded = (encoded << width) | value

    return encoded


def decode_fields(encoded: int) -> tuple[int, ...]:
    values = []
    remaining = encoded

    for _, width in reversed(FIELD_WIDTHS):
        mask = (1 << width) - 1
        values.append(remaining & mask)
        remaining >>= width

    return tuple(reversed(values))


def vector_bits(value: int) -> str:
    return format(value, f"0{TOTAL_WIDTH}b")


def coordinate_bits(value: int, width: int = 5) -> str:
    return format(value, f"0{width}b")


def field_dictionary(value: int) -> dict[str, str]:
    fields = decode_fields(value)

    return {
        name: format(field_value, f"0{width}b")
        for field_value, (name, width)
        in zip(fields, FIELD_WIDTHS)
    }


def read_observed_vectors() -> list[int]:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing input file:\n{INPUT_FILE}"
        )

    values = []

    with INPUT_FILE.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as handle:
        reader = csv.DictReader(handle)

        for row in reader:
            fields = tuple(
                parse_binary(row[name], width)
                for name, width in FIELD_WIDTHS
            )

            values.append(encode_fields(fields))

    unique = sorted(set(values))

    if len(unique) != 13:
        raise AssertionError(
            f"Expected 13 vectors, found {len(unique)}"
        )

    return unique


def gf2_rank(values: list[int]) -> int:
    pivots: dict[int, int] = {}

    for value in values:
        x = value

        while x:
            pivot = x.bit_length() - 1

            if pivot in pivots:
                x ^= pivots[pivot]
            else:
                pivots[pivot] = x
                break

    return len(pivots)


def is_independent(values: tuple[int, ...] | list[int]) -> bool:
    return gf2_rank(list(values)) == len(values)


def canonical_basis(values: list[int]) -> list[int]:
    """
    Greedily choose a deterministic independent basis from vectors
    sorted by packed integer value.
    """
    basis: list[int] = []

    for value in sorted(values):
        if gf2_rank(basis + [value]) > len(basis):
            basis.append(value)

    return basis


def generate_coordinate_map(
    basis: list[int],
) -> dict[int, int]:
    """
    Map every span vector to its basis-coordinate mask.

    Coordinate bit i indicates whether basis[i] participates.
    """
    coordinate_map: dict[int, int] = {}

    for mask in range(1 << len(basis)):
        value = 0

        for index, basis_vector in enumerate(basis):
            if (mask >> index) & 1:
                value ^= basis_vector

        if value in coordinate_map:
            raise AssertionError(
                "Basis generated duplicate coordinates"
            )

        coordinate_map[value] = mask

    return coordinate_map


def find_all_minimal_bases(
    observed: list[int],
    target_rank: int,
) -> list[tuple[int, ...]]:
    """
    Find every target-rank independent subset drawn from the observed
    nonzero transport vectors.
    """
    nonzero = [value for value in observed if value != 0]

    bases = []

    for subset in combinations(nonzero, target_rank):
        if is_independent(subset):
            bases.append(subset)

    return bases


def verify_group_axioms(
    closure: list[int],
) -> dict[str, bool]:
    closure_set = set(closure)
    identity = 0

    closed = all(
        (left ^ right) in closure_set
        for left in closure
        for right in closure
    )

    identity_valid = all(
        (identity ^ value) == value
        and (value ^ identity) == value
        for value in closure
    )

    self_inverse = all(
        (value ^ value) == identity
        for value in closure
    )

    commutative = all(
        (left ^ right) == (right ^ left)
        for left in closure
        for right in closure
    )

    associative = all(
        ((a ^ b) ^ c) == (a ^ (b ^ c))
        for a in closure
        for b in closure
        for c in closure
    )

    return {
        "closure": closed,
        "identity": identity_valid,
        "every_element_self_inverse": self_inverse,
        "commutative": commutative,
        "associative": associative,
    }


def main() -> None:
    observed = read_observed_vectors()
    observed_set = set(observed)

    rank = gf2_rank(observed)

    if rank != 5:
        raise AssertionError(
            f"Expected GF(2) rank 5, found {rank}"
        )

    basis = canonical_basis(observed)

    if len(basis) != rank:
        raise AssertionError(
            "Canonical basis size does not match rank"
        )

    coordinate_map = generate_coordinate_map(basis)
    closure = sorted(coordinate_map)
    closure_set = set(closure)

    if len(closure) != 32:
        raise AssertionError(
            f"Expected closure size 32, found {len(closure)}"
        )

    labels = {
        value: f"G{coordinate_map[value]:02d}"
        for value in closure
    }

    observed_labels = {
        value: f"V{index:02d}"
        for index, value in enumerate(observed)
    }

    axioms = verify_group_axioms(closure)

    if not all(axioms.values()):
        raise AssertionError(
            "One or more closure algebra axioms failed"
        )

    minimal_bases = find_all_minimal_bases(
        observed,
        target_rank=rank,
    )

    # ---------------------------------------------------------
    # Save complete 32-vector closure
    # ---------------------------------------------------------

    closure_rows = []

    for value in sorted(
        closure,
        key=lambda item: coordinate_map[item],
    ):
        fields = field_dictionary(value)
        coordinate = coordinate_map[value]

        closure_rows.append(
            {
                "closure_id": labels[value],
                "basis_coordinates":
                    coordinate_bits(coordinate, rank),
                "packed_bits": vector_bits(value),
                "physically_observed":
                    value in observed_set,
                "observed_id":
                    observed_labels.get(value, ""),
                **fields,
            }
        )

    with CLOSURE_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(closure_rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(closure_rows)

    # ---------------------------------------------------------
    # Save observed vectors with closure coordinates
    # ---------------------------------------------------------

    observed_rows = []

    for value in observed:
        observed_rows.append(
            {
                "observed_id": observed_labels[value],
                "closure_id": labels[value],
                "basis_coordinates": coordinate_bits(
                    coordinate_map[value],
                    rank,
                ),
                "packed_bits": vector_bits(value),
                **field_dictionary(value),
            }
        )

    with OBSERVED_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(observed_rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(observed_rows)

    # ---------------------------------------------------------
    # Save 32 × 32 Cayley table
    # ---------------------------------------------------------

    ordered_closure = sorted(
        closure,
        key=lambda item: coordinate_map[item],
    )

    with CAYLEY_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.writer(handle)

        writer.writerow(
            ["XOR"]
            + [labels[value] for value in ordered_closure]
        )

        for left in ordered_closure:
            writer.writerow(
                [labels[left]]
                + [
                    labels[left ^ right]
                    for right in ordered_closure
                ]
            )

    # ---------------------------------------------------------
    # Save every minimal observed generating basis
    # ---------------------------------------------------------

    basis_rows = []

    for basis_index, candidate in enumerate(
        minimal_bases,
        start=1,
    ):
        row = {
            "basis_number": basis_index,
        }

        for position, value in enumerate(candidate, start=1):
            row[f"generator_{position}_observed_id"] = (
                observed_labels[value]
            )
            row[f"generator_{position}_closure_id"] = (
                labels[value]
            )
            row[f"generator_{position}_bits"] = (
                vector_bits(value)
            )

        basis_rows.append(row)

    with BASES_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(basis_rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(basis_rows)

    summary = {
        "phase": "B4",
        "operation": "XOR",
        "observed_transport_vectors": len(observed),
        "gf2_rank": rank,
        "closure_size": len(closure),
        "closure_dimension": rank,
        "abstract_structure": "(Z2)^5",
        "observed_fraction_of_closure":
            len(observed) / len(closure),
        "unobserved_closure_vectors":
            len(closure_set - observed_set),
        "group_axioms": axioms,
        "identity": {
            "closure_id": labels[0],
            "packed_bits": vector_bits(0),
            "physically_observed": 0 in observed_set,
        },
        "canonical_basis": [
            {
                "basis_position": index,
                "observed_id": observed_labels[value],
                "closure_id": labels[value],
                "packed_bits": vector_bits(value),
                "fields": field_dictionary(value),
            }
            for index, value in enumerate(basis)
        ],
        "minimal_basis_size": rank,
        "number_of_minimal_observed_bases":
            len(minimal_bases),
    }

    with SUMMARY_FILE.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(summary, handle, indent=2)

    print("=" * 80)
    print("IFÁ V5: 32-ELEMENT TRANSPORT CLOSURE ALGEBRA")
    print("=" * 80)

    print()
    print("GENERATED ALGEBRA")
    print("-" * 80)
    print(f"Observed vectors               : {len(observed)}")
    print(f"GF(2) rank                    : {rank}")
    print(f"Closure vectors                : {len(closure)}")
    print(
        "Abstract group                 : "
        f"(Z2)^{rank}"
    )
    print(
        "Observed portion of closure    : "
        f"{len(observed)}/{len(closure)} "
        f"({len(observed) / len(closure):.2%})"
    )
    print(
        "Algebraic but unobserved vectors: "
        f"{len(closure_set - observed_set)}"
    )

    print()
    print("CANONICAL BASIS")
    print("-" * 80)

    for index, value in enumerate(basis):
        print(
            f"B{index}  "
            f"{observed_labels[value]}  "
            f"{vector_bits(value)}"
        )

    print()
    print("GROUP PROPERTIES")
    print("-" * 80)

    for name, passed in axioms.items():
        print(
            f"{name:<32}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    print()
    print("MINIMAL GENERATORS")
    print("-" * 80)
    print(f"Minimum generator count        : {rank}")
    print(
        "Independent five-vector bases  : "
        f"{len(minimal_bases)}"
    )

    print()
    print("Saved:")
    print(CLOSURE_FILE)
    print(CAYLEY_FILE)
    print(OBSERVED_FILE)
    print(BASES_FILE)
    print(SUMMARY_FILE)


if __name__ == "__main__":
    main()
