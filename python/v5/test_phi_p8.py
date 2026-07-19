#!/usr/bin/env python3
"""
Exhaustive IFÁ V5 Φ-P8 test.

Tests:
    1. P2 truth table
    2. Exhaustive 256-state mapping
    3. Bijection
    4. Inverse reconstruction
    5. Self-inverse property
    6. Exact operator order
    7. Permutation-matrix unitarity
    8. Cycle decomposition
    9. Eigenvalues
    10. Superposition norm preservation
    11. Tensor action on all 65,536 operand pairs
"""

from __future__ import annotations

import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from python.v5.ifa_phi_p8 import (  # noqa: E402
    bit_string,
    permutation_vector,
    phi_p2,
    phi_p2_inverse,
    phi_p8,
    phi_p8_inverse,
)


RESULTS_DIR = PROJECT_ROOT / "python" / "v5" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def create_permutation_matrix() -> np.ndarray:
    """
    Create U satisfying:

        U|x> = |Φ-P8(x)>
    """
    matrix = np.zeros((256, 256), dtype=np.complex128)

    for x in range(256):
        y = phi_p8(x)
        matrix[y, x] = 1.0

    return matrix


def cycle_decomposition(
    permutation: tuple[int, ...],
) -> list[list[int]]:
    visited: set[int] = set()
    cycles: list[list[int]] = []

    for start in range(len(permutation)):
        if start in visited:
            continue

        cycle: list[int] = []
        current = start

        while current not in visited:
            visited.add(current)
            cycle.append(current)
            current = permutation[current]

        cycles.append(cycle)

    return cycles


def test_p2() -> list[dict[str, int]]:
    expected = {
        (0, 0): (0, 1),
        (0, 1): (0, 0),
        (1, 0): (1, 0),
        (1, 1): (1, 1),
    }

    rows: list[dict[str, int]] = []

    print("\nP2 ANCHOR–AGREEMENT TABLE")
    print("-------------------------------------------")
    print("A B | Anchor Agreement | Recovered A B")

    for a in (0, 1):
        for b in (0, 1):
            anchor, agreement = phi_p2(a, b)
            recovered_a, recovered_b = phi_p2_inverse(
                anchor,
                agreement,
            )

            require(
                (anchor, agreement) == expected[(a, b)],
                f"Incorrect P2 output for A={a}, B={b}",
            )

            require(
                (recovered_a, recovered_b) == (a, b),
                f"Incorrect P2 inverse for A={a}, B={b}",
            )

            print(
                f"{a} {b} |"
                f"   {anchor}        {agreement}"
                f"      |     {recovered_a} {recovered_b}"
            )

            rows.append(
                {
                    "A": a,
                    "B": b,
                    "Anchor": anchor,
                    "Agreement": agreement,
                    "Recovered_A": recovered_a,
                    "Recovered_B": recovered_b,
                }
            )

    return rows


def test_all_byte_states() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for x in range(256):
        y = phi_p8(x)
        recovered = phi_p8_inverse(y)
        repeated = phi_p8(y)

        require(
            recovered == x,
            (
                f"Inverse failure: x={bit_string(x)}, "
                f"y={bit_string(y)}, "
                f"recovered={bit_string(recovered)}"
            ),
        )

        require(
            repeated == x,
            f"Self-inverse failure for x={bit_string(x)}",
        )

        rows.append(
            {
                "x_decimal": x,
                "x_binary": bit_string(x),
                "phi_p8_decimal": y,
                "phi_p8_binary": bit_string(y),
                "recovered_decimal": recovered,
                "recovered_binary": bit_string(recovered),
            }
        )

    return rows


def test_bijection(permutation: tuple[int, ...]) -> None:
    require(
        len(permutation) == 256,
        "Permutation must contain 256 values",
    )

    require(
        len(set(permutation)) == 256,
        "Φ-P8 is not injective",
    )

    require(
        set(permutation) == set(range(256)),
        "Φ-P8 is not surjective",
    )


def test_unitarity(matrix: np.ndarray) -> None:
    identity = np.eye(256, dtype=np.complex128)

    require(
        np.allclose(matrix.conj().T @ matrix, identity),
        "U†U != I",
    )

    require(
        np.allclose(matrix @ matrix.conj().T, identity),
        "UU† != I",
    )


def test_operator_order(matrix: np.ndarray) -> int:
    identity = np.eye(256, dtype=np.complex128)

    require(
        not np.allclose(matrix, identity),
        "Φ-P8 is unexpectedly the identity",
    )

    square = matrix @ matrix

    require(
        np.allclose(square, identity),
        "Φ-P8 does not satisfy P8² = I",
    )

    fourth_power = square @ square

    require(
        np.allclose(fourth_power, identity),
        "Φ-P8 does not satisfy P8⁴ = I",
    )

    return 2


def test_basis_action(matrix: np.ndarray) -> None:
    for x in range(256):
        state = np.zeros(256, dtype=np.complex128)
        state[x] = 1.0

        result = matrix @ state

        expected = np.zeros(256, dtype=np.complex128)
        expected[phi_p8(x)] = 1.0

        require(
            np.allclose(result, expected),
            f"Incorrect matrix action for x={x}",
        )


def test_superposition(matrix: np.ndarray) -> dict[str, object]:
    state = np.zeros(256, dtype=np.complex128)

    state[0x00] = 1 / math.sqrt(2)
    state[0xFF] = 1 / math.sqrt(2)

    before_norm = float(np.linalg.norm(state))
    result = matrix @ state
    after_norm = float(np.linalg.norm(result))

    require(
        np.isclose(before_norm, 1.0),
        "Input state is not normalized",
    )

    require(
        np.isclose(after_norm, 1.0),
        "Φ-P8 failed to preserve the state norm",
    )

    support = []

    for index, amplitude in enumerate(result):
        if not np.isclose(amplitude, 0.0):
            support.append(
                {
                    "state": bit_string(index),
                    "amplitude_real": float(amplitude.real),
                    "amplitude_imag": float(amplitude.imag),
                    "probability": float(abs(amplitude) ** 2),
                }
            )

    return {
        "before_norm": before_norm,
        "after_norm": after_norm,
        "output_support": support,
    }


def test_tensor_action() -> None:
    """
    Verify:

        |A>|B> -> |Φ-P8(A)>|Φ-P8(B)>

    for every one of the 65,536 byte pairs.
    """
    output_states: set[int] = set()

    for a in range(256):
        pa = phi_p8(a)

        for b in range(256):
            pb = phi_p8(b)

            input_index = (a << 8) | b
            output_index = (pa << 8) | pb

            recovered_a = phi_p8_inverse(pa)
            recovered_b = phi_p8_inverse(pb)
            recovered_index = (recovered_a << 8) | recovered_b

            require(
                recovered_index == input_index,
                f"Tensor reconstruction failure for A={a}, B={b}",
            )

            output_states.add(output_index)

    require(
        len(output_states) == 65_536,
        "P8 tensor P8 is not bijective",
    )


def eigenvalue_summary(
    matrix: np.ndarray,
) -> dict[str, object]:
    eigenvalues = np.linalg.eigvals(matrix)

    rounded = [
        complex(
            round(float(value.real), 8),
            round(float(value.imag), 8),
        )
        for value in eigenvalues
    ]

    multiplicities = Counter(rounded)

    allowed = {
        complex(1.0, 0.0),
        complex(-1.0, 0.0),
    }

    require(
        set(multiplicities).issubset(allowed),
        f"Unexpected eigenvalues: {set(multiplicities) - allowed}",
    )

    return {
        "multiplicities": {
            str(value): count
            for value, count in sorted(
                multiplicities.items(),
                key=lambda item: item[0].real,
            )
        },
        "spectral_radius": float(
            max(abs(value) for value in eigenvalues)
        ),
    }


def write_csv(
    path: Path,
    rows: list[dict[str, object]],
) -> None:
    if not rows:
        return

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    print("=" * 68)
    print("IFÁ V5 CANONICAL Φ-P8 EXHAUSTIVE TEST")
    print("=" * 68)

    p2_rows = test_p2()
    mapping_rows = test_all_byte_states()

    permutation = permutation_vector()
    test_bijection(permutation)

    matrix = create_permutation_matrix()

    test_unitarity(matrix)
    test_basis_action(matrix)

    exact_order = test_operator_order(matrix)

    cycles = cycle_decomposition(permutation)
    cycle_histogram = Counter(len(cycle) for cycle in cycles)

    fixed_points = [
        value
        for value in range(256)
        if phi_p8(value) == value
    ]

    eigenvalues = eigenvalue_summary(matrix)
    superposition = test_superposition(matrix)

    print("\nTesting Φ-P8 tensor Φ-P8 over 65,536 basis states...")
    test_tensor_action()

    summary = {
        "transform": "IFÁ Φ-P8 Anchor–Agreement",
        "input_states": 256,
        "unique_outputs": len(set(permutation)),
        "bijective": True,
        "inverse_reconstruction": True,
        "self_inverse": True,
        "exact_operator_order": exact_order,
        "p8_squared_equals_identity": True,
        "p8_fourth_equals_identity": True,
        "unitary": True,
        "fixed_point_count": len(fixed_points),
        "fixed_points_binary": [
            bit_string(value)
            for value in fixed_points
        ],
        "cycle_count": len(cycles),
        "cycle_histogram": dict(
            sorted(cycle_histogram.items())
        ),
        "eigenvalues": eigenvalues,
        "superposition": superposition,
        "tensor_states_tested": 65_536,
        "tensor_bijection": True,
    }

    write_csv(
        RESULTS_DIR / "phi_p2_truth_table.csv",
        p2_rows,
    )

    write_csv(
        RESULTS_DIR / "phi_p8_mapping.csv",
        mapping_rows,
    )

    with (
        RESULTS_DIR / "phi_p8_summary.json"
    ).open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    with (
        RESULTS_DIR / "phi_p8_cycles.txt"
    ).open("w", encoding="utf-8") as handle:
        for number, cycle in enumerate(cycles, start=1):
            states = " -> ".join(
                bit_string(value)
                for value in cycle
            )

            if len(cycle) > 1:
                states += f" -> {bit_string(cycle[0])}"

            handle.write(
                f"Cycle {number:03d} "
                f"(length {len(cycle)}): {states}\n"
            )

    print("\n" + "=" * 68)
    print("Φ-P8 TEST REPORT")
    print("=" * 68)
    print("Input states                 : 256")
    print("Unique outputs               : 256")
    print("Bijection                    : PASS")
    print("Inverse reconstruction       : PASS")
    print("Self-inverse P8² = I         : PASS")
    print("P8⁴ = I                      : PASS")
    print(f"Exact operator order         : {exact_order}")
    print("Permutation matrix unitary   : PASS")
    print("Basis-state action           : PASS")
    print("Superposition norm           : PASS")
    print("Tensor states tested         : 65,536")
    print("P8 tensor P8 bijection       : PASS")
    print(f"Fixed points                 : {len(fixed_points)}")
    print(
        "Cycle histogram              : "
        f"{dict(sorted(cycle_histogram.items()))}"
    )
    print(
        "Eigenvalue multiplicities    : "
        f"{eigenvalues['multiplicities']}"
    )
    print("=" * 68)

    print("\nSaved:")
    print(RESULTS_DIR / "phi_p2_truth_table.csv")
    print(RESULTS_DIR / "phi_p8_mapping.csv")
    print(RESULTS_DIR / "phi_p8_cycles.txt")
    print(RESULTS_DIR / "phi_p8_summary.json")

    print("\nPASS: Canonical Φ-P8 is ready for V5.")


if __name__ == "__main__":
    main()
