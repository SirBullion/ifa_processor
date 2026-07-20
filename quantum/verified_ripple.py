#!/usr/bin/env python3

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from typing import Iterable

try:
    from qiskit import QuantumCircuit, QuantumRegister
except ImportError as exc:
    raise SystemExit(
        "Qiskit is not installed.\n"
        "Install it with:\n"
        "    python3 -m pip install qiskit\n"
    ) from exc


TOLERANCE = 1e-10
WIDTH = 4
MASK = (1 << WIDTH) - 1


# ================================================================
# Classical reference model
# ================================================================

def phi_p2_reference(value: int) -> int:
    """
    Φ-P2:

        (anchor, agreement)
            ->
        (anchor, NOT(anchor XOR agreement))

    Pair bit convention:

        bit 1 = anchor
        bit 0 = agreement
    """
    if not 0 <= value <= 0b11:
        raise ValueError("Φ-P2 input must be between 0 and 3")

    anchor = (value >> 1) & 1
    agreement = value & 1

    transformed_agreement = 1 ^ anchor ^ agreement

    return (anchor << 1) | transformed_agreement


def phi_p4_reference(value: int) -> int:
    """
    Apply Φ-P2 independently to:

        bits [1:0]
        bits [3:2]
    """
    if not 0 <= value <= MASK:
        raise ValueError("Φ-P4 input must be a four-bit value")

    output = 0

    for pair_index in range(WIDTH // 2):
        shift = 2 * pair_index
        pair = (value >> shift) & 0b11

        output |= phi_p2_reference(pair) << shift

    return output


def ripple_reference(
    a: int,
    b: int,
    carry_initial: int,
) -> tuple[int, list[int]]:
    """
    Classical ripple reference.

    Returns:

        sum_value
        [C0, C1, C2, C3, C4]
    """
    carries = [carry_initial]
    sum_value = 0

    carry = carry_initial

    for bit in range(WIDTH):
        a_bit = (a >> bit) & 1
        b_bit = (b >> bit) & 1

        sum_bit = a_bit ^ b_bit ^ carry

        carry_next = (
            (a_bit & b_bit)
            | (a_bit & carry)
            | (b_bit & carry)
        )

        sum_value |= sum_bit << bit
        carries.append(carry_next)

        carry = carry_next

    return sum_value, carries


# ================================================================
# Quantum gate definitions
# ================================================================

def append_phi_p2(
    circuit: QuantumCircuit,
    anchor,
    agreement,
) -> None:
    """
    agreement ^= anchor
    agreement ^= 1
    """
    circuit.cx(anchor, agreement)
    circuit.x(agreement)


def append_phi_p4(
    circuit: QuantumCircuit,
    register: QuantumRegister,
) -> None:
    for pair_index in range(WIDTH // 2):
        agreement_index = 2 * pair_index
        anchor_index = agreement_index + 1

        append_phi_p2(
            circuit,
            anchor=register[anchor_index],
            agreement=register[agreement_index],
        )


def append_quantum_full_adder(
    circuit: QuantumCircuit,
    a,
    b,
    carry_in,
    sum_target,
    carry_out_target,
) -> None:
    """
    Reversible full-adder embedding:

        sum_target ^=
            a XOR b XOR carry_in

        carry_out_target ^=
            ab XOR a·carry_in XOR b·carry_in
    """

    # Sum relation
    circuit.cx(a, sum_target)
    circuit.cx(b, sum_target)
    circuit.cx(carry_in, sum_target)

    # Carry relation
    circuit.ccx(a, b, carry_out_target)
    circuit.ccx(a, carry_in, carry_out_target)
    circuit.ccx(b, carry_in, carry_out_target)


def append_ripple_channel(
    circuit: QuantumCircuit,
    a_register: QuantumRegister,
    b_register: QuantumRegister,
    sum_register: QuantumRegister,
    carry_register: QuantumRegister,
) -> None:
    """
    Four-stage ripple propagation:

        C0 -> FA0 -> C1
        C1 -> FA1 -> C2
        C2 -> FA2 -> C3
        C3 -> FA3 -> C4
    """
    for bit in range(WIDTH):
        append_quantum_full_adder(
            circuit,
            a=a_register[bit],
            b=b_register[bit],
            carry_in=carry_register[bit],
            sum_target=sum_register[bit],
            carry_out_target=carry_register[bit + 1],
        )


@dataclass
class CircuitLayout:
    circuit: QuantumCircuit

    a: QuantumRegister
    b: QuantumRegister

    a_phi: QuantumRegister
    b_phi: QuantumRegister

    sum_direct: QuantumRegister
    sum_phi: QuantumRegister

    carry_direct: QuantumRegister
    carry_phi: QuantumRegister


def build_dual_carry_ripple() -> CircuitLayout:
    """
    Registers:

        A       4 qubits
        B       4 qubits

        Aφ      4 qubits
        Bφ      4 qubits

        S       4 qubits
        Sφ      4 qubits

        C       5 qubits
        Cφ      5 qubits

    Total: 34 qubits

    Aφ and Bφ begin at zero and are coherently prepared from A and B.
    For computational-basis inputs this acts as copying. For a
    superposition it creates the corresponding entangled relation.
    """

    a = QuantumRegister(WIDTH, "A")
    b = QuantumRegister(WIDTH, "B")

    a_phi = QuantumRegister(WIDTH, "A_phi")
    b_phi = QuantumRegister(WIDTH, "B_phi")

    sum_direct = QuantumRegister(WIDTH, "S")
    sum_phi = QuantumRegister(WIDTH, "S_phi")

    carry_direct = QuantumRegister(WIDTH + 1, "C")
    carry_phi = QuantumRegister(WIDTH + 1, "C_phi")

    circuit = QuantumCircuit(
        a,
        b,
        a_phi,
        b_phi,
        sum_direct,
        sum_phi,
        carry_direct,
        carry_phi,
        name="IFA_Dual_Carry_Ripple_4",
    )

    # ------------------------------------------------------------
    # Prepare coherent copies for the Φ channel
    # ------------------------------------------------------------

    for bit in range(WIDTH):
        circuit.cx(a[bit], a_phi[bit])
        circuit.cx(b[bit], b_phi[bit])

    # ------------------------------------------------------------
    # Apply the Φ coordinate transform
    # ------------------------------------------------------------

    append_phi_p4(circuit, a_phi)
    append_phi_p4(circuit, b_phi)

    circuit.barrier()

    # ------------------------------------------------------------
    # Direct ripple channel
    # ------------------------------------------------------------

    append_ripple_channel(
        circuit,
        a_register=a,
        b_register=b,
        sum_register=sum_direct,
        carry_register=carry_direct,
    )

    circuit.barrier()

    # ------------------------------------------------------------
    # Φ ripple channel
    # ------------------------------------------------------------

    append_ripple_channel(
        circuit,
        a_register=a_phi,
        b_register=b_phi,
        sum_register=sum_phi,
        carry_register=carry_phi,
    )

    return CircuitLayout(
        circuit=circuit,
        a=a,
        b=b,
        a_phi=a_phi,
        b_phi=b_phi,
        sum_direct=sum_direct,
        sum_phi=sum_phi,
        carry_direct=carry_direct,
        carry_phi=carry_phi,
    )


# ================================================================
# Exact sparse simulator for X, CNOT and Toffoli circuits
# ================================================================

def qubit_index(
    circuit: QuantumCircuit,
    qubit,
) -> int:
    return circuit.find_bit(qubit).index


def apply_basis_circuit(
    circuit: QuantumCircuit,
    basis_index: int,
) -> int:
    """
    Apply the actual Qiskit circuit to one computational-basis state.

    Because this circuit consists only of:

        X
        CNOT
        Toffoli
        barrier

    every input basis state maps to exactly one output basis state.
    """

    state = basis_index

    for instruction in circuit.data:
        operation = instruction.operation
        name = operation.name

        qubits = [
            qubit_index(circuit, qubit)
            for qubit in instruction.qubits
        ]

        if name == "barrier":
            continue

        if name == "x":
            target = qubits[0]
            state ^= 1 << target
            continue

        if name == "cx":
            control, target = qubits

            if (state >> control) & 1:
                state ^= 1 << target

            continue

        if name == "ccx":
            control_a, control_b, target = qubits

            if (
                ((state >> control_a) & 1)
                and ((state >> control_b) & 1)
            ):
                state ^= 1 << target

            continue

        raise RuntimeError(
            f"Unsupported circuit operation: {name}"
        )

    return state


def apply_sparse_state(
    circuit: QuantumCircuit,
    amplitudes: dict[int, complex],
) -> dict[int, complex]:
    """
    Apply the reversible circuit to a sparse superposition.
    """
    output: dict[int, complex] = {}

    for basis_index, amplitude in amplitudes.items():
        mapped_index = apply_basis_circuit(
            circuit,
            basis_index,
        )

        output[mapped_index] = (
            output.get(mapped_index, 0j)
            + amplitude
        )

    return output


# ================================================================
# Register encoding and decoding
# ================================================================

def set_qubit(
    basis_index: int,
    circuit: QuantumCircuit,
    qubit,
    value: int,
) -> int:
    index = qubit_index(circuit, qubit)

    if value:
        basis_index |= 1 << index
    else:
        basis_index &= ~(1 << index)

    return basis_index


def read_qubit(
    basis_index: int,
    circuit: QuantumCircuit,
    qubit,
) -> int:
    index = qubit_index(circuit, qubit)
    return (basis_index >> index) & 1


def write_register(
    basis_index: int,
    circuit: QuantumCircuit,
    register: QuantumRegister,
    value: int,
) -> int:
    for bit in range(len(register)):
        basis_index = set_qubit(
            basis_index,
            circuit,
            register[bit],
            (value >> bit) & 1,
        )

    return basis_index


def read_register(
    basis_index: int,
    circuit: QuantumCircuit,
    register: QuantumRegister,
) -> int:
    value = 0

    for bit in range(len(register)):
        value |= (
            read_qubit(
                basis_index,
                circuit,
                register[bit],
            )
            << bit
        )

    return value


def prepare_input_basis(
    layout: CircuitLayout,
    a: int,
    b: int,
    carry_initial: int,
    carry_phi_initial: int,
) -> int:
    circuit = layout.circuit

    state = 0

    state = write_register(
        state,
        circuit,
        layout.a,
        a,
    )

    state = write_register(
        state,
        circuit,
        layout.b,
        b,
    )

    state = set_qubit(
        state,
        circuit,
        layout.carry_direct[0],
        carry_initial,
    )

    state = set_qubit(
        state,
        circuit,
        layout.carry_phi[0],
        carry_phi_initial,
    )

    return state


@dataclass(frozen=True)
class ObservedRippleState:
    a: int
    b: int

    a_phi: int
    b_phi: int

    sum_direct: int
    sum_phi: int

    carry_direct: tuple[int, ...]
    carry_phi: tuple[int, ...]


def decode_output(
    layout: CircuitLayout,
    state: int,
) -> ObservedRippleState:
    circuit = layout.circuit

    direct_carries = tuple(
        read_qubit(
            state,
            circuit,
            layout.carry_direct[index],
        )
        for index in range(WIDTH + 1)
    )

    phi_carries = tuple(
        read_qubit(
            state,
            circuit,
            layout.carry_phi[index],
        )
        for index in range(WIDTH + 1)
    )

    return ObservedRippleState(
        a=read_register(
            state,
            circuit,
            layout.a,
        ),
        b=read_register(
            state,
            circuit,
            layout.b,
        ),
        a_phi=read_register(
            state,
            circuit,
            layout.a_phi,
        ),
        b_phi=read_register(
            state,
            circuit,
            layout.b_phi,
        ),
        sum_direct=read_register(
            state,
            circuit,
            layout.sum_direct,
        ),
        sum_phi=read_register(
            state,
            circuit,
            layout.sum_phi,
        ),
        carry_direct=direct_carries,
        carry_phi=phi_carries,
    )


# ================================================================
# Exhaustive tests
# ================================================================

def test_exhaustive_dual_carry(
    layout: CircuitLayout,
) -> int:
    failures = 0
    tests = 0

    print("=== EXHAUSTIVE DUAL-CARRY RIPPLE TEST ===")
    print()

    for a in range(1 << WIDTH):
        for b in range(1 << WIDTH):
            for carry_initial in range(2):
                for carry_phi_initial in range(2):
                    tests += 1

                    input_state = prepare_input_basis(
                        layout,
                        a,
                        b,
                        carry_initial,
                        carry_phi_initial,
                    )

                    output_state = apply_basis_circuit(
                        layout.circuit,
                        input_state,
                    )

                    observed = decode_output(
                        layout,
                        output_state,
                    )

                    expected_a_phi = phi_p4_reference(a)
                    expected_b_phi = phi_p4_reference(b)

                    expected_sum, expected_carries = (
                        ripple_reference(
                            a,
                            b,
                            carry_initial,
                        )
                    )

                    expected_phi_sum, expected_phi_carries = (
                        ripple_reference(
                            expected_a_phi,
                            expected_b_phi,
                            carry_phi_initial,
                        )
                    )

                    passed = (
                        observed.a == a
                        and observed.b == b
                        and observed.a_phi == expected_a_phi
                        and observed.b_phi == expected_b_phi
                        and observed.sum_direct == expected_sum
                        and observed.sum_phi == expected_phi_sum
                        and observed.carry_direct
                        == tuple(expected_carries)
                        and observed.carry_phi
                        == tuple(expected_phi_carries)
                    )

                    if not passed:
                        failures += 1

                        if failures <= 20:
                            print(
                                "FAIL "
                                f"A={a:X} "
                                f"B={b:X} "
                                f"C0={carry_initial} "
                                f"Cφ0={carry_phi_initial}"
                            )
                            print(
                                "  observed:",
                                observed,
                            )
                            print(
                                "  expected direct:",
                                f"S={expected_sum:X}",
                                expected_carries,
                            )
                            print(
                                "  expected phi:",
                                f"Aφ={expected_a_phi:X}",
                                f"Bφ={expected_b_phi:X}",
                                f"Sφ={expected_phi_sum:X}",
                                expected_phi_carries,
                            )

    print(f"Configurations tested : {tests}")
    print(f"Ripple failures       : {failures}")

    return failures


def test_inverse_round_trip(
    layout: CircuitLayout,
) -> int:
    failures = 0
    tests = 0

    inverse = layout.circuit.inverse()

    print()
    print("=== EXHAUSTIVE INVERSE ROUND-TRIP TEST ===")
    print()

    for a in range(1 << WIDTH):
        for b in range(1 << WIDTH):
            for carry_initial in range(2):
                for carry_phi_initial in range(2):
                    tests += 1

                    original = prepare_input_basis(
                        layout,
                        a,
                        b,
                        carry_initial,
                        carry_phi_initial,
                    )

                    prepared = apply_basis_circuit(
                        layout.circuit,
                        original,
                    )

                    restored = apply_basis_circuit(
                        inverse,
                        prepared,
                    )

                    if restored != original:
                        failures += 1

                        if failures <= 20:
                            print(
                                "FAIL inverse "
                                f"A={a:X} "
                                f"B={b:X} "
                                f"C0={carry_initial} "
                                f"Cφ0={carry_phi_initial}"
                            )

    print(f"Round trips tested : {tests}")
    print(f"Round-trip failures: {failures}")

    return failures


def test_output_arithmetic(
    layout: CircuitLayout,
) -> int:
    failures = 0
    tests = 0

    print()
    print("=== ARITHMETIC IDENTITY TEST ===")
    print()

    for a in range(1 << WIDTH):
        for b in range(1 << WIDTH):
            for carry_initial in range(2):
                for carry_phi_initial in range(2):
                    tests += 1

                    input_state = prepare_input_basis(
                        layout,
                        a,
                        b,
                        carry_initial,
                        carry_phi_initial,
                    )

                    output_state = apply_basis_circuit(
                        layout.circuit,
                        input_state,
                    )

                    observed = decode_output(
                        layout,
                        output_state,
                    )

                    direct_total_observed = (
                        observed.sum_direct
                        | (
                            observed.carry_direct[-1]
                            << WIDTH
                        )
                    )

                    direct_total_expected = (
                        a + b + carry_initial
                    )

                    phi_total_observed = (
                        observed.sum_phi
                        | (
                            observed.carry_phi[-1]
                            << WIDTH
                        )
                    )

                    phi_total_expected = (
                        phi_p4_reference(a)
                        + phi_p4_reference(b)
                        + carry_phi_initial
                    )

                    if (
                        direct_total_observed
                        != direct_total_expected
                        or phi_total_observed
                        != phi_total_expected
                    ):
                        failures += 1

    print(f"Arithmetic cases tested : {tests}")
    print(f"Arithmetic failures     : {failures}")

    return failures


# ================================================================
# Superposition test
# ================================================================

def state_norm(
    amplitudes: dict[int, complex],
) -> float:
    return math.sqrt(
        sum(abs(amplitude) ** 2 for amplitude in amplitudes.values())
    )


def states_equal(
    observed: dict[int, complex],
    expected: dict[int, complex],
) -> bool:
    keys = set(observed) | set(expected)

    return all(
        abs(
            observed.get(key, 0j)
            - expected.get(key, 0j)
        )
        <= TOLERANCE
        for key in keys
    )


def test_sparse_superposition(
    layout: CircuitLayout,
) -> int:
    """
    Prepare the sparse coherent input:

        (
          |A=0000, B=0000, C0=0, Cφ0=0>
          +
          |A=1111, B=0001, C0=1, Cφ0=1>
        ) / sqrt(2)

    The full 34-qubit circuit acts linearly on both components.
    """

    print()
    print("=== FULL-RIPPLE SPARSE SUPERPOSITION TEST ===")
    print()

    first_input = prepare_input_basis(
        layout,
        a=0x0,
        b=0x0,
        carry_initial=0,
        carry_phi_initial=0,
    )

    second_input = prepare_input_basis(
        layout,
        a=0xF,
        b=0x1,
        carry_initial=1,
        carry_phi_initial=1,
    )

    amplitude = 1 / math.sqrt(2)

    input_state = {
        first_input: amplitude,
        second_input: amplitude,
    }

    observed = apply_sparse_state(
        layout.circuit,
        input_state,
    )

    first_output = apply_basis_circuit(
        layout.circuit,
        first_input,
    )

    second_output = apply_basis_circuit(
        layout.circuit,
        second_input,
    )

    expected = {
        first_output: amplitude,
        second_output: amplitude,
    }

    passed = states_equal(
        observed,
        expected,
    )

    norm = state_norm(observed)

    print("Input components : 2")
    print("Output components:", len(observed))
    print("State norm       :", f"{norm:.12f}")
    print("Linear mapping   :", passed)

    print()
    print("Observed output relation states:")

    for basis_index, output_amplitude in observed.items():
        decoded = decode_output(
            layout,
            basis_index,
        )

        print(
            f"  amplitude={output_amplitude} "
            f"A={decoded.a:X} "
            f"B={decoded.b:X} "
            f"Aφ={decoded.a_phi:X} "
            f"Bφ={decoded.b_phi:X} "
            f"S={decoded.sum_direct:X} "
            f"Cout={decoded.carry_direct[-1]} "
            f"Sφ={decoded.sum_phi:X} "
            f"Cφout={decoded.carry_phi[-1]}"
        )

    return 0 if (
        passed
        and math.isclose(
            norm,
            1.0,
            abs_tol=TOLERANCE,
        )
    ) else 1


# ================================================================
# Selected mapping display
# ================================================================

def display_selected_mappings(
    layout: CircuitLayout,
) -> None:
    examples = [
        (0x0, 0x0, 0, 0),
        (0x1, 0x1, 0, 0),
        (0x7, 0x1, 0, 0),
        (0xF, 0x1, 0, 0),
        (0xA, 0x5, 1, 0),
        (0xF, 0xF, 1, 1),
    ]

    print()
    print("=== SELECTED DUAL-CARRY MAPPINGS ===")
    print()
    print(
        "A B C0 Cφ0 | Aφ Bφ | S Cout | Sφ Cφout"
    )
    print(
        "-----------------------------------------"
    )

    for a, b, c0, cp0 in examples:
        input_state = prepare_input_basis(
            layout,
            a,
            b,
            c0,
            cp0,
        )

        output_state = apply_basis_circuit(
            layout.circuit,
            input_state,
        )

        observed = decode_output(
            layout,
            output_state,
        )

        print(
            f"{a:X} {b:X}  {c0}   {cp0}  | "
            f"{observed.a_phi:X}  "
            f"{observed.b_phi:X}  | "
            f"{observed.sum_direct:X}   "
            f"{observed.carry_direct[-1]}   | "
            f"{observed.sum_phi:X}    "
            f"{observed.carry_phi[-1]}"
        )


# ================================================================
# Main
# ================================================================

def main() -> int:
    layout = build_dual_carry_ripple()
    circuit = layout.circuit

    print("=== IFÁ QUANTUM DUAL-CARRY RIPPLE ===")
    print()

    print("Width        :", WIDTH)
    print("Qubits       :", circuit.num_qubits)
    print("Circuit depth:", circuit.depth())
    print("Gate count   :", circuit.count_ops())

    print()
    print("Register structure:")
    print("  A, B       : direct operands")
    print("  A_phi,B_phi: Φ-transformed operands")
    print("  S          : direct sum")
    print("  S_phi      : Φ-channel sum")
    print("  C[0..4]    : direct ripple propagation")
    print("  C_phi[0..4]: Φ ripple propagation")

    display_selected_mappings(layout)

    failures = 0

    failures += test_exhaustive_dual_carry(layout)
    failures += test_output_arithmetic(layout)
    failures += test_inverse_round_trip(layout)
    failures += test_sparse_superposition(layout)

    print()
    print("=== REVERSIBILITY STATEMENT ===")
    print()
    print(
        "The circuit is composed only of X, CNOT and Toffoli "
        "gates."
    )
    print(
        "Each component gate is unitary and reversible."
    )
    print(
        "The complete inverse circuit is obtained by reversing "
        "the gate order."
    )

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


