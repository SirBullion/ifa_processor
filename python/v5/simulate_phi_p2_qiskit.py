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


def phi_p2_reference(value: int) -> int:
    """
    Classical Φ-P2 reference.

    Input bit order:
        value = (a << 1) | b

    Mapping:
        (a, b) -> (a, NOT(a XOR b))
    """
    if value < 0 or value > 3:
        raise ValueError("Φ-P2 input must be between 0 and 3")

    a = (value >> 1) & 1
    b = value & 1
    b_phi = 1 ^ a ^ b

    return (a << 1) | b_phi


def build_phi_p2_gate() -> QuantumCircuit:
    """
    Qiskit qubit convention used here:

        q[1] = a
        q[0] = b

    Φ-P2:
        b' = 1 XOR a XOR b
        a' = a

    Gate decomposition:
        CNOT a -> b
        X on b
    """
    circuit = QuantumCircuit(2, name="Phi-P2")

    circuit.cx(1, 0)
    circuit.x(0)

    return circuit


def prepare_basis_state(value: int) -> QuantumCircuit:
    """Prepare |ab>, where q[1]=a and q[0]=b."""
    circuit = QuantumCircuit(2)

    if value & 0b01:
        circuit.x(0)

    if value & 0b10:
        circuit.x(1)

    return circuit


def dominant_basis_state(state: Statevector) -> tuple[int, float]:
    probabilities = np.abs(state.data) ** 2
    index = int(np.argmax(probabilities))
    probability = float(probabilities[index])
    return index, probability


def test_basis_states(phi_gate: QuantumCircuit) -> int:
    failures = 0

    print("=== Φ-P2 BASIS-STATE SIMULATION ===")
    print()

    for value in range(4):
        circuit = prepare_basis_state(value)
        circuit.compose(phi_gate, inplace=True)

        output = Statevector.from_instruction(circuit)
        observed, probability = dominant_basis_state(output)
        expected = phi_p2_reference(value)

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
            f"|{value:02b}> -> |{observed:02b}>  "
            f"expected |{expected:02b}>  "
            f"P={probability:.12f}  {status}"
        )

        if not passed:
            failures += 1

    return failures


def test_unitarity(phi_gate: QuantumCircuit) -> int:
    print()
    print("=== UNITARITY TEST ===")
    print()

    matrix = Operator(phi_gate).data
    identity = np.eye(4, dtype=complex)
    product = matrix.conj().T @ matrix

    unitary = np.allclose(
        product,
        identity,
        atol=TOLERANCE,
    )

    print("U†U = I :", unitary)

    return 0 if unitary else 1


def test_self_inverse(phi_gate: QuantumCircuit) -> int:
    print()
    print("=== SELF-INVERSE TEST ===")
    print()

    matrix = Operator(phi_gate).data
    identity = np.eye(4, dtype=complex)

    self_inverse = np.allclose(
        matrix @ matrix,
        identity,
        atol=TOLERANCE,
    )

    print("U² = I  :", self_inverse)

    return 0 if self_inverse else 1


def test_superposition(phi_gate: QuantumCircuit) -> int:
    """
    Prepare:

        (|00> + |11>) / sqrt(2)

    Expected after Φ-P2:

        (|01> + |11>) / sqrt(2)
    """
    print()
    print("=== SUPERPOSITION TEST ===")
    print()

    circuit = QuantumCircuit(2)

    # Bell-like input:
    # (|00> + |11>) / sqrt(2)
    circuit.h(1)
    circuit.cx(1, 0)

    circuit.compose(phi_gate, inplace=True)

    output = Statevector.from_instruction(circuit)

    expected = np.zeros(4, dtype=complex)
    expected[0b01] = 1 / math.sqrt(2)
    expected[0b11] = 1 / math.sqrt(2)

    passed = np.allclose(
        output.data,
        expected,
        atol=TOLERANCE,
    )

    print("Expected non-zero amplitudes:")
    print("  |01> =", f"{expected[0b01]:.12f}")
    print("  |11> =", f"{expected[0b11]:.12f}")

    print()
    print("Observed statevector:")

    for index, amplitude in enumerate(output.data):
        if abs(amplitude) > TOLERANCE:
            print(f"  |{index:02b}> = {amplitude}")

    print()
    print("Superposition mapping :", passed)

    return 0 if passed else 1


def main() -> int:
    phi_gate = build_phi_p2_gate()

    print("=== Φ-P2 QUANTUM CIRCUIT ===")
    print()
    print(phi_gate.draw(output="text"))

    failures = 0
    failures += test_basis_states(phi_gate)
    failures += test_unitarity(phi_gate)
    failures += test_self_inverse(phi_gate)
    failures += test_superposition(phi_gate)

    print()
    print("=== FINAL RESULT ===")
    print("Failures :", failures)
    print("RESULT   :", "PASS" if failures == 0 else "FAIL")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
