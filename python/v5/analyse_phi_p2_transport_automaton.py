#!/usr/bin/env python3
"""
IFÁ V5

Extract the explicit structure behind the carry-aware Φ-P2 theorems.

This script identifies:

1. All 13 local XOR transport vectors
2. Their exact multiplicities
3. The 18 carry-aware relation source states
4. The two source states with four targets
5. The sixteen source states with two targets
6. The explicit dual-carry ripple automaton
7. The 14 reachable carry-transition edges
8. Carry-transition frequencies by two-bit block position
9. Graphviz DOT output for visualisation

Canonical Φ-P2
--------------

    (A1, A0) -> (A1, NOT(A1 XOR A0))

Local relation frame
--------------------

    Y    = (A + B + Cin) mod 4
    Cout = floor((A + B + Cin) / 4)
    RA   = A AND B
    RD   = A XOR B
    R0   = NOT(A OR B)
    T    = RD XOR Y
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from python.v5.ifa_phi_p8 import phi_p2, phi_p8  # noqa: E402


BLOCK_MASK = 0b11
BYTE_MASK = 0xFF
BLOCK_WIDTH = 2
BYTE_WIDTH = 8
BLOCK_COUNT = BYTE_WIDTH // BLOCK_WIDTH

RESULTS_DIR = PROJECT_ROOT / "python" / "v5" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True, order=True)
class RelationFrame:
    y: int
    cout: int
    ra: int
    rd: int
    r0: int
    t: int

    def tuple(self) -> tuple[int, int, int, int, int, int]:
        return (
            self.y,
            self.cout,
            self.ra,
            self.rd,
            self.r0,
            self.t,
        )


@dataclass(frozen=True, order=True)
class CarryState:
    direct: int
    transformed: int

    def tuple(self) -> tuple[int, int]:
        return self.direct, self.transformed

    def label(self) -> str:
        return f"{self.direct}{self.transformed}"


@dataclass(frozen=True, order=True)
class CarryEdge:
    source: CarryState
    target: CarryState


def bit_string(value: int, width: int) -> str:
    return format(value, f"0{width}b")


def phi_word2(value: int) -> int:
    if not 0 <= value <= BLOCK_MASK:
        raise ValueError(f"Expected a two-bit value, received {value}")

    high = (value >> 1) & 1
    low = value & 1

    out_high, out_low = phi_p2(high, low)

    return (out_high << 1) | out_low


def relation_frame(
    a: int,
    b: int,
    carry_in: int,
) -> RelationFrame:
    if not 0 <= a <= BLOCK_MASK:
        raise ValueError(f"Invalid local operand A: {a}")

    if not 0 <= b <= BLOCK_MASK:
        raise ValueError(f"Invalid local operand B: {b}")

    if carry_in not in (0, 1):
        raise ValueError(f"Invalid carry input: {carry_in}")

    total = a + b + carry_in

    y = total & BLOCK_MASK
    cout = (total >> BLOCK_WIDTH) & 1
    ra = a & b
    rd = a ^ b
    r0 = (~(a | b)) & BLOCK_MASK
    t = rd ^ y

    return RelationFrame(
        y=y,
        cout=cout,
        ra=ra,
        rd=rd,
        r0=r0,
        t=t,
    )


def transport_vector(
    source: RelationFrame,
    target: RelationFrame,
) -> tuple[int, int, int, int, int, int]:
    return (
        source.y ^ target.y,
        source.cout ^ target.cout,
        source.ra ^ target.ra,
        source.rd ^ target.rd,
        source.r0 ^ target.r0,
        source.t ^ target.t,
    )


def frame_label(frame: RelationFrame) -> str:
    return (
        f"Y={bit_string(frame.y, 2)} "
        f"C={frame.cout} "
        f"RA={bit_string(frame.ra, 2)} "
        f"RD={bit_string(frame.rd, 2)} "
        f"R0={bit_string(frame.r0, 2)} "
        f"T={bit_string(frame.t, 2)}"
    )


def vector_label(
    vector: tuple[int, int, int, int, int, int],
) -> str:
    return (
        f"ΔY={bit_string(vector[0], 2)} "
        f"ΔC={vector[1]} "
        f"ΔRA={bit_string(vector[2], 2)} "
        f"ΔRD={bit_string(vector[3], 2)} "
        f"ΔR0={bit_string(vector[4], 2)} "
        f"ΔT={bit_string(vector[5], 2)}"
    )


def derive_local_algebra() -> dict[str, object]:
    vector_counter: Counter[
        tuple[int, int, int, int, int, int]
    ] = Counter()

    vector_contexts: defaultdict[
        tuple[int, int, int, int, int, int],
        list[dict[str, object]],
    ] = defaultdict(list)

    source_targets: defaultdict[
        tuple[int, RelationFrame],
        set[tuple[int, RelationFrame]],
    ] = defaultdict(set)

    source_target_contexts: defaultdict[
        tuple[
            tuple[int, RelationFrame],
            tuple[int, RelationFrame],
        ],
        list[dict[str, int]],
    ] = defaultdict(list)

    transition_counter: Counter[
        tuple[RelationFrame, RelationFrame]
    ] = Counter()

    for a in range(4):
        for b in range(4):
            phi_a = phi_word2(a)
            phi_b = phi_word2(b)

            for direct_cin in (0, 1):
                source = relation_frame(a, b, direct_cin)
                source_key = (direct_cin, source)

                for phi_cin in (0, 1):
                    target = relation_frame(
                        phi_a,
                        phi_b,
                        phi_cin,
                    )

                    target_key = (phi_cin, target)
                    vector = transport_vector(source, target)

                    context = {
                        "A": a,
                        "B": b,
                        "Phi_A": phi_a,
                        "Phi_B": phi_b,
                        "direct_Cin": direct_cin,
                        "phi_Cin": phi_cin,
                    }

                    vector_counter[vector] += 1
                    vector_contexts[vector].append(context)

                    source_targets[source_key].add(target_key)

                    source_target_contexts[
                        (source_key, target_key)
                    ].append(context)

                    transition_counter[(source, target)] += 1

    branch_distribution = Counter(
        len(targets)
        for targets in source_targets.values()
    )

    four_target_sources = {
        source: targets
        for source, targets in source_targets.items()
        if len(targets) == 4
    }

    two_target_sources = {
        source: targets
        for source, targets in source_targets.items()
        if len(targets) == 2
    }

    return {
        "vector_counter": vector_counter,
        "vector_contexts": vector_contexts,
        "source_targets": source_targets,
        "source_target_contexts": source_target_contexts,
        "transition_counter": transition_counter,
        "branch_distribution": branch_distribution,
        "four_target_sources": four_target_sources,
        "two_target_sources": two_target_sources,
    }


def derive_carry_automaton() -> dict[str, object]:
    """
    Derive carry-state transitions over all ordered byte pairs.

    The automaton state is:

        (direct carry, Φ-transformed carry)

    Each byte is processed as four two-bit blocks, least significant first.
    """
    edge_counter: Counter[CarryEdge] = Counter()
    edge_by_block: defaultdict[
        int,
        Counter[CarryEdge],
    ] = defaultdict(Counter)

    edge_operand_labels: defaultdict[
        CarryEdge,
        set[tuple[int, int, int, int]],
    ] = defaultdict(set)

    trace_counter: Counter[
        tuple[
            CarryState,
            CarryState,
            CarryState,
            CarryState,
            CarryState,
        ]
    ] = Counter()

    block_context_counter: Counter[
        tuple[int, CarryEdge]
    ] = Counter()

    final_state_counter: Counter[CarryState] = Counter()

    for a in range(256):
        phi_a = phi_p8(a)

        for b in range(256):
            phi_b = phi_p8(b)

            state = CarryState(0, 0)
            trace = [state]

            for block_index in range(BLOCK_COUNT):
                shift = block_index * BLOCK_WIDTH

                a_block = (a >> shift) & BLOCK_MASK
                b_block = (b >> shift) & BLOCK_MASK

                phi_a_block = (phi_a >> shift) & BLOCK_MASK
                phi_b_block = (phi_b >> shift) & BLOCK_MASK

                direct = relation_frame(
                    a_block,
                    b_block,
                    state.direct,
                )

                transformed = relation_frame(
                    phi_a_block,
                    phi_b_block,
                    state.transformed,
                )

                target = CarryState(
                    direct=direct.cout,
                    transformed=transformed.cout,
                )

                edge = CarryEdge(
                    source=state,
                    target=target,
                )

                edge_counter[edge] += 1
                edge_by_block[block_index][edge] += 1
                block_context_counter[(block_index, edge)] += 1

                edge_operand_labels[edge].add(
                    (
                        a_block,
                        b_block,
                        phi_a_block,
                        phi_b_block,
                    )
                )

                state = target
                trace.append(state)

            trace_counter[tuple(trace)] += 1
            final_state_counter[state] += 1

    reachable_states = {
        edge.source
        for edge in edge_counter
    } | {
        edge.target
        for edge in edge_counter
    }

    adjacency: defaultdict[
        CarryState,
        set[CarryState],
    ] = defaultdict(set)

    for edge in edge_counter:
        adjacency[edge.source].add(edge.target)

    return {
        "edge_counter": edge_counter,
        "edge_by_block": edge_by_block,
        "edge_operand_labels": edge_operand_labels,
        "trace_counter": trace_counter,
        "block_context_counter": block_context_counter,
        "final_state_counter": final_state_counter,
        "reachable_states": reachable_states,
        "adjacency": adjacency,
    }


def save_transport_vectors(
    local: dict[str, object],
) -> Path:
    path = RESULTS_DIR / "phi_p2_explicit_13_transport_vectors.csv"

    vector_counter = local["vector_counter"]
    vector_contexts = local["vector_contexts"]

    rows: list[dict[str, object]] = []

    sorted_vectors = sorted(
        vector_counter.items(),
        key=lambda item: (-item[1], item[0]),
    )

    for vector_id, (vector, multiplicity) in enumerate(
        sorted_vectors,
        start=1,
    ):
        contexts = vector_contexts[vector]

        rows.append(
            {
                "vector_id": vector_id,
                "Delta_Y": bit_string(vector[0], 2),
                "Delta_Cout": vector[1],
                "Delta_RA": bit_string(vector[2], 2),
                "Delta_RD": bit_string(vector[3], 2),
                "Delta_R0": bit_string(vector[4], 2),
                "Delta_T": bit_string(vector[5], 2),
                "multiplicity": multiplicity,
                "example_A": bit_string(contexts[0]["A"], 2),
                "example_B": bit_string(contexts[0]["B"], 2),
                "example_Phi_A": bit_string(
                    contexts[0]["Phi_A"],
                    2,
                ),
                "example_Phi_B": bit_string(
                    contexts[0]["Phi_B"],
                    2,
                ),
                "example_direct_Cin":
                    contexts[0]["direct_Cin"],
                "example_phi_Cin":
                    contexts[0]["phi_Cin"],
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


def save_branching_sources(
    local: dict[str, object],
) -> Path:
    path = RESULTS_DIR / "phi_p2_explicit_branching_sources.csv"

    source_targets = local["source_targets"]

    rows: list[dict[str, object]] = []

    for source_id, (source_key, targets) in enumerate(
        sorted(source_targets.items()),
        start=1,
    ):
        direct_cin, source_frame = source_key

        for target_index, target_key in enumerate(
            sorted(targets),
            start=1,
        ):
            phi_cin, target_frame = target_key

            rows.append(
                {
                    "source_id": source_id,
                    "branch_degree": len(targets),
                    "target_index": target_index,
                    "direct_Cin": direct_cin,
                    "source_Y": bit_string(source_frame.y, 2),
                    "source_Cout": source_frame.cout,
                    "source_RA": bit_string(source_frame.ra, 2),
                    "source_RD": bit_string(source_frame.rd, 2),
                    "source_R0": bit_string(source_frame.r0, 2),
                    "source_T": bit_string(source_frame.t, 2),
                    "phi_Cin": phi_cin,
                    "target_Y": bit_string(target_frame.y, 2),
                    "target_Cout": target_frame.cout,
                    "target_RA": bit_string(target_frame.ra, 2),
                    "target_RD": bit_string(target_frame.rd, 2),
                    "target_R0": bit_string(target_frame.r0, 2),
                    "target_T": bit_string(target_frame.t, 2),
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


def save_carry_edges(
    automaton: dict[str, object],
) -> Path:
    path = RESULTS_DIR / "phi_p2_explicit_14_carry_edges.csv"

    edge_counter = automaton["edge_counter"]
    edge_by_block = automaton["edge_by_block"]
    edge_operand_labels = automaton["edge_operand_labels"]

    rows: list[dict[str, object]] = []

    for edge_id, edge in enumerate(
        sorted(edge_counter),
        start=1,
    ):
        operands = edge_operand_labels[edge]

        rows.append(
            {
                "edge_id": edge_id,
                "source_direct": edge.source.direct,
                "source_phi": edge.source.transformed,
                "target_direct": edge.target.direct,
                "target_phi": edge.target.transformed,
                "total_frequency": edge_counter[edge],
                "block_0_frequency":
                    edge_by_block[0][edge],
                "block_1_frequency":
                    edge_by_block[1][edge],
                "block_2_frequency":
                    edge_by_block[2][edge],
                "block_3_frequency":
                    edge_by_block[3][edge],
                "distinct_local_operand_labels":
                    len(operands),
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


def save_carry_traces(
    automaton: dict[str, object],
) -> Path:
    path = RESULTS_DIR / "phi_p2_explicit_carry_traces.csv"

    trace_counter = automaton["trace_counter"]

    rows: list[dict[str, object]] = []

    for trace_id, (trace, frequency) in enumerate(
        sorted(
            trace_counter.items(),
            key=lambda item: (-item[1], item[0]),
        ),
        start=1,
    ):
        rows.append(
            {
                "trace_id": trace_id,
                "C0": trace[0].label(),
                "C1": trace[1].label(),
                "C2": trace[2].label(),
                "C3": trace[3].label(),
                "C4": trace[4].label(),
                "frequency": frequency,
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


def save_dot(
    automaton: dict[str, object],
) -> Path:
    path = RESULTS_DIR / "phi_p2_dual_carry_automaton.dot"

    edge_counter = automaton["edge_counter"]
    reachable_states = automaton["reachable_states"]

    lines = [
        "digraph PhiP2CarryAutomaton {",
        '    graph [rankdir=LR, label="IFÁ V5 Dual-Carry Ripple Automaton", labelloc=t];',
        '    node [shape=circle, fontname="DejaVu Sans"];',
        '    edge [fontname="DejaVu Sans"];',
        "",
    ]

    for state in sorted(reachable_states):
        attributes = []

        if state == CarryState(0, 0):
            attributes.append("shape=doublecircle")

        label = (
            f"C={state.direct}, "
            f"CΦ={state.transformed}"
        )

        attributes.append(f'label="{label}"')

        lines.append(
            f'    "{state.label()}" '
            f'[{", ".join(attributes)}];'
        )

    lines.append("")

    for edge in sorted(edge_counter):
        lines.append(
            f'    "{edge.source.label()}" -> '
            f'"{edge.target.label()}" '
            f'[label="{edge_counter[edge]}"];'
        )

    lines.append("}")

    path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    return path


def save_summary(
    local: dict[str, object],
    automaton: dict[str, object],
) -> Path:
    path = RESULTS_DIR / "phi_p2_transport_automaton_summary.json"

    vector_counter = local["vector_counter"]
    four_target_sources = local["four_target_sources"]
    two_target_sources = local["two_target_sources"]

    edge_counter = automaton["edge_counter"]
    adjacency = automaton["adjacency"]
    final_state_counter = automaton["final_state_counter"]

    summary = {
        "local_transport_algebra": {
            "distinct_transport_vectors":
                len(vector_counter),
            "transport_vector_multiplicities":
                sorted(vector_counter.values()),
            "carry_aware_source_states":
                len(local["source_targets"]),
            "two_target_source_states":
                len(two_target_sources),
            "four_target_source_states":
                len(four_target_sources),
            "maximum_branch_degree":
                max(
                    len(targets)
                    for targets
                    in local["source_targets"].values()
                ),
            "transport_vectors": [
                {
                    "vector": {
                        "Delta_Y": vector[0],
                        "Delta_Cout": vector[1],
                        "Delta_RA": vector[2],
                        "Delta_RD": vector[3],
                        "Delta_R0": vector[4],
                        "Delta_T": vector[5],
                    },
                    "multiplicity": multiplicity,
                }
                for vector, multiplicity in sorted(
                    vector_counter.items(),
                    key=lambda item: (-item[1], item[0]),
                )
            ],
        },
        "dual_carry_ripple_automaton": {
            "reachable_carry_states":
                len(automaton["reachable_states"]),
            "reachable_edges":
                len(edge_counter),
            "distinct_full_traces":
                len(automaton["trace_counter"]),
            "adjacency": {
                source.label(): [
                    target.label()
                    for target in sorted(targets)
                ]
                for source, targets in sorted(
                    adjacency.items()
                )
            },
            "final_state_counts": {
                state.label(): count
                for state, count in sorted(
                    final_state_counter.items()
                )
            },
        },
    }

    path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    return path


def print_four_target_sources(
    local: dict[str, object],
) -> None:
    four_target_sources = local["four_target_sources"]

    print()
    print("FOUR-TARGET SOURCE STATES")
    print("-" * 80)

    for index, (source_key, targets) in enumerate(
        sorted(four_target_sources.items()),
        start=1,
    ):
        direct_cin, source_frame = source_key

        print(
            f"Source {index}: "
            f"Cin={direct_cin} | "
            f"{frame_label(source_frame)}"
        )

        for target_index, target_key in enumerate(
            sorted(targets),
            start=1,
        ):
            phi_cin, target_frame = target_key

            print(
                f"    Target {target_index}: "
                f"CinΦ={phi_cin} | "
                f"{frame_label(target_frame)}"
            )


def print_transport_vectors(
    local: dict[str, object],
) -> None:
    vector_counter = local["vector_counter"]

    print()
    print("EXPLICIT 13 TRANSPORT VECTORS")
    print("-" * 80)

    sorted_vectors = sorted(
        vector_counter.items(),
        key=lambda item: (-item[1], item[0]),
    )

    for index, (vector, multiplicity) in enumerate(
        sorted_vectors,
        start=1,
    ):
        print(
            f"V{index:02d} | "
            f"multiplicity={multiplicity:2d} | "
            f"{vector_label(vector)}"
        )


def print_carry_automaton(
    automaton: dict[str, object],
) -> None:
    edge_counter = automaton["edge_counter"]
    edge_by_block = automaton["edge_by_block"]

    print()
    print("DUAL-CARRY RIPPLE AUTOMATON")
    print("-" * 80)

    print(
        "Reachable carry states            :",
        len(automaton["reachable_states"]),
    )

    print(
        "Reachable carry edges             :",
        len(edge_counter),
    )

    print(
        "Distinct complete carry traces    :",
        len(automaton["trace_counter"]),
    )

    print()
    print("EXPLICIT CARRY EDGES")
    print("-" * 80)

    for edge_id, edge in enumerate(
        sorted(edge_counter),
        start=1,
    ):
        block_counts = [
            edge_by_block[index][edge]
            for index in range(BLOCK_COUNT)
        ]

        print(
            f"E{edge_id:02d}: "
            f"{edge.source.label()} -> "
            f"{edge.target.label()} | "
            f"total={edge_counter[edge]:6d} | "
            f"blocks={block_counts}"
        )


def verify(
    local: dict[str, object],
    automaton: dict[str, object],
) -> dict[str, bool]:
    vector_counter = local["vector_counter"]
    branch_distribution = local["branch_distribution"]
    edge_counter = automaton["edge_counter"]
    final_state_counter = automaton["final_state_counter"]

    vector_multiplicity = Counter(
        vector_counter.values()
    )

    checks = {
        "13 explicit transport vectors":
            len(vector_counter) == 13,

        "11 vectors have multiplicity 4":
            vector_multiplicity[4] == 11,

        "1 vector has multiplicity 8":
            vector_multiplicity[8] == 1,

        "1 vector has multiplicity 12":
            vector_multiplicity[12] == 1,

        "18 carry-aware source states":
            len(local["source_targets"]) == 18,

        "16 two-target source states":
            branch_distribution[2] == 16,

        "2 four-target source states":
            branch_distribution[4] == 2,

        "14 reachable carry edges":
            len(edge_counter) == 14,

        "four reachable carry states":
            len(automaton["reachable_states"]) == 4,

        "65,536 final states counted":
            sum(final_state_counter.values()) == 65536,

        "final 00 count":
            final_state_counter[CarryState(0, 0)] == 24704,

        "final 01 count":
            final_state_counter[CarryState(0, 1)] == 8192,

        "final 10 count":
            final_state_counter[CarryState(1, 0)] == 8192,

        "final 11 count":
            final_state_counter[CarryState(1, 1)] == 24448,
    }

    failed = [
        name
        for name, passed in checks.items()
        if not passed
    ]

    if failed:
        raise AssertionError(
            "Verification failed: " + ", ".join(failed)
        )

    return checks


def main() -> None:
    print("=" * 80)
    print("IFÁ V5: Φ-P2 TRANSPORT AND DUAL-CARRY AUTOMATON")
    print("=" * 80)

    local = derive_local_algebra()
    automaton = derive_carry_automaton()
    checks = verify(local, automaton)

    print_transport_vectors(local)
    print_four_target_sources(local)
    print_carry_automaton(automaton)

    print()
    print("THEOREM CHECKS")
    print("-" * 80)

    for name, passed in checks.items():
        print(
            f"{name:<48}"
            f"{'PASS' if passed else 'FAIL'}"
        )

    vector_path = save_transport_vectors(local)
    branching_path = save_branching_sources(local)
    edge_path = save_carry_edges(automaton)
    trace_path = save_carry_traces(automaton)
    dot_path = save_dot(automaton)
    summary_path = save_summary(local, automaton)

    print()
    print("Saved:")
    print(vector_path)
    print(branching_path)
    print(edge_path)
    print(trace_path)
    print(dot_path)
    print(summary_path)

    print()
    print("To render the automaton with Graphviz:")
    print(
        "dot -Tpng "
        f"{dot_path} "
        "-o "
        f"{RESULTS_DIR / 'phi_p2_dual_carry_automaton.png'}"
    )


if __name__ == "__main__":
    main()
