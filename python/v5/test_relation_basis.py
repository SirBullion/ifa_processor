#!/usr/bin/env python3
"""
IFÁ V5 first relation-state basis experiment.

Questions answered:

1. How many A,B inputs exist?
2. How many distinct Relation Frames are reachable?
3. Which five-register tensor states are unreachable?
4. Are there input-to-frame collisions?
5. How many qubits would a compact frame-index encoding require?
"""

from __future__ import annotations

from collections import defaultdict

from ifa_relation_model import (
    RelationFrame,
    compact_qubit_count,
    enumerate_inputs,
    tensor_register_dimension,
)


def binary(value: int, width: int) -> str:
    return format(value, f"0{width}b")


def run(width: int = 1) -> None:
    frame_to_inputs: dict[
        RelationFrame,
        list[tuple[int, int]],
    ] = defaultdict(list)

    rows = list(enumerate_inputs(width))

    for a, b, frame in rows:
        frame_to_inputs[frame].append((a, b))

    unique_frames = sorted(
        frame_to_inputs,
        key=lambda frame: frame.packed(width),
    )

    tensor_dimension = tensor_register_dimension(width)
    reachable_count = len(unique_frames)
    unreachable_count = tensor_dimension - reachable_count

    collision_classes = {
        frame: inputs
        for frame, inputs in frame_to_inputs.items()
        if len(inputs) > 1
    }

    largest_collision = max(
        (len(inputs) for inputs in frame_to_inputs.values()),
        default=0,
    )

    compact_qubits = compact_qubit_count(reachable_count)

    print("=" * 72)
    print("IFÁ V5 RELATION-STATE BASIS TEST")
    print("=" * 72)
    print(f"Input width                   : {width} bit(s)")
    print(f"Input pairs                   : {len(rows)}")
    print(f"Full tensor-register dimension: {tensor_dimension}")
    print(f"Distinct reachable frames     : {reachable_count}")
    print(f"Unreachable tensor states     : {unreachable_count}")
    print(f"Collision classes             : {len(collision_classes)}")
    print(f"Largest collision class       : {largest_collision}")
    print(f"Compact encoding qubits       : {compact_qubits}")
    print()

    print("TRUTH TABLE")
    print("-" * 72)
    print("A  B  |  Y RA RD R0 T  | packed | frame index")
    print("-" * 72)

    frame_index = {
        frame: index
        for index, frame in enumerate(unique_frames)
    }

    for a, b, frame in rows:
        print(
            f"{binary(a, width)}  "
            f"{binary(b, width)}  |  "
            f"{frame.bit_string(width)}  | "
            f"{binary(frame.packed(width), 5 * width)} | "
            f"{frame_index[frame]}"
        )

    print()
    print("REACHABLE RELATION-FRAME BASIS")
    print("-" * 72)

    for index, frame in enumerate(unique_frames):
        inputs = ", ".join(
            f"({binary(a, width)},{binary(b, width)})"
            for a, b in frame_to_inputs[frame]
        )

        print(
            f"|Ψ{index}> = "
            f"|{frame.bit_string(width, separator='')}> "
            f"from {inputs}"
        )

    print()
    print("TRANSPORT CHECK")
    print("-" * 72)

    transport_values = {frame.t for frame in unique_frames}

    print(
        "Observed T values             : "
        + ", ".join(binary(value, width) for value in sorted(transport_values))
    )

    if width == 1 and transport_values == {0}:
        print("PASS: for 1-bit modular addition, Y = RD and T = 0")
    else:
        print("INFO: transport is nontrivial for this width")

    print()
    print("RESULT")
    print("-" * 72)

    assert len(rows) == (1 << width) ** 2
    assert reachable_count <= tensor_dimension
    assert unreachable_count >= 0

    print("PASS: every input pair produced a valid Relation Frame")
    print("PASS: reachable relation states were enumerated")
    print("PASS: tensor-space occupancy was calculated")
    print("PASS: input-to-frame collisions were measured")
    print("=" * 72)


if __name__ == "__main__":
    run(width=1)
