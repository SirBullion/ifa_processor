#!/usr/bin/env python3

from __future__ import annotations

import math
import sys

import numpy as np

try:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Operator, Statevector
except ImportError as exc:
    raise SystemExit(
        "Qiskit is not installed.\n"
        "Install it with:\n"
        "    python3 -m pip install qiskit\n"
    ) from exc


TOLERANCE = 1e-10
NUMBER_OF_STATES = 256


def phi_p2_reference(value: int) -> int:
    """
    Classical Φ-P2 reference for a two-bit pair.

    Pair convention:
        value[1] = anchor bit a
        value[0] = agreement/source bit b

    Transform:
        (a, b) -> (a, NOT(a XOR b))
    """
    if not 0 <= value <= 0b11:
        raise ValueError("Φ-P2 input must be between 0 and 3")

    a = (value >> 1) & 1
    b = value & 1
    b_phi = 1 ^ a ^ b

    return (a << 1) | b_phi


def phi_p8_reference(value: int) -> int:
    """
    Apply Φ-P2 independently to four adjacent two-bit pairs:

        bits [1:0]
        bits [3:2]
        bits [5:4]
        bits [7:6]
    """
    if not 0 <= value <= 0xFF:
        raise ValueError("Φ-P8 input must be between 0 and 255")

    output = 0

    for pair_index in range(4):
        shift = 2 * pair_index
        pair = (value >> shift) & 0b11
        transformed_pair = phi_p2_reference(pair)
        output |= transformed_pair << shift

    return output


def append_phi_p2(
    circuit: QuantumCircuit,
    anchor_qubit: int,
    agreement_qubit: int,
) -> None:
    """
    Append one Φ-P2 block.

    For the selected pair:

        anchor'    = anchor
        agreement' = 1 XOR anchor XOR agreement

    Quantum decomposition:

        CNOT(anchor -> agreement)
        X(agreement)
    """
    circuit.cx(anchor_qubit, agreement_qubit)
    circuit.x(agreement_qubit)


def build_phi_p8_circuit() -> QuantumCircuit:
    """
    Build Φ-P8 as four independent Φ-P2 cells.

    Qiskit uses little-endian state labels:

        q[7] ... q[1] q[0]

    Pair allocation:

        Φ-P2 block 0: anchor q1, agreement q0
        Φ-P2 block 1: anchor q3, agreement q2
        Φ-P2 block 2: anchor q5, agreement q4
        Φ-P2 block 3: anchor q7, agreement q6
    """
    circuit = QuantumCircuit(8, name="Phi-P8")

    for pair_index in range(4):
        agreement_qubit = 2 * pair_index
        anchor_qubit = agreement_qubit + 1

        append_phi_p2(
            circuit,
            anchor_qubit=anchor_qubit,
            agreement_qubit=agreement_qubit,
        )

    return circuit


def prepare_basis_state(value: int) -> QuantumCircuit:
    """Prepare the 8-qubit computational basis state |value>."""
    if not 0 <= value <= 0xFF:
        raise ValueError("Basis value must be between 0 and 255")

    circuit = QuantumCircuit(8)

    for qubit in range(8):
        if (value >> qubit) & 1:
            circuit.x(qubit)

    return circuit


def dominant_basis_state(
    state: Statevector,
) -> tuple[int, float]:
    probabilities = np.abs(state.data) ** 2
    observed = int(np.argmax(probabilities))
    probability = float(probabilities[observed])

    return observed, probability


def test_all_basis_states(
    phi_p8: QuantumCircuit,
) -> int:
    failures = 0

    print("=== Φ-P8 EXHAUSTIVE BASIS-STATE SIMULATION ===")
    print()

    for input_value in range(NUMBER_OF_STATES):
        circuit = prepare_basis_state(input_value)
        circuit.compose(phi_p8, inplace=True)

        output_state = Statevector.from_instruction(circuit)

        observed, probability = dominant_basis_state(output_state)
        expected = phi_p8_reference(input_value)

        passed = (
            observed == expected
            and math.isclose(
                probability,
                1.0,
                abs_tol=TOLERANCE,
            )
        )

        if not passed:
            failures += 1

            if failures <= 20:
                print(
                    f"FAIL "
                    f"|{input_value:08b}> "
                    f"-> |{observed:08b}> "
                    f"expected |{expected:08b}> "
                    f"P={probability:.12f}"
                )

    print(f"Basis states tested : {NUMBER_OF_STATES}")
    print(f"Basis failures      : {failures}")

    return failures


def test_selected_mappings(
    phi_p8: QuantumCircuit,
) -> int:
    failures = 0

    examples = [
        0x00,
        0x01,
        0x02,
        0x03,
        0x55,
        0xAA,
        0xF0,
        0xFF,
    ]

    print()
    print("=== SELECTED Φ-P8 MAPPINGS ===")
    print()

    for input_value in examples:
        circuit = prepare_basis_state(input_value)
        circuit.compose(phi_p8, inplace=True)

        output_state = Statevector.from_instruction(circuit)
        observed, probability = dominant_basis_state(output_state)
        expected = phi_p8_reference(input_value)

        passed = (
            observed == expected
            and math.isclose(
                probability,
                1.0,
                abs_tol=TOLERANCE,
            )
        )

        status = "PASS" if passed else "FAIL"

        print(
            f"|{input_value:08b}> "
            f"-> |{observed:08b}>  "
            f"expected |{expected:08b}>  "
            f"P={probability:.12f}  "
            f"{status}"
        )

        if not passed:
            failures += 1

    return failures


def test_unitarity(
    phi_p8: QuantumCircuit,
) -> int:
    print()
    print("=== Φ-P8 UNITARITY TEST ===")
    print()

    matrix = Operator(phi_p8).data
    identity = np.eye(NUMBER_OF_STATES, dtype=complex)
    product = matrix.conj().T @ matrix

    unitary = np.allclose(
        product,
        identity,
        atol=TOLERANCE,
    )

    maximum_error = float(
        np.max(np.abs(product - identity))
    )

    print("U†U = I          :", unitary)
    print("Maximum deviation:", f"{maximum_error:.3e}")

    return 0 if unitary else 1


def test_self_inverse(
    phi_p8: QuantumCircuit,
) -> int:
    print()
    print("=== Φ-P8 SELF-INVERSE TEST ===")
    print()

    matrix = Operator(phi_p8).data
    identity = np.eye(NUMBER_OF_STATES, dtype=complex)
    product = matrix @ matrix

    self_inverse = np.allclose(
        product,
        identity,
        atol=TOLERANCE,
    )

    maximum_error = float(
        np.max(np.abs(product - identity))
    )

    print("U² = I           :", self_inverse)
    print("Maximum deviation:", f"{maximum_error:.3e}")

    return 0 if self_inverse else 1


def test_round_trip_basis_states(
    phi_p8: QuantumCircuit,
) -> int:
    failures = 0

    print()
    print("=== Φ-P8 ROUND-TRIP TEST ===")
    print()

    for input_value in range(NUMBER_OF_STATES):
        circuit = prepare_basis_state(input_value)

        circuit.compose(phi_p8, inplace=True)
        circuit.compose(phi_p8, inplace=True)

        output_state = Statevector.from_instruction(circuit)
        observed, probability = dominant_basis_state(output_state)

        passed = (
            observed == input_value
            and math.isclose(
                probability,
                1.0,
                abs_tol=TOLERANCE,
            )
        )

        if not passed:
            failures += 1

            if failures <= 20:
                print(
                    f"FAIL round trip "
                    f"|{input_value:08b}> "
                    f"-> |{observed:08b}> "
                    f"P={probability:.12f}"
                )

    print(f"Round trips tested : {NUMBER_OF_STATES}")
    print(f"Round-trip failures: {failures}")

    return failures


def test_superposition(
    phi_p8: QuantumCircuit,
) -> int:
    """
    Prepare the GHZ-like state:

        (|00000000> + |11111111>) / sqrt(2)

    Since:

        Φ-P8(00000000) = 01010101
        Φ-P8(11111111) = 11111111

    the expected output is:

        (|01010101> + |11111111>) / sqrt(2)
    """
    print()
    print("=== Φ-P8 SUPERPOSITION TEST ===")
    print()

    circuit = QuantumCircuit(8)

    circuit.h(7)

    for qubit in range(6, -1, -1):
        circuit.cx(7, qubit)

    circuit.compose(phi_p8, inplace=True)

    output_state = Statevector.from_instruction(circuit)

    expected = np.zeros(NUMBER_OF_STATES, dtype=complex)

    first_output = phi_p8_reference(0x00)
    second_output = phi_p8_reference(0xFF)

    expected[first_output] = 1 / math.sqrt(2)
    expected[second_output] = 1 / math.sqrt(2)

    passed = np.allclose(
        output_state.data,
        expected,
        atol=TOLERANCE,
    )

    print("Input components:")
    print("  |00000000>")
    print("  |11111111>")

    print()
    print("Expected output components:")
    print(f"  |{first_output:08b}>")
    print(f"  |{second_output:08b}>")

    print()
    print("Observed non-zero amplitudes:")

    for index, amplitude in enumerate(output_state.data):
        if abs(amplitude) > TOLERANCE:
            print(
                f"  |{index:08b}> = {amplitude}"
            )

    print()
    print("Superposition mapping:", passed)

    return 0 if passed else 1


def main() -> int:
    phi_p8 = build_phi_p8_circuit()

    print("=== Φ-P8 QUANTUM CIRCUIT ===")
    print()
    print(phi_p8.draw(output="text"))
    print()

    failures = 0

    failures += test_selected_mappings(phi_p8)
    failures += test_all_basis_states(phi_p8)
    failures += test_unitarity(phi_p8)
    failures += test_self_inverse(phi_p8)
    failures += test_round_trip_basis_states(phi_p8)
    failures += test_superposition(phi_p8)

    print()
    print("=== FINAL RESULT ===")
    print("Total failures :", failures)
    print(
        "RESULT         :",
        "PASS" if failures == 0 else "FAIL",
    )

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())


