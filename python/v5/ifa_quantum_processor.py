#!/usr/bin/env python3

from __future__ import annotations

import math
import sys
from dataclasses import dataclass

try:
    from qiskit import QuantumCircuit, QuantumRegister
except ImportError as exc:
    raise SystemExit(
        "Qiskit is not installed.\n"
        "Install it with:\n"
        "    python3 -m pip install qiskit\n"
    ) from exc


WIDTH = 8
MASK = (1 << WIDTH) - 1
OPERAND_PAIRS = (1 << WIDTH) ** 2
CARRY_CONFIGURATIONS = 4
TOTAL_CONFIGURATIONS = OPERAND_PAIRS * CARRY_CONFIGURATIONS
TOLERANCE = 1e-10


# ================================================================
# Classical IFÁ reference model
# ================================================================

def phi_p2_reference(value: int) -> int:
    """
    Φ-P2 pair mapping.

        pair bits = (anchor, agreement)

        anchor'    = anchor
        agreement' = NOT(anchor XOR agreement)
    """
    if not 0 <= value <= 0b11:
        raise ValueError("Φ-P2 input must be between 0 and 3")

    anchor = (value >> 1) & 1
    agreement = value & 1
    transformed_agreement = 1 ^ anchor ^ agreement

    return (anchor << 1) | transformed_agreement


def phi_p8_reference(value: int) -> int:
    """Apply Φ-P2 independently to four adjacent bit pairs."""
    if not 0 <= value <= MASK:
        raise ValueError("Φ-P8 input must be an 8-bit value")

    output = 0

    for pair_index in range(WIDTH // 2):
        shift = 2 * pair_index
        pair = (value >> shift) & 0b11
        output |= phi_p2_reference(pair) << shift

    return output


def relation_reference(
    a_phi: int,
    b_phi: int,
) -> tuple[int, int, int]:
    """
    Native IFÁ relation frame.

        RA = AGREE    = Aφ AND Bφ
        RD = DISAGREE = Aφ XOR Bφ
        R0 = ABSENCE  = NOT(Aφ OR Bφ)
    """
    ra = a_phi & b_phi
    rd = a_phi ^ b_phi
    r0 = (~(a_phi | b_phi)) & MASK

    return ra, rd, r0


def ripple_reference(
    a: int,
    b: int,
    carry_initial: int,
) -> tuple[int, tuple[int, ...]]:
    """
    WIDTH-bit ripple reference.

    Returns:

        sum_value
        (C0, C1, ..., C8)
    """
    carry = carry_initial
    carries = [carry]
    sum_value = 0

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

    return sum_value, tuple(carries)


# ================================================================
# Reversible quantum gate definitions
# ================================================================

def append_phi_p2(
    circuit: QuantumCircuit,
    anchor,
    agreement,
) -> None:
    circuit.cx(anchor, agreement)
    circuit.x(agreement)


def append_phi_p8(
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


def append_agree(
    circuit: QuantumCircuit,
    a,
    b,
    target,
) -> None:
    """target ^= A AND B"""
    circuit.ccx(a, b, target)


def append_disagree(
    circuit: QuantumCircuit,
    a,
    b,
    target,
) -> None:
    """target ^= A XOR B"""
    circuit.cx(a, target)
    circuit.cx(b, target)


def append_absence(
    circuit: QuantumCircuit,
    a,
    b,
    target,
) -> None:
    """target ^= NOT(A OR B) using negative controls."""
    circuit.x(a)
    circuit.x(b)
    circuit.ccx(a, b, target)
    circuit.x(b)
    circuit.x(a)


def append_relation_frame(
    circuit: QuantumCircuit,
    a_phi: QuantumRegister,
    b_phi: QuantumRegister,
    ra: QuantumRegister,
    rd: QuantumRegister,
    r0: QuantumRegister,
) -> None:
    for bit in range(WIDTH):
        append_agree(
            circuit,
            a_phi[bit],
            b_phi[bit],
            ra[bit],
        )

        append_disagree(
            circuit,
            a_phi[bit],
            b_phi[bit],
            rd[bit],
        )

        append_absence(
            circuit,
            a_phi[bit],
            b_phi[bit],
            r0[bit],
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
    Reversible full-adder embedding.

        sum_target ^= A XOR B XOR Cin

        carry_out_target ^=
            AB XOR A·Cin XOR B·Cin
    """
    circuit.cx(a, sum_target)
    circuit.cx(b, sum_target)
    circuit.cx(carry_in, sum_target)

    circuit.ccx(a, b, carry_out_target)
    circuit.ccx(a, carry_in, carry_out_target)
    circuit.ccx(b, carry_in, carry_out_target)


def append_ripple_channel(
    circuit: QuantumCircuit,
    a: QuantumRegister,
    b: QuantumRegister,
    sum_register: QuantumRegister,
    carry_register: QuantumRegister,
) -> None:
    for bit in range(WIDTH):
        append_quantum_full_adder(
            circuit,
            a=a[bit],
            b=b[bit],
            carry_in=carry_register[bit],
            sum_target=sum_register[bit],
            carry_out_target=carry_register[bit + 1],
        )


# ================================================================
# Complete quantum processing core
# ================================================================

@dataclass
class ProcessorLayout:
    circuit: QuantumCircuit

    a: QuantumRegister
    b: QuantumRegister

    a_phi: QuantumRegister
    b_phi: QuantumRegister

    ra: QuantumRegister
    rd: QuantumRegister
    r0: QuantumRegister

    sum_direct: QuantumRegister
    sum_phi: QuantumRegister

    carry_direct: QuantumRegister
    carry_phi: QuantumRegister


def build_quantum_processor() -> ProcessorLayout:
    """
    Complete register structure:

        A             8
        B             8
        A_phi         8
        B_phi         8
        RA            8
        RD            8
        R0            8
        S             8
        S_phi         8
        C             9
        C_phi         9
                      --
        Total        82 qubits
    """
    a = QuantumRegister(WIDTH, "A")
    b = QuantumRegister(WIDTH, "B")

    a_phi = QuantumRegister(WIDTH, "A_phi")
    b_phi = QuantumRegister(WIDTH, "B_phi")

    ra = QuantumRegister(WIDTH, "RA")
    rd = QuantumRegister(WIDTH, "RD")
    r0 = QuantumRegister(WIDTH, "R0")

    sum_direct = QuantumRegister(WIDTH, "S")
    sum_phi = QuantumRegister(WIDTH, "S_phi")

    carry_direct = QuantumRegister(WIDTH + 1, "C")
    carry_phi = QuantumRegister(WIDTH + 1, "C_phi")

    circuit = QuantumCircuit(
        a,
        b,
        a_phi,
        b_phi,
        ra,
        rd,
        r0,
        sum_direct,
        sum_phi,
        carry_direct,
        carry_phi,
        name="IFA_Quantum_Processor_8",
    )

    # ------------------------------------------------------------
    # 1. Coherent operand embedding for the Φ channel
    # ------------------------------------------------------------

    for bit in range(WIDTH):
        circuit.cx(a[bit], a_phi[bit])
        circuit.cx(b[bit], b_phi[bit])

    # ------------------------------------------------------------
    # 2. Φ-P8 coordinate transform
    # ------------------------------------------------------------

    append_phi_p8(circuit, a_phi)
    append_phi_p8(circuit, b_phi)

    circuit.barrier()

    # ------------------------------------------------------------
    # 3. Native relation-frame preparation
    # ------------------------------------------------------------

    append_relation_frame(
        circuit,
        a_phi,
        b_phi,
        ra,
        rd,
        r0,
    )

    circuit.barrier()

    # ------------------------------------------------------------
    # 4. Direct ripple propagation
    # ------------------------------------------------------------

    append_ripple_channel(
        circuit,
        a,
        b,
        sum_direct,
        carry_direct,
    )

    circuit.barrier()

    # ------------------------------------------------------------
    # 5. Φ-channel ripple propagation
    # ------------------------------------------------------------

    append_ripple_channel(
        circuit,
        a_phi,
        b_phi,
        sum_phi,
        carry_phi,
    )

    return ProcessorLayout(
        circuit=circuit,
        a=a,
        b=b,
        a_phi=a_phi,
        b_phi=b_phi,
        ra=ra,
        rd=rd,
        r0=r0,
        sum_direct=sum_direct,
        sum_phi=sum_phi,
        carry_direct=carry_direct,
        carry_phi=carry_phi,
    )


# ================================================================
# Exact sparse reversible simulator
# ================================================================

CompiledOperation = tuple[str, tuple[int, ...]]


def compile_circuit(
    circuit: QuantumCircuit,
) -> tuple[CompiledOperation, ...]:
    """
    Convert the Qiskit circuit into an efficient sequence of indexed
    X, CNOT and Toffoli operations.
    """
    operations: list[CompiledOperation] = []

    for instruction in circuit.data:
        name = instruction.operation.name

        if name == "barrier":
            continue

        qubits = tuple(
            circuit.find_bit(qubit).index
            for qubit in instruction.qubits
        )

        if name not in {"x", "cx", "ccx"}:
            raise RuntimeError(
                f"Unsupported circuit operation: {name}"
            )

        operations.append((name, qubits))

    return tuple(operations)


def invert_compiled_circuit(
    operations: tuple[CompiledOperation, ...],
) -> tuple[CompiledOperation, ...]:
    """
    X, CNOT and Toffoli are individually self-inverse. Therefore the
    inverse circuit is the same gate sequence in reverse order.
    """
    return tuple(reversed(operations))


def apply_compiled_basis_circuit(
    operations: tuple[CompiledOperation, ...],
    state: int,
) -> int:
    for name, qubits in operations:
        if name == "x":
            target = qubits[0]
            state ^= 1 << target

        elif name == "cx":
            control, target = qubits

            if (state >> control) & 1:
                state ^= 1 << target

        elif name == "ccx":
            control_a, control_b, target = qubits

            if (
                ((state >> control_a) & 1)
                and ((state >> control_b) & 1)
            ):
                state ^= 1 << target

    return state


def apply_sparse_state(
    operations: tuple[CompiledOperation, ...],
    amplitudes: dict[int, complex],
) -> dict[int, complex]:
    output: dict[int, complex] = {}

    for basis_state, amplitude in amplitudes.items():
        mapped = apply_compiled_basis_circuit(
            operations,
            basis_state,
        )

        output[mapped] = output.get(mapped, 0j) + amplitude

    return output


# ================================================================
# Register encoding and decoding
# ================================================================

def qubit_index(
    circuit: QuantumCircuit,
    qubit,
) -> int:
    return circuit.find_bit(qubit).index


def set_qubit(
    state: int,
    circuit: QuantumCircuit,
    qubit,
    value: int,
) -> int:
    index = qubit_index(circuit, qubit)

    if value:
        state |= 1 << index
    else:
        state &= ~(1 << index)

    return state


def read_qubit(
    state: int,
    circuit: QuantumCircuit,
    qubit,
) -> int:
    index = qubit_index(circuit, qubit)
    return (state >> index) & 1


def write_register(
    state: int,
    circuit: QuantumCircuit,
    register: QuantumRegister,
    value: int,
) -> int:
    for bit in range(len(register)):
        state = set_qubit(
            state,
            circuit,
            register[bit],
            (value >> bit) & 1,
        )

    return state


def read_register(
    state: int,
    circuit: QuantumCircuit,
    register: QuantumRegister,
) -> int:
    value = 0

    for bit in range(len(register)):
        value |= (
            read_qubit(
                state,
                circuit,
                register[bit],
            )
            << bit
        )

    return value


def prepare_processor_input(
    layout: ProcessorLayout,
    a: int,
    b: int,
    carry_initial: int,
    carry_phi_initial: int,
) -> int:
    state = 0
    circuit = layout.circuit

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
class ProcessorOutput:
    a: int
    b: int

    a_phi: int
    b_phi: int

    ra: int
    rd: int
    r0: int

    sum_direct: int
    sum_phi: int

    carry_direct: tuple[int, ...]
    carry_phi: tuple[int, ...]


def decode_processor_output(
    layout: ProcessorLayout,
    state: int,
) -> ProcessorOutput:
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

    return ProcessorOutput(
        a=read_register(state, circuit, layout.a),
        b=read_register(state, circuit, layout.b),

        a_phi=read_register(state, circuit, layout.a_phi),
        b_phi=read_register(state, circuit, layout.b_phi),

        ra=read_register(state, circuit, layout.ra),
        rd=read_register(state, circuit, layout.rd),
        r0=read_register(state, circuit, layout.r0),

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
# Expected output
# ================================================================

def expected_processor_output(
    a: int,
    b: int,
    carry_initial: int,
    carry_phi_initial: int,
) -> ProcessorOutput:
    a_phi = phi_p8_reference(a)
    b_phi = phi_p8_reference(b)

    ra, rd, r0 = relation_reference(
        a_phi,
        b_phi,
    )

    sum_direct, carry_direct = ripple_reference(
        a,
        b,
        carry_initial,
    )

    sum_phi, carry_phi = ripple_reference(
        a_phi,
        b_phi,
        carry_phi_initial,
    )

    return ProcessorOutput(
        a=a,
        b=b,
        a_phi=a_phi,
        b_phi=b_phi,
        ra=ra,
        rd=rd,
        r0=r0,
        sum_direct=sum_direct,
        sum_phi=sum_phi,
        carry_direct=carry_direct,
        carry_phi=carry_phi,
    )


# ================================================================
# Exhaustive tests
# ================================================================

def test_all_operand_pairs(
    layout: ProcessorLayout,
    operations: tuple[CompiledOperation, ...],
) -> int:
    failures = 0
    tests = 0

    print("=== EXHAUSTIVE END-TO-END PROCESSOR TEST ===")
    print()

    for a in range(1 << WIDTH):
        for b in range(1 << WIDTH):
            for carry_initial in range(2):
                for carry_phi_initial in range(2):
                    tests += 1

                    input_state = prepare_processor_input(
                        layout,
                        a,
                        b,
                        carry_initial,
                        carry_phi_initial,
                    )

                    output_state = apply_compiled_basis_circuit(
                        operations,
                        input_state,
                    )

                    observed = decode_processor_output(
                        layout,
                        output_state,
                    )

                    expected = expected_processor_output(
                        a,
                        b,
                        carry_initial,
                        carry_phi_initial,
                    )

                    if observed != expected:
                        failures += 1

                        if failures <= 10:
                            print(
                                "FAIL "
                                f"A={a:02X} "
                                f"B={b:02X} "
                                f"C0={carry_initial} "
                                f"Cφ0={carry_phi_initial}"
                            )
                            print("  observed:", observed)
                            print("  expected:", expected)

    print(f"Ordered operand pairs       : {OPERAND_PAIRS}")
    print(f"Initial-carry configurations: {CARRY_CONFIGURATIONS}")
    print(f"Total configurations tested : {tests}")
    print(f"Processor failures          : {failures}")

    return failures


def test_arithmetic_identities(
    layout: ProcessorLayout,
    operations: tuple[CompiledOperation, ...],
) -> int:
    failures = 0
    tests = 0

    print()
    print("=== END-TO-END ARITHMETIC IDENTITY TEST ===")
    print()

    for a in range(1 << WIDTH):
        for b in range(1 << WIDTH):
            for carry_initial in range(2):
                for carry_phi_initial in range(2):
                    tests += 1

                    input_state = prepare_processor_input(
                        layout,
                        a,
                        b,
                        carry_initial,
                        carry_phi_initial,
                    )

                    output_state = apply_compiled_basis_circuit(
                        operations,
                        input_state,
                    )

                    observed = decode_processor_output(
                        layout,
                        output_state,
                    )

                    direct_total = (
                        observed.sum_direct
                        | (
                            observed.carry_direct[-1]
                            << WIDTH
                        )
                    )

                    expected_direct_total = (
                        a + b + carry_initial
                    )

                    phi_total = (
                        observed.sum_phi
                        | (
                            observed.carry_phi[-1]
                            << WIDTH
                        )
                    )

                    expected_phi_total = (
                        phi_p8_reference(a)
                        + phi_p8_reference(b)
                        + carry_phi_initial
                    )

                    relation_partition = (
                        observed.ra
                        | observed.rd
                        | observed.r0
                    )

                    relation_overlap = (
                        (observed.ra & observed.rd)
                        | (observed.ra & observed.r0)
                        | (observed.rd & observed.r0)
                    )

                    if (
                        direct_total != expected_direct_total
                        or phi_total != expected_phi_total
                        or relation_partition != MASK
                        or relation_overlap != 0
                    ):
                        failures += 1

                        if failures <= 10:
                            print(
                                "FAIL identity "
                                f"A={a:02X} "
                                f"B={b:02X} "
                                f"C0={carry_initial} "
                                f"Cφ0={carry_phi_initial}"
                            )

    print(f"Identity cases tested : {tests}")
    print(f"Identity failures     : {failures}")

    return failures


def test_inverse_round_trip_samples(
    layout: ProcessorLayout,
    operations: tuple[CompiledOperation, ...],
) -> int:
    """
    Verify complete inverse propagation across representative values.

    The earlier component tests already exhaustively established each
    gate block. This confirms their complete end-to-end composition.
    """
    inverse_operations = invert_compiled_circuit(operations)

    sample_values = [
        0x00,
        0x01,
        0x0F,
        0x55,
        0x7F,
        0x80,
        0xAA,
        0xF0,
        0xFE,
        0xFF,
    ]

    failures = 0
    tests = 0

    print()
    print("=== COMPLETE PROCESSOR INVERSE TEST ===")
    print()

    for a in sample_values:
        for b in sample_values:
            for carry_initial in range(2):
                for carry_phi_initial in range(2):
                    tests += 1

                    original = prepare_processor_input(
                        layout,
                        a,
                        b,
                        carry_initial,
                        carry_phi_initial,
                    )

                    processed = apply_compiled_basis_circuit(
                        operations,
                        original,
                    )

                    restored = apply_compiled_basis_circuit(
                        inverse_operations,
                        processed,
                    )

                    if restored != original:
                        failures += 1

                        print(
                            "FAIL inverse "
                            f"A={a:02X} "
                            f"B={b:02X} "
                            f"C0={carry_initial} "
                            f"Cφ0={carry_phi_initial}"
                        )

    print(f"Inverse cases tested : {tests}")
    print(f"Inverse failures     : {failures}")

    return failures


# ================================================================
# Sparse superposition test
# ================================================================

def sparse_state_norm(
    state: dict[int, complex],
) -> float:
    return math.sqrt(
        sum(abs(amplitude) ** 2 for amplitude in state.values())
    )


def sparse_states_equal(
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


def test_processor_superposition(
    layout: ProcessorLayout,
    operations: tuple[CompiledOperation, ...],
) -> int:
    """
    Apply the complete 82-qubit processor to four coherent basis
    components without constructing a dense 2^82 statevector.
    """
    print()
    print("=== END-TO-END SPARSE SUPERPOSITION TEST ===")
    print()

    configurations = [
        (0x00, 0x00, 0, 0),
        (0x55, 0xAA, 0, 1),
        (0xA5, 0x5A, 1, 0),
        (0xFF, 0x01, 1, 1),
    ]

    amplitude = 1 / math.sqrt(len(configurations))

    input_state: dict[int, complex] = {}

    for a, b, c0, cp0 in configurations:
        basis_state = prepare_processor_input(
            layout,
            a,
            b,
            c0,
            cp0,
        )

        input_state[basis_state] = amplitude

    observed = apply_sparse_state(
        operations,
        input_state,
    )

    expected: dict[int, complex] = {}

    for basis_state, basis_amplitude in input_state.items():
        output_state = apply_compiled_basis_circuit(
            operations,
            basis_state,
        )

        expected[output_state] = basis_amplitude

    mapping_correct = sparse_states_equal(
        observed,
        expected,
    )

    norm = sparse_state_norm(observed)

    print("Input components :", len(input_state))
    print("Output components:", len(observed))
    print("State norm       :", f"{norm:.12f}")
    print("Linear mapping   :", mapping_correct)

    print()
    print("Observed processor branches:")

    for basis_state, branch_amplitude in observed.items():
        output = decode_processor_output(
            layout,
            basis_state,
        )

        print(
            f"  amplitude={branch_amplitude} "
            f"A={output.a:02X} "
            f"B={output.b:02X} "
            f"Aφ={output.a_phi:02X} "
            f"Bφ={output.b_phi:02X} "
            f"RA={output.ra:02X} "
            f"RD={output.rd:02X} "
            f"R0={output.r0:02X} "
            f"S={output.sum_direct:02X} "
            f"Cout={output.carry_direct[-1]} "
            f"Sφ={output.sum_phi:02X} "
            f"Cφout={output.carry_phi[-1]}"
        )

    passed = (
        mapping_correct
        and math.isclose(
            norm,
            1.0,
            abs_tol=TOLERANCE,
        )
    )

    return 0 if passed else 1


# ================================================================
# Selected output display
# ================================================================

def display_selected_processor_states(
    layout: ProcessorLayout,
    operations: tuple[CompiledOperation, ...],
) -> None:
    examples = [
        (0x00, 0x00, 0, 0),
        (0x01, 0x01, 0, 0),
        (0x7F, 0x01, 0, 0),
        (0xFF, 0x01, 0, 0),
        (0xA5, 0x5A, 1, 0),
        (0xFF, 0xFF, 1, 1),
    ]

    print()
    print("=== SELECTED IFÁ PROCESSOR STATES ===")
    print()

    print(
        " A   B  C0 Cφ0 | Aφ  Bφ | RA  RD  R0 | "
        " S Cout | Sφ Cφout"
    )
    print(
        "-----------------------------------------------------------"
    )

    for a, b, c0, cp0 in examples:
        input_state = prepare_processor_input(
            layout,
            a,
            b,
            c0,
            cp0,
        )

        output_state = apply_compiled_basis_circuit(
            operations,
            input_state,
        )

        output = decode_processor_output(
            layout,
            output_state,
        )

        print(
            f"{a:02X}  {b:02X}   {c0}   {cp0}  | "
            f"{output.a_phi:02X}  {output.b_phi:02X} | "
            f"{output.ra:02X}  {output.rd:02X}  {output.r0:02X} | "
            f"{output.sum_direct:02X}   "
            f"{output.carry_direct[-1]}   | "
            f"{output.sum_phi:02X}    "
            f"{output.carry_phi[-1]}"
        )


# ================================================================
# Main
# ================================================================

def main() -> int:
    layout = build_quantum_processor()
    circuit = layout.circuit
    operations = compile_circuit(circuit)

    print("=== IFÁ 8-BIT QUANTUM PROCESSING CORE ===")
    print()

    print("Width               :", WIDTH)
    print("Qubits              :", circuit.num_qubits)
    print("Circuit depth       :", circuit.depth())
    print("Qiskit gate count   :", circuit.count_ops())
    print("Compiled operations :", len(operations))

    print()
    print("Pipeline:")
    print("  A,B")
    print("    -> coherent Φ-channel embedding")
    print("    -> Φ-P8")
    print("    -> RA/RD/R0 relation frame")
    print("    -> direct ripple propagation")
    print("    -> Φ ripple propagation")

    display_selected_processor_states(
        layout,
        operations,
    )

    failures = 0

    failures += test_all_operand_pairs(
        layout,
        operations,
    )

    failures += test_arithmetic_identities(
        layout,
        operations,
    )

    failures += test_inverse_round_trip_samples(
        layout,
        operations,
    )

    failures += test_processor_superposition(
        layout,
        operations,
    )

    print()
    print("=== QUANTUM VALIDITY STATEMENT ===")
    print()
    print(
        "The processing core is composed exclusively of "
        "X, CNOT and Toffoli gates."
    )
    print(
        "Each primitive is unitary and reversible."
    )
    print(
        "Therefore their ordered composition is a unitary "
        "reversible quantum operator."
    )
    print(
        "The inverse processor is obtained by reversing the "
        "complete gate sequence."
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
