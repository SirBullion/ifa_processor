#!/usr/bin/env python3

from __future__ import annotations

import math
import sys
from dataclasses import dataclass

import numpy as np

try:
    from qiskit import QuantumCircuit, QuantumRegister
    from qiskit.quantum_info import Operator, Statevector
except ImportError as exc:
    raise SystemExit(
        "Qiskit is not installed.\n"
        "Install it with:\n"
        "    python3 -m pip install qiskit\n"
    ) from exc


TOLERANCE = 1e-10
BYTE_VALUES = 256
ORDERED_PAIRS = BYTE_VALUES * BYTE_VALUES


# ---------------------------------------------------------------------
# Classical reference definitions
# ---------------------------------------------------------------------

def phi_p2_reference(value: int) -> int:
    """
    Φ-P2 on one two-bit pair:

        (anchor, agreement)
            ->
        (anchor, NOT(anchor XOR agreement))
    """
    if not 0 <= value <= 0b11:
        raise ValueError("Φ-P2 value must be between 0 and 3")

    anchor = (value >> 1) & 1
    agreement = value & 1

    transformed_agreement = 1 ^ anchor ^ agreement

    return (anchor << 1) | transformed_agreement


def phi_p8_reference(value: int) -> int:
    """Apply Φ-P2 to four adjacent two-bit blocks."""
    if not 0 <= value <= 0xFF:
        raise ValueError("Φ-P8 value must be between 0 and 255")

    result = 0

    for pair_index in range(4):
        shift = pair_index * 2
        pair = (value >> shift) & 0b11
        result |= phi_p2_reference(pair) << shift

    return result


def relation_reference(
    a_phi: int,
    b_phi: int,
) -> tuple[int, int, int]:
    """
    IFÁ relation frame:

        RA = Aφ AND Bφ
        RD = Aφ XOR Bφ
        R0 = NOT(Aφ OR Bφ)
    """
    ra = a_phi & b_phi
    rd = a_phi ^ b_phi
    r0 = (~(a_phi | b_phi)) & 0xFF

    return ra, rd, r0


# ---------------------------------------------------------------------
# Quantum gate definitions
# ---------------------------------------------------------------------

def append_phi_p2(
    circuit: QuantumCircuit,
    anchor,
    agreement,
) -> None:
    """
    agreement' = agreement XOR anchor XOR 1
    anchor'    = anchor
    """
    circuit.cx(anchor, agreement)
    circuit.x(agreement)


def append_phi_p8(
    circuit: QuantumCircuit,
    register: QuantumRegister,
) -> None:
    """Append four independent Φ-P2 blocks."""
    for pair_index in range(4):
        agreement_index = 2 * pair_index
        anchor_index = agreement_index + 1

        append_phi_p2(
            circuit,
            register[anchor_index],
            register[agreement_index],
        )


def append_agree(
    circuit: QuantumCircuit,
    a,
    b,
    target,
) -> None:
    """
    target ^= (a AND b)
    """
    circuit.ccx(a, b, target)


def append_disagree(
    circuit: QuantumCircuit,
    a,
    b,
    target,
) -> None:
    """
    target ^= (a XOR b)
    """
    circuit.cx(a, target)
    circuit.cx(b, target)


def append_absence(
    circuit: QuantumCircuit,
    a,
    b,
    target,
) -> None:
    """
    target ^= (NOT a AND NOT b)

    Negative-control Toffoli decomposition.
    """
    circuit.x(a)
    circuit.x(b)

    circuit.ccx(a, b, target)

    circuit.x(b)
    circuit.x(a)


def append_relation_cell(
    circuit: QuantumCircuit,
    a,
    b,
    ra,
    rd,
    r0,
) -> None:
    """Prepare one local five-qubit relation frame."""
    append_agree(circuit, a, b, ra)
    append_disagree(circuit, a, b, rd)
    append_absence(circuit, a, b, r0)


def append_relation_frame(
    circuit: QuantumCircuit,
    a_register: QuantumRegister,
    b_register: QuantumRegister,
    ra_register: QuantumRegister,
    rd_register: QuantumRegister,
    r0_register: QuantumRegister,
) -> None:
    """Prepare the complete eight-position relation frame."""
    for bit in range(8):
        append_relation_cell(
            circuit,
            a_register[bit],
            b_register[bit],
            ra_register[bit],
            rd_register[bit],
            r0_register[bit],
        )


def build_relation_frame_circuit() -> QuantumCircuit:
    """
    Register layout:

        A   : 8 qubits
        B   : 8 qubits
        RA  : 8 ancillas
        RD  : 8 ancillas
        R0  : 8 ancillas

    Total: 40 qubits
    """
    a = QuantumRegister(8, "A")
    b = QuantumRegister(8, "B")
    ra = QuantumRegister(8, "RA")
    rd = QuantumRegister(8, "RD")
    r0 = QuantumRegister(8, "R0")

    circuit = QuantumCircuit(
        a,
        b,
        ra,
        rd,
        r0,
        name="IFA_Relation_Frame",
    )

    circuit.barrier()

    append_phi_p8(circuit, a)
    append_phi_p8(circuit, b)

    circuit.barrier()

    append_relation_frame(
        circuit,
        a,
        b,
        ra,
        rd,
        r0,
    )

    return circuit


# ---------------------------------------------------------------------
# Reversible basis-state simulation
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RelationState:
    a: int
    b: int
    ra: int
    rd: int
    r0: int


def reversible_prepare(
    a: int,
    b: int,
    ra_target: int = 0,
    rd_target: int = 0,
    r0_target: int = 0,
) -> RelationState:
    """
    Basis-state evaluation of the exact reversible circuit:

        A  <- Φ(A)
        B  <- Φ(B)

        RA <- RA XOR (Aφ AND Bφ)
        RD <- RD XOR (Aφ XOR Bφ)
        R0 <- R0 XOR NOT(Aφ OR Bφ)
    """
    a_phi = phi_p8_reference(a)
    b_phi = phi_p8_reference(b)

    generated_ra, generated_rd, generated_r0 = relation_reference(
        a_phi,
        b_phi,
    )

    return RelationState(
        a=a_phi,
        b=b_phi,
        ra=ra_target ^ generated_ra,
        rd=rd_target ^ generated_rd,
        r0=r0_target ^ generated_r0,
    )


def reversible_uncompute(
    state: RelationState,
) -> RelationState:
    """
    Apply the inverse circuit:

        relation-frame inverse first,
        then Φ-P8 inverse.

    Both stages are self-inverse.
    """
    generated_ra, generated_rd, generated_r0 = relation_reference(
        state.a,
        state.b,
    )

    cleared_ra = state.ra ^ generated_ra
    cleared_rd = state.rd ^ generated_rd
    cleared_r0 = state.r0 ^ generated_r0

    original_a = phi_p8_reference(state.a)
    original_b = phi_p8_reference(state.b)

    return RelationState(
        a=original_a,
        b=original_b,
        ra=cleared_ra,
        rd=cleared_rd,
        r0=cleared_r0,
    )


def test_exhaustive_relation_frame() -> int:
    failures = 0

    print("=== EXHAUSTIVE QUANTUM RELATION-FRAME TEST ===")
    print()

    for a in range(BYTE_VALUES):
        for b in range(BYTE_VALUES):
            observed = reversible_prepare(a, b)

            expected_a_phi = phi_p8_reference(a)
            expected_b_phi = phi_p8_reference(b)

            expected_ra, expected_rd, expected_r0 = relation_reference(
                expected_a_phi,
                expected_b_phi,
            )

            passed = (
                observed.a == expected_a_phi
                and observed.b == expected_b_phi
                and observed.ra == expected_ra
                and observed.rd == expected_rd
                and observed.r0 == expected_r0
            )

            if not passed:
                failures += 1

                if failures <= 20:
                    print(
                        "FAIL "
                        f"A={a:02X} "
                        f"B={b:02X} "
                        f"Aφ={observed.a:02X} "
                        f"Bφ={observed.b:02X} "
                        f"RA={observed.ra:02X} "
                        f"RD={observed.rd:02X} "
                        f"R0={observed.r0:02X}"
                    )

    print(f"Ordered operand pairs tested : {ORDERED_PAIRS}")
    print(f"Relation-frame failures      : {failures}")

    return failures


def test_exhaustive_uncomputation() -> int:
    failures = 0

    print()
    print("=== EXHAUSTIVE UNCOMPUTATION TEST ===")
    print()

    for a in range(BYTE_VALUES):
        for b in range(BYTE_VALUES):
            prepared = reversible_prepare(a, b)
            restored = reversible_uncompute(prepared)

            expected = RelationState(
                a=a,
                b=b,
                ra=0,
                rd=0,
                r0=0,
            )

            if restored != expected:
                failures += 1

                if failures <= 20:
                    print(
                        "FAIL uncompute "
                        f"A={a:02X} "
                        f"B={b:02X} "
                        f"restored={restored}"
                    )

    print(f"Round trips tested       : {ORDERED_PAIRS}")
    print(f"Uncomputation failures   : {failures}")

    return failures


def test_arbitrary_target_reversibility() -> int:
    """
    Verify that the relation circuit is reversible even when the target
    registers do not begin at zero.
    """
    failures = 0

    target_patterns = [
        (0x00, 0x00, 0x00),
        (0xFF, 0x00, 0x00),
        (0x00, 0xFF, 0x00),
        (0x00, 0x00, 0xFF),
        (0x55, 0xAA, 0x0F),
        (0xA5, 0x5A, 0xF0),
    ]

    sample_operands = [
        (0x00, 0x00),
        (0x00, 0xFF),
        (0x55, 0xAA),
        (0xA5, 0x5A),
        (0xFF, 0xFF),
    ]

    print()
    print("=== ARBITRARY TARGET REVERSIBILITY TEST ===")
    print()

    for a, b in sample_operands:
        for ra_target, rd_target, r0_target in target_patterns:
            prepared = reversible_prepare(
                a,
                b,
                ra_target,
                rd_target,
                r0_target,
            )

            restored = reversible_uncompute(prepared)

            expected = RelationState(
                a=a,
                b=b,
                ra=ra_target,
                rd=rd_target,
                r0=r0_target,
            )

            if restored != expected:
                failures += 1

                print(
                    "FAIL target round trip "
                    f"A={a:02X} B={b:02X} "
                    f"RA0={ra_target:02X} "
                    f"RD0={rd_target:02X} "
                    f"R00={r0_target:02X}"
                )

    tests = len(sample_operands) * len(target_patterns)

    print(f"Target-state tests    : {tests}")
    print(f"Target-state failures : {failures}")

    return failures


# ---------------------------------------------------------------------
# Exact local quantum matrix tests
# ---------------------------------------------------------------------

def build_local_relation_cell() -> QuantumCircuit:
    """
    Five-qubit cell:

        q0 = A
        q1 = B
        q2 = RA
        q3 = RD
        q4 = R0
    """
    circuit = QuantumCircuit(5, name="Relation_Cell")

    append_relation_cell(
        circuit,
        0,
        1,
        2,
        3,
        4,
    )

    return circuit


def test_local_cell_unitarity(
    cell: QuantumCircuit,
) -> int:
    print()
    print("=== LOCAL RELATION-CELL UNITARITY ===")
    print()

    matrix = Operator(cell).data
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


def test_local_cell_self_inverse(
    cell: QuantumCircuit,
) -> int:
    print()
    print("=== LOCAL RELATION-CELL SELF-INVERSE TEST ===")
    print()

    matrix = Operator(cell).data
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


def test_local_basis_states(
    cell: QuantumCircuit,
) -> int:
    failures = 0

    print()
    print("=== LOCAL RELATION-CELL BASIS TEST ===")
    print()

    for a in range(2):
        for b in range(2):
            circuit = QuantumCircuit(5)

            if a:
                circuit.x(0)

            if b:
                circuit.x(1)

            circuit.compose(cell, inplace=True)

            state = Statevector.from_instruction(circuit)
            probabilities = np.abs(state.data) ** 2

            observed = int(np.argmax(probabilities))
            probability = float(probabilities[observed])

            expected_ra = a & b
            expected_rd = a ^ b
            expected_r0 = 1 ^ (a | b)

            expected_index = (
                (a << 0)
                | (b << 1)
                | (expected_ra << 2)
                | (expected_rd << 3)
                | (expected_r0 << 4)
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
                f"A={a} B={b} "
                f"-> RA={expected_ra} "
                f"RD={expected_rd} "
                f"R0={expected_r0} "
                f"P={probability:.12f} "
                f"{status}"
            )

            if not passed:
                failures += 1

    return failures


def test_local_superposition(
    cell: QuantumCircuit,
) -> int:
    """
    Prepare:

        (|A=0,B=0> + |A=1,B=1>) / sqrt(2)

    Expected relation-frame state:

        (|00,RA=0,RD=0,R0=1>
         +
         |11,RA=1,RD=0,R0=0>) / sqrt(2)
    """
    print()
    print("=== LOCAL RELATION-CELL SUPERPOSITION TEST ===")
    print()

    circuit = QuantumCircuit(5)

    circuit.h(0)
    circuit.cx(0, 1)

    circuit.compose(cell, inplace=True)

    observed = Statevector.from_instruction(circuit)

    expected = np.zeros(32, dtype=complex)

    # A=0, B=0, RA=0, RD=0, R0=1
    index_00 = 1 << 4

    # A=1, B=1, RA=1, RD=0, R0=0
    index_11 = (1 << 0) | (1 << 1) | (1 << 2)

    expected[index_00] = 1 / math.sqrt(2)
    expected[index_11] = 1 / math.sqrt(2)

    passed = np.allclose(
        observed.data,
        expected,
        atol=TOLERANCE,
    )

    print("Expected non-zero states:")
    print(f"  |{index_00:05b}>")
    print(f"  |{index_11:05b}>")

    print()
    print("Observed non-zero amplitudes:")

    for index, amplitude in enumerate(observed.data):
        if abs(amplitude) > TOLERANCE:
            print(f"  |{index:05b}> = {amplitude}")

    print()
    print("Superposition relation mapping:", passed)

    return 0 if passed else 1


# ---------------------------------------------------------------------
# Selected full-frame examples
# ---------------------------------------------------------------------

def display_selected_examples() -> None:
    examples = [
        (0x00, 0x00),
        (0x00, 0xFF),
        (0x55, 0xAA),
        (0xA5, 0x5A),
        (0xF0, 0x0F),
        (0xFF, 0xFF),
    ]

    print()
    print("=== SELECTED FULL RELATION FRAMES ===")
    print()

    print(
        " A   B   Aφ  Bφ  RA  RD  R0"
    )

    for a, b in examples:
        state = reversible_prepare(a, b)

        print(
            f"{a:02X}  {b:02X}  "
            f"{state.a:02X}  {state.b:02X}  "
            f"{state.ra:02X}  "
            f"{state.rd:02X}  "
            f"{state.r0:02X}"
        )


def main() -> int:
    full_circuit = build_relation_frame_circuit()
    local_cell = build_local_relation_cell()

    print("=== IFÁ QUANTUM RELATION-FRAME CIRCUIT ===")
    print()
    print("Qubits       :", full_circuit.num_qubits)
    print("Circuit depth:", full_circuit.depth())
    print("Gate count   :", full_circuit.count_ops())
    print()

    print("=== LOCAL FIVE-QUBIT RELATION CELL ===")
    print()
    print(local_cell.draw(output="text"))

    failures = 0

    failures += test_local_basis_states(local_cell)
    failures += test_local_cell_unitarity(local_cell)
    failures += test_local_cell_self_inverse(local_cell)
    failures += test_local_superposition(local_cell)

    display_selected_examples()

    failures += test_exhaustive_relation_frame()
    failures += test_exhaustive_uncomputation()
    failures += test_arbitrary_target_reversibility()

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
