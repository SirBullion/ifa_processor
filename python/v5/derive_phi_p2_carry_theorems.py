#!/usr/bin/env python3
"""
IFÁ V5

Exact combinatorial derivation of the carry-aware Φ-P2 algebra.

This script derives and verifies:

    1. 64 total local carry-aware contexts
    2. 40 distinct carry-aware relation transitions
    3. 13 distinct XOR transport vectors
    4. 46 reachable block/carry trace contexts in the full byte system
    5. Final carry-pair distribution over all 65,536 byte pairs

The derivation is exhaustive and exact. It does not use random sampling.

Canonical transform
-------------------

For a two-bit word x = x1 x0:

    Φ-P2(x1, x0) = (x1, NOT(x1 XOR x0))

Canonical relation fields
-------------------------

For a two-bit block A, B and carry input C:

    total = A + B + C
    Y     = total mod 4
    Cout  = floor(total / 4)
    RA    = A AND B
    RD    = A XOR B
    R0    = NOT(A OR B)
    T     = RD XOR Y
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


from python.v5.ifa_phi_p8 import phi_p2, phi_p8  # noqa: E402


BLOCK_MASK = 0b11
BYTE_MASK = 0xFF
BLOCK_WIDTH = 2
BYTE_WIDTH = 8

RESULTS_DIR = PROJECT_ROOT / "python" / "v5" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class BlockFrame:
    y: int
    cout: int
    ra: int
    rd: int
    r0: int
    t: int

    def key(self) -> tuple[int, int, int, int, int, int]:
        return (
            self.y,
            self.cout,
            self.ra,
            self.rd,
            self.r0,
            self.t,
        )


def bits(value: int, width: int) -> str:
    return format(value, f"0{width}b")


def phi_word2(value: int) -> int:
    if not 0 <= value <= BLOCK_MASK:
        raise ValueError(f"Expected 2-bit value, received {value}")

    x1 = (value >> 1) & 1
    x0 = value & 1

    y1, y0 = phi_p2(x1, x0)

    return (y1 << 1) | y0


def frame(a: int, b: int, carry_in: int) -> BlockFrame:
    if not 0 <= a <= BLOCK_MASK:
        raise ValueError(f"Invalid A block: {a}")

    if not 0 <= b <= BLOCK_MASK:
        raise ValueError(f"Invalid B block: {b}")

    if carry_in not in (0, 1):
        raise ValueError(f"Invalid carry input: {carry_in}")

    total = a + b + carry_in

    y = total & BLOCK_MASK
    cout = (total >> BLOCK_WIDTH) & 1
    ra = a & b
    rd = a ^ b
    r0 = (~(a | b)) & BLOCK_MASK
    t = rd ^ y

    return BlockFrame(
        y=y,
        cout=cout,
        ra=ra,
        rd=rd,
        r0=r0,
        t=t,
    )


def delta(
    source: BlockFrame,
    destination: BlockFrame,
) -> tuple[int, int, int, int, int, int]:
    return (
        source.y ^ destination.y,
        source.cout ^ destination.cout,
        source.ra ^ destination.ra,
        source.rd ^ destination.rd,
        source.r0 ^ destination.r0,
        source.t ^ destination.t,
    )


def local_derivation() -> dict[str, object]:
    """
    Derive the complete 64-context local algebra.

    A block pair has:

        4 choices for A
        4 choices for B
        2 choices for direct carry-in
        2 choices for transformed carry-in

    Therefore:

        4 × 4 × 2 × 2 = 64
    """
    context_rows: list[dict[str, object]] = []

    transition_counter: Counter[
        tuple[
            tuple[int, int, int, int, int, int],
            tuple[int, int, int, int, int, int],
        ]
    ] = Counter()

    vector_counter: Counter[
        tuple[int, int, int, int, int, int]
    ] = Counter()

    source_counter: Counter[
        tuple[int, tuple[int, int, int, int, int, int]]
    ] = Counter()

    source_targets: defaultdict[
        tuple[int, tuple[int, int, int, int, int, int]],
        set[
            tuple[
                int,
                tuple[int, int, int, int, int, int],
            ]
        ],
    ] = defaultdict(set)

    for a in range(4):
        for b in range(4):
            phi_a = phi_word2(a)
            phi_b = phi_word2(b)

            for carry_in in (0, 1):
                source = frame(a, b, carry_in)
                source_key = (carry_in, source.key())

                for phi_carry_in in (0, 1):
                    destination = frame(
                        phi_a,
                        phi_b,
                        phi_carry_in,
                    )

                    destination_key = (
                        phi_carry_in,
                        destination.key(),
                    )

                    transition = (
                        source.key(),
                        destination.key(),
                    )

                    vector = delta(source, destination)

                    transition_counter[transition] += 1
                    vector_counter[vector] += 1
                    source_counter[source_key] += 1
                    source_targets[source_key].add(destination_key)

                    context_rows.append(
                        {
                            "A": bits(a, 2),
                            "B": bits(b, 2),
                            "Phi_A": bits(phi_a, 2),
                            "Phi_B": bits(phi_b, 2),
                            "C_in": carry_in,
                            "C_in_phi": phi_carry_in,
                            "Y": bits(source.y, 2),
                            "C_out": source.cout,
                            "RA": bits(source.ra, 2),
                            "RD": bits(source.rd, 2),
                            "R0": bits(source.r0, 2),
                            "T": bits(source.t, 2),
                            "Y_phi": bits(destination.y, 2),
                            "C_out_phi": destination.cout,
                            "RA_phi": bits(destination.ra, 2),
                            "RD_phi": bits(destination.rd, 2),
                            "R0_phi": bits(destination.r0, 2),
                            "T_phi": bits(destination.t, 2),
                            "Delta_Y": bits(vector[0], 2),
                            "Delta_Cout": vector[1],
                            "Delta_RA": bits(vector[2], 2),
                            "Delta_RD": bits(vector[3], 2),
                            "Delta_R0": bits(vector[4], 2),
                            "Delta_T": bits(vector[5], 2),
                        }
                    )

    if len(context_rows) != 64:
        raise AssertionError(
            f"Expected 64 contexts, got {len(context_rows)}"
        )

    transition_multiplicity = Counter(
        transition_counter.values()
    )

    vector_multiplicity = Counter(
        vector_counter.values()
    )

    branching_distribution = Counter(
        len(targets)
        for targets in source_targets.values()
    )

    return {
        "rows": context_rows,
        "total_contexts": len(context_rows),
        "distinct_transitions": len(transition_counter),
        "distinct_vectors": len(vector_counter),
        "distinct_sources": len(source_targets),
        "branching_sources": sum(
            1
            for targets in source_targets.values()
            if len(targets) > 1
        ),
        "maximum_targets": max(
            len(targets)
            for targets in source_targets.values()
        ),
        "transition_counter": transition_counter,
        "vector_counter": vector_counter,
        "transition_multiplicity": transition_multiplicity,
        "vector_multiplicity": vector_multiplicity,
        "branching_distribution": branching_distribution,
        "source_targets": source_targets,
    }


def derive_reachable_trace_contexts() -> dict[str, object]:
    """
    Derive all carry contexts that actually occur during four-block byte
    execution.

    A trace context is:

        (
            block_index,
            direct_carry_in,
            phi_carry_in,
            direct_carry_out,
            phi_carry_out
        )

    The first block is constrained to:

        direct_carry_in = 0
        phi_carry_in    = 0

    Later carry inputs are determined by previous block outputs.
    """
    trace_counter: Counter[
        tuple[int, int, int, int, int]
    ] = Counter()

    carry_input_counter: Counter[
        tuple[int, int, int]
    ] = Counter()

    carry_transition_counter: Counter[
        tuple[int, int, int, int]
    ] = Counter()

    final_carry_counter: Counter[
        tuple[int, int]
    ] = Counter()

    for a in range(256):
        for b in range(256):
            direct_carry = 0
            phi_carry = 0

            phi_a = phi_p8(a)
            phi_b = phi_p8(b)

            for block_index, shift in enumerate(
                range(0, BYTE_WIDTH, BLOCK_WIDTH)
            ):
                a_block = (a >> shift) & BLOCK_MASK
                b_block = (b >> shift) & BLOCK_MASK

                phi_a_block = (phi_a >> shift) & BLOCK_MASK
                phi_b_block = (phi_b >> shift) & BLOCK_MASK

                direct_carry_in = direct_carry
                phi_carry_in = phi_carry

                direct_frame = frame(
                    a_block,
                    b_block,
                    direct_carry_in,
                )

                phi_frame = frame(
                    phi_a_block,
                    phi_b_block,
                    phi_carry_in,
                )

                direct_carry = direct_frame.cout
                phi_carry = phi_frame.cout

                trace_key = (
                    block_index,
                    direct_carry_in,
                    phi_carry_in,
                    direct_carry,
                    phi_carry,
                )

                trace_counter[trace_key] += 1

                carry_input_counter[
                    (
                        block_index,
                        direct_carry_in,
                        phi_carry_in,
                    )
                ] += 1

                carry_transition_counter[
                    (
                        direct_carry_in,
                        phi_carry_in,
                        direct_carry,
                        phi_carry,
                    )
                ] += 1

            final_carry_counter[
                (direct_carry, phi_carry)
            ] += 1

    return {
        "trace_counter": trace_counter,
        "carry_input_counter": carry_input_counter,
        "carry_transition_counter": carry_transition_counter,
        "final_carry_counter": final_carry_counter,
        "reachable_trace_contexts": len(trace_counter),
        "reachable_carry_inputs": len(carry_input_counter),
        "reachable_carry_transitions": len(
            carry_transition_counter
        ),
    }


def derive_final_carry_formula() -> dict[str, object]:
    """
    Verify the exact final carry-pair counts independently.

    Direct final carry:

        C = 1 iff A + B >= 256

    Transformed final carry:

        C_phi = 1 iff Φ(A) + Φ(B) >= 256
    """
    counts: Counter[tuple[int, int]] = Counter()

    for a in range(256):
        for b in range(256):
            direct_carry = int(a + b >= 256)

            phi_a = phi_p8(a)
            phi_b = phi_p8(b)

            phi_carry = int(phi_a + phi_b >= 256)

            counts[(direct_carry, phi_carry)] += 1

    matching = counts[(0, 0)] + counts[(1, 1)]
    differing = counts[(0, 1)] + counts[(1, 0)]

    return {
        "counts": counts,
        "matching": matching,
        "differing": differing,
        "matching_fraction": matching / 65536,
        "differing_fraction": differing / 65536,
    }


def save_local_contexts(
    rows: list[dict[str, object]],
) -> Path:
    path = RESULTS_DIR / "phi_p2_theorem_local_contexts.csv"

    with path.open(
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

    return path


def save_transition_table(
    transition_counter: Counter,
) -> Path:
    path = RESULTS_DIR / "phi_p2_theorem_40_transitions.csv"

    rows = []

    for (source, destination), multiplicity in sorted(
        transition_counter.items()
    ):
        rows.append(
            {
                "source_Y": bits(source[0], 2),
                "source_Cout": source[1],
                "source_RA": bits(source[2], 2),
                "source_RD": bits(source[3], 2),
                "source_R0": bits(source[4], 2),
                "source_T": bits(source[5], 2),
                "destination_Y": bits(destination[0], 2),
                "destination_Cout": destination[1],
                "destination_RA": bits(destination[2], 2),
                "destination_RD": bits(destination[3], 2),
                "destination_R0": bits(destination[4], 2),
                "destination_T": bits(destination[5], 2),
                "multiplicity": multiplicity,
            }
        )

    with path.open(
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

    return path


def save_vector_table(
    vector_counter: Counter,
) -> Path:
    path = RESULTS_DIR / "phi_p2_theorem_13_vectors.csv"

    rows = []

    for vector, multiplicity in sorted(vector_counter.items()):
        rows.append(
            {
                "Delta_Y": bits(vector[0], 2),
                "Delta_Cout": vector[1],
                "Delta_RA": bits(vector[2], 2),
                "Delta_RD": bits(vector[3], 2),
                "Delta_R0": bits(vector[4], 2),
                "Delta_T": bits(vector[5], 2),
                "multiplicity": multiplicity,
            }
        )

    with path.open(
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

    return path


def save_trace_table(
    trace_counter: Counter,
) -> Path:
    path = RESULTS_DIR / "phi_p2_theorem_46_trace_contexts.csv"

    rows = []

    for trace, multiplicity in sorted(trace_counter.items()):
        rows.append(
            {
                "block_index": trace[0],
                "direct_Cin": trace[1],
                "phi_Cin": trace[2],
                "direct_Cout": trace[3],
                "phi_Cout": trace[4],
                "multiplicity": multiplicity,
            }
        )

    with path.open(
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

    return path


def main() -> None:
    print("=" * 80)
    print("IFÁ V5: EXACT Φ-P2 CARRY THEOREM DERIVATION")
    print("=" * 80)

    local = local_derivation()
    traces = derive_reachable_trace_contexts()
    final_carry = derive_final_carry_formula()

    expected_final = {
        (0, 0): 24704,
        (0, 1): 8192,
        (1, 0): 8192,
        (1, 1): 24448,
    }

    assertions = {
        "64 local contexts":
            local["total_contexts"] == 64,

        "40 distinct relation transitions":
            local["distinct_transitions"] == 40,

        "13 distinct XOR vectors":
            local["distinct_vectors"] == 13,

        "18 carry-aware source states":
            local["distinct_sources"] == 18,

        "18 branching source states":
            local["branching_sources"] == 18,

        "maximum branch degree 4":
            local["maximum_targets"] == 4,

        "46 reachable trace contexts":
            traces["reachable_trace_contexts"] == 46,

        "final carry distribution":
            dict(final_carry["counts"]) == expected_final,

        "matching carry count 49152":
            final_carry["matching"] == 49152,

        "different carry count 16384":
            final_carry["differing"] == 16384,
    }

    failed = [
        name
        for name, passed in assertions.items()
        if not passed
    ]

    if failed:
        raise AssertionError(
            "Theorem verification failed: "
            + ", ".join(failed)
        )

    local_path = save_local_contexts(local["rows"])

    transition_path = save_transition_table(
        local["transition_counter"]
    )

    vector_path = save_vector_table(
        local["vector_counter"]
    )

    trace_path = save_trace_table(
        traces["trace_counter"]
    )

    summary = {
        "theorems": assertions,
        "local_algebra": {
            "operand_block_pairs": 16,
            "carry_pairs_per_operand_pair": 4,
            "total_contexts": local["total_contexts"],
            "distinct_relation_transitions":
                local["distinct_transitions"],
            "distinct_xor_vectors":
                local["distinct_vectors"],
            "carry_aware_source_states":
                local["distinct_sources"],
            "branching_source_states":
                local["branching_sources"],
            "maximum_target_count":
                local["maximum_targets"],
            "transition_multiplicity_distribution": {
                str(key): value
                for key, value in sorted(
                    local[
                        "transition_multiplicity"
                    ].items()
                )
            },
            "vector_multiplicity_distribution": {
                str(key): value
                for key, value in sorted(
                    local[
                        "vector_multiplicity"
                    ].items()
                )
            },
            "branching_degree_distribution": {
                str(key): value
                for key, value in sorted(
                    local[
                        "branching_distribution"
                    ].items()
                )
            },
        },
        "global_carry_algebra": {
            "reachable_trace_contexts":
                traces["reachable_trace_contexts"],
            "reachable_carry_input_contexts":
                traces["reachable_carry_inputs"],
            "reachable_carry_transitions":
                traces["reachable_carry_transitions"],
            "final_carry_pair_counts": {
                str(key): value
                for key, value in sorted(
                    final_carry["counts"].items()
                )
            },
            "matching_final_carries":
                final_carry["matching"],
            "different_final_carries":
                final_carry["differing"],
            "matching_fraction":
                final_carry["matching_fraction"],
            "different_fraction":
                final_carry["differing_fraction"],
        },
    }

    summary_path = (
        RESULTS_DIR / "phi_p2_carry_theorems_summary.json"
    )

    with summary_path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(summary, handle, indent=2)

    print()
    print("LOCAL ALGEBRA")
    print("-" * 80)
    print(
        "Total contexts                    :",
        local["total_contexts"],
    )
    print(
        "Distinct relation transitions     :",
        local["distinct_transitions"],
    )
    print(
        "Distinct XOR transport vectors    :",
        local["distinct_vectors"],
    )
    print(
        "Carry-aware source states         :",
        local["distinct_sources"],
    )
    print(
        "Branching source states           :",
        local["branching_sources"],
    )
    print(
        "Maximum targets from one source   :",
        local["maximum_targets"],
    )

    print()
    print("TRANSITION MULTIPLICITY DISTRIBUTION")
    print("-" * 80)

    for multiplicity, number_of_transitions in sorted(
        local["transition_multiplicity"].items()
    ):
        print(
            f"Multiplicity {multiplicity:>2} : "
            f"{number_of_transitions} transition(s)"
        )

    print()
    print("VECTOR MULTIPLICITY DISTRIBUTION")
    print("-" * 80)

    for multiplicity, number_of_vectors in sorted(
        local["vector_multiplicity"].items()
    ):
        print(
            f"Multiplicity {multiplicity:>2} : "
            f"{number_of_vectors} vector(s)"
        )

    print()
    print("BRANCHING DEGREE DISTRIBUTION")
    print("-" * 80)

    for degree, number_of_sources in sorted(
        local["branching_distribution"].items()
    ):
        print(
            f"{degree} target(s) : "
            f"{number_of_sources} source state(s)"
        )

    print()
    print("GLOBAL CARRY ALGEBRA")
    print("-" * 80)
    print(
        "Reachable trace contexts          :",
        traces["reachable_trace_contexts"],
    )
    print(
        "Reachable carry-input contexts    :",
        traces["reachable_carry_inputs"],
    )
    print(
        "Reachable carry transitions       :",
        traces["reachable_carry_transitions"],
    )

    print()
    print("FINAL CARRY-PAIR DISTRIBUTION")
    print("-" * 80)

    for pair, count in sorted(final_carry["counts"].items()):
        print(f"{pair} : {count}")

    print()
    print(
        "Matching final carries            :",
        final_carry["matching"],
        f"({final_carry['matching_fraction']:.2%})",
    )

    print(
        "Different final carries           :",
        final_carry["differing"],
        f"({final_carry['differing_fraction']:.2%})",
    )

    print()
    print("THEOREM CHECKS")
    print("-" * 80)

    for theorem, passed in assertions.items():
        print(
            f"{theorem:<45} "
            f"{'PASS' if passed else 'FAIL'}"
        )

    print()
    print("Saved:")
    print(local_path)
    print(transition_path)
    print(vector_path)
    print(trace_path)
    print(summary_path)


if __name__ == "__main__":
    main()
