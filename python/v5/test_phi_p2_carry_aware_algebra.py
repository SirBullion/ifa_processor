#!/usr/bin/env python3
"""
IFÁ V5: carry-aware Φ-P2 block algebra.

This experiment studies the complete two-bit block:

    A_block, B_block ∈ {00, 01, 10, 11}
    C_in              ∈ {0, 1}
    C_in_phi          ∈ {0, 1}

There are:

    4 × 4 × 2 × 2 = 64

carry-aware local contexts.

It then reconstructs every 8-bit relation frame from four two-bit blocks and
checks the reconstruction against the direct whole-byte computation for all
65,536 ordered byte pairs.

Canonical definitions
---------------------

For each byte pair A, B:

    Y  = (A + B) mod 256
    RA = A AND B
    RD = A XOR B
    R0 = NOT(A OR B)
    T  = RD XOR Y

Φ-P2:

    (x1, x0) -> (x1, NOT(x1 XOR x0))

Φ-P8 applies Φ-P2 independently to four adjacent bit pairs.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from python.v5.ifa_phi_p8 import phi_p2, phi_p8  # noqa: E402


WIDTH = 8
BYTE_MASK = 0xFF
BLOCK_WIDTH = 2
BLOCK_MASK = 0b11

RESULTS_DIR = PROJECT_ROOT / "python" / "v5" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class BlockRelation:
    """Relation frame for one two-bit block."""

    y: int
    carry_out: int
    ra: int
    rd: int
    r0: int
    t: int

    def key(self) -> tuple[int, int, int, int, int, int]:
        return (
            self.y,
            self.carry_out,
            self.ra,
            self.rd,
            self.r0,
            self.t,
        )


@dataclass(frozen=True)
class ByteRelation:
    """Canonical full-byte relation frame."""

    y: int
    ra: int
    rd: int
    r0: int
    t: int

    def key(self) -> tuple[int, int, int, int, int]:
        return self.y, self.ra, self.rd, self.r0, self.t


def bits(value: int, width: int) -> str:
    """Return a zero-padded binary string."""
    return format(value, f"0{width}b")


def phi_word2(value: int) -> int:
    """
    Apply canonical Φ-P2 to one two-bit word.

    Input layout:

        value = x1 x0

    Transform:

        x1' = x1
        x0' = NOT(x1 XOR x0)
    """
    if not 0 <= value <= BLOCK_MASK:
        raise ValueError(f"Expected a two-bit value, received {value}")

    x1 = (value >> 1) & 1
    x0 = value & 1

    transformed = phi_p2(x1, x0)

    if not isinstance(transformed, tuple) or len(transformed) != 2:
        raise TypeError(
            "phi_p2 must return a two-element tuple: (anchor, agreement)"
        )

    y1, y0 = transformed

    if y1 not in (0, 1) or y0 not in (0, 1):
        raise ValueError(
            f"phi_p2 returned non-binary values: {(y1, y0)}"
        )

    return (y1 << 1) | y0


def block_relation(
    a: int,
    b: int,
    carry_in: int,
) -> BlockRelation:
    """
    Compute one carry-aware two-bit relation frame.

    The sum is:

        total = A_block + B_block + C_in
        Y     = total mod 4
        C_out = floor(total / 4)
    """
    if not 0 <= a <= BLOCK_MASK:
        raise ValueError(f"Invalid A block: {a}")

    if not 0 <= b <= BLOCK_MASK:
        raise ValueError(f"Invalid B block: {b}")

    if carry_in not in (0, 1):
        raise ValueError(f"Invalid carry input: {carry_in}")

    total = a + b + carry_in

    y = total & BLOCK_MASK
    carry_out = (total >> BLOCK_WIDTH) & 1

    ra = a & b
    rd = a ^ b
    r0 = (~(a | b)) & BLOCK_MASK
    t = rd ^ y

    return BlockRelation(
        y=y,
        carry_out=carry_out,
        ra=ra,
        rd=rd,
        r0=r0,
        t=t,
    )


def byte_relation(a: int, b: int) -> ByteRelation:
    """Compute the canonical full-byte relation frame."""
    y = (a + b) & BYTE_MASK
    ra = a & b
    rd = a ^ b
    r0 = (~(a | b)) & BYTE_MASK
    t = rd ^ y

    return ByteRelation(
        y=y,
        ra=ra,
        rd=rd,
        r0=r0,
        t=t,
    )


def xor_delta(
    source: BlockRelation,
    destination: BlockRelation,
) -> tuple[int, int, int, int, int, int]:
    """XOR transition vector between two block relation frames."""
    return (
        source.y ^ destination.y,
        source.carry_out ^ destination.carry_out,
        source.ra ^ destination.ra,
        source.rd ^ destination.rd,
        source.r0 ^ destination.r0,
        source.t ^ destination.t,
    )


def reconstruct_from_blocks(
    a: int,
    b: int,
) -> tuple[
    ByteRelation,
    ByteRelation,
    list[dict[str, int]],
    int,
    int,
]:
    """
    Reconstruct direct and Φ-P8 relation frames from four two-bit blocks.

    Blocks are processed from least significant to most significant so that
    carry propagates correctly:

        bits 1:0
        bits 3:2
        bits 5:4
        bits 7:6
    """
    direct_y = 0
    direct_ra = 0
    direct_rd = 0
    direct_r0 = 0

    phi_y = 0
    phi_ra = 0
    phi_rd = 0
    phi_r0 = 0

    direct_carry = 0
    phi_carry = 0

    trace: list[dict[str, int]] = []

    for block_index, shift in enumerate(range(0, WIDTH, BLOCK_WIDTH)):
        a_block = (a >> shift) & BLOCK_MASK
        b_block = (b >> shift) & BLOCK_MASK

        phi_a_block = phi_word2(a_block)
        phi_b_block = phi_word2(b_block)

        direct_carry_in = direct_carry
        phi_carry_in = phi_carry

        direct_frame = block_relation(
            a_block,
            b_block,
            direct_carry_in,
        )

        phi_frame = block_relation(
            phi_a_block,
            phi_b_block,
            phi_carry_in,
        )

        direct_y |= direct_frame.y << shift
        direct_ra |= direct_frame.ra << shift
        direct_rd |= direct_frame.rd << shift
        direct_r0 |= direct_frame.r0 << shift

        phi_y |= phi_frame.y << shift
        phi_ra |= phi_frame.ra << shift
        phi_rd |= phi_frame.rd << shift
        phi_r0 |= phi_frame.r0 << shift

        direct_carry = direct_frame.carry_out
        phi_carry = phi_frame.carry_out

        trace.append(
            {
                "block_index": block_index,
                "shift": shift,
                "a_block": a_block,
                "b_block": b_block,
                "phi_a_block": phi_a_block,
                "phi_b_block": phi_b_block,
                "direct_carry_in": direct_carry_in,
                "direct_y": direct_frame.y,
                "direct_carry_out": direct_frame.carry_out,
                "phi_carry_in": phi_carry_in,
                "phi_y": phi_frame.y,
                "phi_carry_out": phi_frame.carry_out,
            }
        )

    direct_t = direct_rd ^ direct_y
    phi_t = phi_rd ^ phi_y

    direct_relation = ByteRelation(
        y=direct_y,
        ra=direct_ra,
        rd=direct_rd,
        r0=direct_r0,
        t=direct_t,
    )

    phi_relation = ByteRelation(
        y=phi_y,
        ra=phi_ra,
        rd=phi_rd,
        r0=phi_r0,
        t=phi_t,
    )

    return (
        direct_relation,
        phi_relation,
        trace,
        direct_carry,
        phi_carry,
    )


def enumerate_local_contexts() -> tuple[
    list[dict[str, object]],
    Counter,
    Counter,
    defaultdict,
]:
    """Enumerate all 64 carry-aware local contexts."""
    rows: list[dict[str, object]] = []

    transition_counts: Counter[
        tuple[
            tuple[int, int, int, int, int, int],
            tuple[int, int, int, int, int, int],
        ]
    ] = Counter()

    delta_counts: Counter[
        tuple[int, int, int, int, int, int]
    ] = Counter()

    source_to_targets: defaultdict[
        tuple[int, tuple[int, int, int, int, int, int]],
        set[tuple[int, tuple[int, int, int, int, int, int]]],
    ] = defaultdict(set)

    for a in range(4):
        for b in range(4):
            phi_a = phi_word2(a)
            phi_b = phi_word2(b)

            for carry_in in (0, 1):
                for phi_carry_in in (0, 1):
                    source = block_relation(a, b, carry_in)

                    destination = block_relation(
                        phi_a,
                        phi_b,
                        phi_carry_in,
                    )

                    delta = xor_delta(source, destination)

                    transition_counts[
                        (source.key(), destination.key())
                    ] += 1

                    delta_counts[delta] += 1

                    source_key = (carry_in, source.key())
                    destination_key = (
                        phi_carry_in,
                        destination.key(),
                    )

                    source_to_targets[source_key].add(destination_key)

                    rows.append(
                        {
                            "A_block": bits(a, 2),
                            "B_block": bits(b, 2),
                            "Phi_A_block": bits(phi_a, 2),
                            "Phi_B_block": bits(phi_b, 2),
                            "C_in": carry_in,
                            "C_in_phi": phi_carry_in,
                            "Y": bits(source.y, 2),
                            "C_out": source.carry_out,
                            "RA": bits(source.ra, 2),
                            "RD": bits(source.rd, 2),
                            "R0": bits(source.r0, 2),
                            "T": bits(source.t, 2),
                            "Y_phi": bits(destination.y, 2),
                            "C_out_phi": destination.carry_out,
                            "RA_phi": bits(destination.ra, 2),
                            "RD_phi": bits(destination.rd, 2),
                            "R0_phi": bits(destination.r0, 2),
                            "T_phi": bits(destination.t, 2),
                            "Delta_Y": bits(delta[0], 2),
                            "Delta_C_out": delta[1],
                            "Delta_RA": bits(delta[2], 2),
                            "Delta_RD": bits(delta[3], 2),
                            "Delta_R0": bits(delta[4], 2),
                            "Delta_T": bits(delta[5], 2),
                        }
                    )

    return rows, transition_counts, delta_counts, source_to_targets


def verify_phi_word2() -> None:
    """Ensure the local helper matches the corresponding Φ-P8 block."""
    for value in range(256):
        expected = 0

        for shift in range(0, WIDTH, BLOCK_WIDTH):
            block = (value >> shift) & BLOCK_MASK
            expected |= phi_word2(block) << shift

        actual = phi_p8(value)

        if actual != expected:
            raise AssertionError(
                "Local Φ-P2 composition does not match Φ-P8: "
                f"x={bits(value, 8)}, "
                f"local={bits(expected, 8)}, "
                f"phi_p8={bits(actual, 8)}"
            )


def verify_global_reconstruction() -> dict[str, object]:
    """Verify four-block reconstruction over every ordered byte pair."""
    tested = 0
    direct_failures = 0
    phi_failures = 0
    carry_pair_counts: Counter[tuple[int, int]] = Counter()
    trace_context_counts: Counter[
        tuple[int, int, int, int]
    ] = Counter()

    first_failure: dict[str, object] | None = None

    for a in range(256):
        for b in range(256):
            tested += 1

            phi_a = phi_p8(a)
            phi_b = phi_p8(b)

            expected_direct = byte_relation(a, b)
            expected_phi = byte_relation(phi_a, phi_b)

            (
                reconstructed_direct,
                reconstructed_phi,
                trace,
                final_direct_carry,
                final_phi_carry,
            ) = reconstruct_from_blocks(a, b)

            carry_pair_counts[
                (final_direct_carry, final_phi_carry)
            ] += 1

            for step in trace:
                trace_context_counts[
                    (
                        step["block_index"],
                        step["direct_carry_in"],
                        step["phi_carry_in"],
                        step["direct_carry_out"] << 1
                        | step["phi_carry_out"],
                    )
                ] += 1

            direct_ok = reconstructed_direct == expected_direct
            phi_ok = reconstructed_phi == expected_phi

            if not direct_ok:
                direct_failures += 1

            if not phi_ok:
                phi_failures += 1

            if (not direct_ok or not phi_ok) and first_failure is None:
                first_failure = {
                    "A": bits(a, 8),
                    "B": bits(b, 8),
                    "Phi_A": bits(phi_a, 8),
                    "Phi_B": bits(phi_b, 8),
                    "expected_direct": asdict(expected_direct),
                    "reconstructed_direct": asdict(
                        reconstructed_direct
                    ),
                    "expected_phi": asdict(expected_phi),
                    "reconstructed_phi": asdict(
                        reconstructed_phi
                    ),
                    "trace": trace,
                }

    if direct_failures or phi_failures:
        raise AssertionError(
            "Four-block reconstruction failed. "
            f"Direct failures={direct_failures}, "
            f"Φ failures={phi_failures}, "
            f"first failure={first_failure}"
        )

    return {
        "ordered_byte_pairs_tested": tested,
        "direct_reconstruction_failures": direct_failures,
        "phi_reconstruction_failures": phi_failures,
        "direct_reconstruction_pass": direct_failures == 0,
        "phi_reconstruction_pass": phi_failures == 0,
        "final_carry_pair_counts": {
            str(key): value
            for key, value in sorted(carry_pair_counts.items())
        },
        "reachable_trace_contexts": len(trace_context_counts),
    }


def main() -> None:
    print("=" * 80)
    print("IFÁ V5: CARRY-AWARE Φ-P2 BLOCK ALGEBRA")
    print("=" * 80)

    verify_phi_word2()

    (
        local_rows,
        transition_counts,
        delta_counts,
        source_to_targets,
    ) = enumerate_local_contexts()

    if len(local_rows) != 64:
        raise AssertionError(
            f"Expected 64 local contexts, received {len(local_rows)}"
        )

    local_csv = (
        RESULTS_DIR / "phi_p2_carry_aware_local_contexts.csv"
    )

    with local_csv.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(local_rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(local_rows)

    branching_rows: list[dict[str, object]] = []

    for source, targets in sorted(source_to_targets.items()):
        carry_in, source_frame = source

        branching_rows.append(
            {
                "source_C_in": carry_in,
                "source_frame": source_frame,
                "target_count": len(targets),
                "targets": [
                    {
                        "C_in_phi": target[0],
                        "frame": target[1],
                    }
                    for target in sorted(targets)
                ],
            }
        )

    global_results = verify_global_reconstruction()

    summary = {
        "local_operand_pair_states": 16,
        "carry_contexts_per_operand_pair": 4,
        "total_local_contexts": len(local_rows),
        "distinct_carry_aware_relation_transitions": len(
            transition_counts
        ),
        "distinct_carry_aware_xor_vectors": len(delta_counts),
        "carry_aware_source_states": len(source_to_targets),
        "branching_source_states": sum(
            1
            for targets in source_to_targets.values()
            if len(targets) > 1
        ),
        "maximum_targets_from_one_source": max(
            len(targets)
            for targets in source_to_targets.values()
        ),
        "branching": branching_rows,
        "global_reconstruction": global_results,
    }

    summary_json = (
        RESULTS_DIR / "phi_p2_carry_aware_summary.json"
    )

    with summary_json.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(summary, handle, indent=2)

    print()
    print("LOCAL CARRY-AWARE ALGEBRA")
    print("-" * 80)
    print("Two-bit operand-pair states          :", 16)
    print("Carry contexts per operand pair      :", 4)
    print("Total local contexts                 :", len(local_rows))
    print(
        "Distinct relation transitions       :",
        len(transition_counts),
    )
    print(
        "Distinct XOR transition vectors     :",
        len(delta_counts),
    )
    print(
        "Carry-aware source states           :",
        len(source_to_targets),
    )
    print(
        "Branching source states             :",
        summary["branching_source_states"],
    )
    print(
        "Maximum targets from one source     :",
        summary["maximum_targets_from_one_source"],
    )

    print()
    print("FOUR-BLOCK BYTE RECONSTRUCTION")
    print("-" * 80)
    print(
        "Ordered byte pairs tested           :",
        global_results["ordered_byte_pairs_tested"],
    )
    print(
        "Direct reconstruction               :",
        "PASS"
        if global_results["direct_reconstruction_pass"]
        else "FAIL",
    )
    print(
        "Φ-P8 reconstruction                :",
        "PASS"
        if global_results["phi_reconstruction_pass"]
        else "FAIL",
    )
    print(
        "Reachable block/carry trace contexts:",
        global_results["reachable_trace_contexts"],
    )

    print()
    print("Final carry-pair frequencies")
    print("-" * 80)

    for pair, frequency in (
        global_results["final_carry_pair_counts"].items()
    ):
        print(f"{pair:>8} : {frequency}")

    print()
    print("Saved:")
    print(local_csv)
    print(summary_json)


if __name__ == "__main__":
    main()
