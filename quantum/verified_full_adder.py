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


# ---------------------------------------------------------------------
# Classical reference
# ---------------------------------------------------------------------

def full_adder_reference(
    a: int,
    b: int,
    carry_in: int,
) -> tuple[int, int]:
    """
    Classical one-bit full adder.

    sum_bit  = a XOR b XOR carry_in
    carry_out = majority(a, b, carry_in)
    """
    sum_bit = a ^ b ^ carry_in

    carry_out = (
        (a & b)
        | (a & carry_in)
        | (b & carry_in)
    )

    return sum_bit, carry_out


def reversible_reference(
    a: int,
    b: int,
    carry_in: int,
    sum_target: int,
    carry_target: int,
) -> tuple[int, int, int, int, int]:
    """
    Exact reversible embedding used by the quantum circuit.
    """
    generated_sum = a ^ b ^ carry_in

    generated_carry = (
        (a & b)
        ^ (a & carry_in)
        ^ (b & carry_in)
    )

    return (
        a,
        b,
        carry_in,
        sum_target ^ generated_sum,
        carry_target ^ generated_carry,
    )


# ---------------------------------------------------------------------
# Quantum circuit
# ---------------------------------------------------------------------

def append_quantum_full_adder(
    circuit: QuantumCircuit,
    a,
    b,
    carry_in,
    sum_target,
    carry_target,
) -> None:
    """
    Reversible full-adder embedding.

    sum_target ^= a XOR b XOR carry_in

    carry_target ^=
        (a AND b)
        XOR (a AND carry_in)
        XOR (b AND carry_in)

    The three pairwise products equal the majority carry for every
    three-bit input.
    """

    # Sum channel
    circuit.cx(a, sum_target)
    circuit.cx(b, sum_target)
    circuit.cx(carry_in, sum_target)

    # Carry channel
    circuit.ccx(a, b, carry_target)
    circuit.ccx(a, carry_in, carry_target)
    circuit.ccx(b, carry_in, carry_target)


def build_quantum_full_adder() -> QuantumCircuit:
    """
    Qubit assignment:

        q0 = A
        q1 = B
        q2 = carry-in
        q3 = sum target
        q4 = carry target
    """
    circuit = QuantumCircuit(5, name="IFA_Full_Adder")

    append_quantum_full_adder(
        circuit,
        a=0,
        b=1,
        carry_in=2,
        sum_target=3,
        carry_target=4,
    )

    return circuit


# ---------------------------------------------------------------------
# State preparation and observation
# ---------------------------------------------------------------------

def prepare_basis_state(
    a: int,
    b: int,
    carry_in: int,
    sum_target: int = 0,
    carry_target: int = 0,
) -> QuantumCircuit:
    circuit = QuantumCircuit(5)

    values = [
        a,
        b,
        carry_in,
        sum_target,
        carry_target,
    ]

    for qubit, value in enumerate(values):
        if value:
            circuit.x(qubit)

    return circuit


def encode_basis_index(
    a: int,
    b: int,
    carry_in: int,
    sum_target: int,
    carry_target: int,
) -> int:
    return (
        (a << 0)
        | (b << 1)
        | (carry_in << 2)
        | (sum_target << 3)
        | (carry_target << 4)
    )


def dominant_basis_state(
    state: Statevector,
) -> tuple[int, float]:
    probabilities = np.abs(state.data) ** 2

    observed = int(np.argmax(probabilities))
    probability = float(probabilities[observed])

    return observed, probability


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

def test_truth_table(
    full_adder: QuantumCircuit,
) -> int:
    failures = 0

    print("=== QUANTUM FULL-ADDER TRUTH TABLE ===")
    print()
    print("A B Cin | Sum Cout | Probability Result")
    print("----------------------------------------")

    for a in range(2):
        for b in range(2):
            for carry_in in range(2):
                circuit = prepare_basis_state(
                    a,
                    b,
                    carry_in,
                )

                circuit.compose(full_adder, inplace=True)

                state = Statevector.from_instruction(circuit)
                observed, probability = dominant_basis_state(state)

                expected_sum, expected_carry = full_adder_reference(
                    a,
                    b,
                    carry_in,
                )

                expected_index = encode_basis_index(
                    a,
                    b,
                    carry_in,
                    expected_sum,
                    expected_carry,
                )

                passed = (
                    observed == expected_index
                    and math.isclose(
                        probability,
                        1.0,
                        abs_tol=TOLERANCE,
                    )
                )

                status = "PASS" if passed else "FAIL"

                print(
                    f"{a} {b}  {carry_in}  |"
                    f"  {expected_sum}    {expected_carry}   |"
                    f" {probability:.12f} {status}"
                )

                if not passed:
                    failures += 1

    print()
    print("Truth-table cases tested :", 8)
    print("Truth-table failures     :", failures)

    return failures


def test_all_32_basis_states(
    full_adder: QuantumCircuit,
) -> int:
    """
    Test every possible state, including non-zero target qubits.

    This verifies the complete reversible permutation rather than only
    the conventional target-zero full-adder use case.
    """
    failures = 0

    print()
    print("=== COMPLETE 32-STATE REVERSIBLE TEST ===")
    print()

    for input_index in range(32):
        a = (input_index >> 0) & 1
        b = (input_index >> 1) & 1
        carry_in = (input_index >> 2) & 1
        sum_target = (input_index >> 3) & 1
        carry_target = (input_index >> 4) & 1

        circuit = prepare_basis_state(
            a,
            b,
            carry_in,
            sum_target,
            carry_target,
        )

        circuit.compose(full_adder, inplace=True)

        state = Statevector.from_instruction(circuit)
        observed, probability = dominant_basis_state(state)

        expected_values = reversible_reference(
            a,
            b,
            carry_in,
            sum_target,
            carry_target,
        )

        expected_index = encode_basis_index(*expected_values)

        passed = (
            observed == expected_index
            and math.isclose(
                probability,
                1.0,
                abs_tol=TOLERANCE,
            )
        )

        if not passed:
            failures += 1

            print(
                f"FAIL |{input_index:05b}> "
                f"-> |{observed:05b}> "
                f"expected |{expected_index:05b}> "
                f"P={probability:.12f}"
            )

    print("Basis states tested :", 32)
    print("Basis failures      :", failures)

    return failures


def test_unitarity(
    full_adder: QuantumCircuit,
) -> int:
    print()
    print("=== FULL-ADDER UNITARITY TEST ===")
    print()

    matrix = Operator(full_adder).data
    identity = np.eye(32, dtype=complex)

    product = matrix.conj().T @ matrix

    unitary = np.allclose(
        product,
        identity,
        atol=TOLERANCE,
    )

    maximum_deviation = float(
        np.max(np.abs(product - identity))
    )

    print("U†U = I          :", unitary)
    print("Maximum deviation:", f"{maximum_deviation:.3e}")

    return 0 if unitary else 1


def test_self_inverse(
    full_adder: QuantumCircuit,
) -> int:
    print()
    print("=== FULL-ADDER SELF-INVERSE TEST ===")
    print()

    matrix = Operator(full_adder).data
    identity = np.eye(32, dtype=complex)

    product = matrix @ matrix

    self_inverse = np.allclose(
        product,
        identity,
        atol=TOLERANCE,
    )

    maximum_deviation = float(
        np.max(np.abs(product - identity))
    )

    print("U² = I           :", self_inverse)
    print("Maximum deviation:", f"{maximum_deviation:.3e}")

    return 0 if self_inverse else 1


def test_round_trip(
    full_adder: QuantumCircuit,
) -> int:
    failures = 0

    print()
    print("=== FULL-ADDER ROUND-TRIP TEST ===")
    print()

    for input_index in range(32):
        circuit = QuantumCircuit(5)

        for qubit in range(5):
            if (input_index >> qubit) & 1:
                circuit.x(qubit)

        circuit.compose(full_adder, inplace=True)
        circuit.compose(full_adder, inplace=True)

        state = Statevector.from_instruction(circuit)
        observed, probability = dominant_basis_state(state)

        passed = (
            observed == input_index
            and math.isclose(
                probability,
                1.0,
                abs_tol=TOLERANCE,
            )
        )

        if not passed:
            failures += 1

            print(
                f"FAIL |{input_index:05b}> "
                f"-> |{observed:05b}> "
                f"P={probability:.12f}"
            )

    print("Round trips tested :", 32)
    print("Round-trip failures:", failures)

    return failures


def test_superposition(
    full_adder: QuantumCircuit,
) -> int:
    """
    Prepare:

        (|A=0,B=0,Cin=0> + |A=1,B=1,Cin=1>) / sqrt(2)

    Expected:

        |000, Sum=0, Cout=0>
        +
        |111, Sum=1, Cout=1>
    """
    print()
    print("=== FULL-ADDER SUPERPOSITION TEST ===")
    print()

    circuit = QuantumCircuit(5)

    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(0, 2)

    circuit.compose(full_adder, inplace=True)

    observed = Statevector.from_instruction(circuit)

    expected = np.zeros(32, dtype=complex)

    index_000 = encode_basis_index(
        0,
        0,
        0,
        0,
        0,
    )

    index_111 = encode_basis_index(
        1,
        1,
        1,
        1,
        1,
    )

    expected[index_000] = 1 / math.sqrt(2)
    expected[index_111] = 1 / math.sqrt(2)

    passed = np.allclose(
        observed.data,
        expected,
        atol=TOLERANCE,
    )

    print("Expected non-zero states:")
    print(f"  |{index_000:05b}>")
    print(f"  |{index_111:05b}>")

    print()
    print("Observed non-zero amplitudes:")

    for index, amplitude in enumerate(observed.data):
        if abs(amplitude) > TOLERANCE:
            print(
                f"  |{index:05b}> = {amplitude}"
            )

    print()
    print("Superposition mapping:", passed)

    return 0 if passed else 1


def test_uniform_superposition(
    full_adder: QuantumCircuit,
) -> int:
    """
    Apply the full adder to a uniform superposition of all five-qubit
    basis states.

    A reversible permutation must preserve the uniform state.
    """
    print()
    print("=== UNIFORM SUPERPOSITION TEST ===")
    print()

    circuit = QuantumCircuit(5)

    for qubit in range(5):
        circuit.h(qubit)

    before = Statevector.from_instruction(circuit)

    circuit.compose(full_adder, inplace=True)

    after = Statevector.from_instruction(circuit)

    passed = np.allclose(
        after.data,
        before.data,
        atol=TOLERANCE,
    )

    norm = float(np.linalg.norm(after.data))

    print("Uniform state preserved:", passed)
    print("Output state norm       :", f"{norm:.12f}")

    return 0 if passed else 1


def main() -> int:
    full_adder = build_quantum_full_adder()

    print("=== IFÁ REVERSIBLE QUANTUM FULL ADDER ===")
    print()
    print(full_adder.draw(output="text"))
    print()

    print("Qubits       :", full_adder.num_qubits)
    print("Circuit depth:", full_adder.depth())
    print("Gate count   :", full_adder.count_ops())
    print()

    failures = 0

    failures += test_truth_table(full_adder)
    failures += test_all_32_basis_states(full_adder)
    failures += test_unitarity(full_adder)
    failures += test_self_inverse(full_adder)
    failures += test_round_trip(full_adder)
    failures += test_superposition(full_adder)
    failures += test_uniform_superposition(full_adder)

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


