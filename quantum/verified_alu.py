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
TOLERANCE = 1e-10

OP_PAPO = 0b000
OP_YO = 0b001
OP_SEDA = 0b010
OP_JU = 0b011
OP_KERE = 0b100

VALID_OPERATIONS = {
    OP_PAPO: "PAPO",
    OP_YO: "YO",
    OP_SEDA: "SEDA",
    OP_JU: "JU",
    OP_KERE: "KERE",
}


# ================================================================
# Classical reference model
# ================================================================

def operation_reference(
    opcode: int,
    a: int,
    b: int,
) -> int:
    if opcode == OP_PAPO:
        return (a + b) & MASK

    if opcode == OP_YO:
        return (a - b) & MASK

    if opcode == OP_SEDA:
        return int(a == b)

    if opcode == OP_JU:
        return int(a > b)

    if opcode == OP_KERE:
        return int(a < b)

    return 0


def ripple_reference(
    a: int,
    b: int,
    carry_initial: int,
) -> tuple[int, tuple[int, ...]]:
    carry = carry_initial
    carries = [carry]
    result = 0

    for bit in range(WIDTH):
        a_bit = (a >> bit) & 1
        b_bit = (b >> bit) & 1

        sum_bit = a_bit ^ b_bit ^ carry

        carry_next = (
            (a_bit & b_bit)
            | (a_bit & carry)
            | (b_bit & carry)
        )

        result |= sum_bit << bit
        carries.append(carry_next)
        carry = carry_next

    return result, tuple(carries)


# ================================================================
# Reversible arithmetic primitives
# ================================================================

def append_full_adder(
    circuit: QuantumCircuit,
    a,
    b,
    carry_in,
    sum_target,
    carry_out,
) -> None:
    """
    Reversible full-adder embedding:

        SUM ^= A XOR B XOR Cin

        Cout ^=
            AB XOR A·Cin XOR B·Cin
    """

    circuit.cx(a, sum_target)
    circuit.cx(b, sum_target)
    circuit.cx(carry_in, sum_target)

    circuit.ccx(a, b, carry_out)
    circuit.ccx(a, carry_in, carry_out)
    circuit.ccx(b, carry_in, carry_out)


def append_ripple(
    circuit: QuantumCircuit,
    a_register: QuantumRegister,
    b_register: QuantumRegister,
    sum_register: QuantumRegister,
    carry_register: QuantumRegister,
) -> None:
    for bit in range(WIDTH):
        append_full_adder(
            circuit,
            a=a_register[bit],
            b=b_register[bit],
            carry_in=carry_register[bit],
            sum_target=sum_register[bit],
            carry_out=carry_register[bit + 1],
        )


def append_equality_flag(
    circuit: QuantumCircuit,
    difference: QuantumRegister,
    equality_target,
) -> None:
    """
    equality_target ^= 1 when all difference bits are zero.
    """

    for bit in range(WIDTH):
        circuit.x(difference[bit])

    circuit.mcx(
        [difference[bit] for bit in range(WIDTH)],
        equality_target,
    )

    for bit in reversed(range(WIDTH)):
        circuit.x(difference[bit])


def append_greater_flag(
    circuit: QuantumCircuit,
    subtraction_carry_out,
    equality_flag,
    greater_target,
) -> None:
    """
    For unsigned subtraction A + NOT(B) + 1:

        subtraction carry-out = 1 exactly when A >= B

    Therefore:

        A > B = carry-out AND NOT(equal)
    """

    circuit.x(equality_flag)

    circuit.ccx(
        subtraction_carry_out,
        equality_flag,
        greater_target,
    )

    circuit.x(equality_flag)


def append_less_flag(
    circuit: QuantumCircuit,
    subtraction_carry_out,
    less_target,
) -> None:
    """
    A < B exactly when subtraction carry-out is zero.
    """

    circuit.x(subtraction_carry_out)
    circuit.cx(subtraction_carry_out, less_target)
    circuit.x(subtraction_carry_out)


# ================================================================
# Reversible opcode selector
# ================================================================

def prepare_opcode_controls(
    circuit: QuantumCircuit,
    opcode: QuantumRegister,
    opcode_value: int,
) -> None:
    for bit in range(len(opcode)):
        required_value = (opcode_value >> bit) & 1

        if required_value == 0:
            circuit.x(opcode[bit])


def restore_opcode_controls(
    circuit: QuantumCircuit,
    opcode: QuantumRegister,
    opcode_value: int,
) -> None:
    for bit in reversed(range(len(opcode))):
        required_value = (opcode_value >> bit) & 1

        if required_value == 0:
            circuit.x(opcode[bit])


def append_selected_byte(
    circuit: QuantumCircuit,
    opcode: QuantumRegister,
    opcode_value: int,
    source: QuantumRegister,
    output: QuantumRegister,
) -> None:
    """
    OUT ^= source when OP == opcode_value.
    """

    prepare_opcode_controls(
        circuit,
        opcode,
        opcode_value,
    )

    opcode_controls = [
        opcode[0],
        opcode[1],
        opcode[2],
    ]

    for bit in range(WIDTH):
        circuit.mcx(
            opcode_controls + [source[bit]],
            output[bit],
        )

    restore_opcode_controls(
        circuit,
        opcode,
        opcode_value,
    )


def append_selected_flag(
    circuit: QuantumCircuit,
    opcode: QuantumRegister,
    opcode_value: int,
    flag,
    output_bit,
) -> None:
    """
    OUT[0] ^= flag when OP == opcode_value.
    """

    prepare_opcode_controls(
        circuit,
        opcode,
        opcode_value,
    )

    circuit.mcx(
        [
            opcode[0],
            opcode[1],
            opcode[2],
            flag,
        ],
        output_bit,
    )

    restore_opcode_controls(
        circuit,
        opcode,
        opcode_value,
    )


# ================================================================
# Integrated IFÁ quantum ALU
# ================================================================

@dataclass
class ALULayout:
    circuit: QuantumCircuit

    a: QuantumRegister
    b: QuantumRegister
    b_not: QuantumRegister

    papo: QuantumRegister
    yo: QuantumRegister
    difference: QuantumRegister

    papo_carry: QuantumRegister
    yo_carry: QuantumRegister

    seda: QuantumRegister
    ju: QuantumRegister
    kere: QuantumRegister

    opcode: QuantumRegister
    output: QuantumRegister


def build_integrated_ifa_alu() -> ALULayout:
    """
    Register allocation:

        A             8
        B             8
        B_NOT         8

        PAPO          8
        YO            8
        DIFFERENCE    8

        PAPO_C        9
        YO_C          9

        SEDA          1
        JU            1
        KERE          1

        OP            3
        OUT           8
                     --
        Total        80 qubits
    """

    a = QuantumRegister(WIDTH, "A")
    b = QuantumRegister(WIDTH, "B")
    b_not = QuantumRegister(WIDTH, "B_NOT")

    papo = QuantumRegister(WIDTH, "PAPO")
    yo = QuantumRegister(WIDTH, "YO")
    difference = QuantumRegister(WIDTH, "DIFF")

    papo_carry = QuantumRegister(WIDTH + 1, "PAPO_C")
    yo_carry = QuantumRegister(WIDTH + 1, "YO_C")

    seda = QuantumRegister(1, "SEDA")
    ju = QuantumRegister(1, "JU")
    kere = QuantumRegister(1, "KERE")

    opcode = QuantumRegister(3, "OP")
    output = QuantumRegister(WIDTH, "OUT")

    circuit = QuantumCircuit(
        a,
        b,
        b_not,
        papo,
        yo,
        difference,
        papo_carry,
        yo_carry,
        seda,
        ju,
        kere,
        opcode,
        output,
        name="IFA_Quantum_ALU_8",
    )

    # ------------------------------------------------------------
    # PAPO candidate: A + B
    # ------------------------------------------------------------

    append_ripple(
        circuit,
        a_register=a,
        b_register=b,
        sum_register=papo,
        carry_register=papo_carry,
    )

    circuit.barrier()

    # ------------------------------------------------------------
    # YO candidate: A + NOT(B) + 1
    # ------------------------------------------------------------

    for bit in range(WIDTH):
        circuit.cx(b[bit], b_not[bit])
        circuit.x(b_not[bit])

    # Two's-complement +1.
    circuit.x(yo_carry[0])

    append_ripple(
        circuit,
        a_register=a,
        b_register=b_not,
        sum_register=yo,
        carry_register=yo_carry,
    )

    circuit.barrier()

    # ------------------------------------------------------------
    # Comparison relation preparation
    # ------------------------------------------------------------

    # DIFF = A XOR B
    for bit in range(WIDTH):
        circuit.cx(a[bit], difference[bit])
        circuit.cx(b[bit], difference[bit])

    append_equality_flag(
        circuit,
        difference=difference,
        equality_target=seda[0],
    )

    append_greater_flag(
        circuit,
        subtraction_carry_out=yo_carry[WIDTH],
        equality_flag=seda[0],
        greater_target=ju[0],
    )

    append_less_flag(
        circuit,
        subtraction_carry_out=yo_carry[WIDTH],
        less_target=kere[0],
    )

    circuit.barrier()

    # ------------------------------------------------------------
    # Native-operation selector
    # ------------------------------------------------------------

    append_selected_byte(
        circuit,
        opcode,
        OP_PAPO,
        papo,
        output,
    )

    append_selected_byte(
        circuit,
        opcode,
        OP_YO,
        yo,
        output,
    )

    append_selected_flag(
        circuit,
        opcode,
        OP_SEDA,
        seda[0],
        output[0],
    )

    append_selected_flag(
        circuit,
        opcode,
        OP_JU,
        ju[0],
        output[0],
    )

    append_selected_flag(
        circuit,
        opcode,
        OP_KERE,
        kere[0],
        output[0],
    )

    return ALULayout(
        circuit=circuit,
        a=a,
        b=b,
        b_not=b_not,
        papo=papo,
        yo=yo,
        difference=difference,
        papo_carry=papo_carry,
        yo_carry=yo_carry,
        seda=seda,
        ju=ju,
        kere=kere,
        opcode=opcode,
        output=output,
    )


# ================================================================
# Exact sparse simulator
# ================================================================

@dataclass(frozen=True)
class CompiledGate:
    controls: tuple[int, ...]
    target: int


def compile_circuit(
    circuit: QuantumCircuit,
) -> tuple[CompiledGate, ...]:
    """
    Compile X and arbitrary controlled-X gates.

    A gate with no controls is ordinary X.
    """

    compiled: list[CompiledGate] = []

    for instruction in circuit.data:
        operation = instruction.operation
        name = operation.name

        if name == "barrier":
            continue

        qubits = tuple(
            circuit.find_bit(qubit).index
            for qubit in instruction.qubits
        )

        if name == "x":
            compiled.append(
                CompiledGate(
                    controls=(),
                    target=qubits[0],
                )
            )
            continue

        if name == "cx":
            compiled.append(
                CompiledGate(
                    controls=(qubits[0],),
                    target=qubits[1],
                )
            )
            continue

        if name == "ccx":
            compiled.append(
                CompiledGate(
                    controls=qubits[:-1],
                    target=qubits[-1],
                )
            )
            continue

        if (
            name.startswith("mcx")
            or (
                name.startswith("c")
                and name.endswith("x")
            )
        ):
            compiled.append(
                CompiledGate(
                    controls=qubits[:-1],
                    target=qubits[-1],
                )
            )
            continue

        raise RuntimeError(
            f"Unsupported operation: {name}"
        )

    return tuple(compiled)


def inverse_compiled_circuit(
    operations: tuple[CompiledGate, ...],
) -> tuple[CompiledGate, ...]:
    return tuple(reversed(operations))


def apply_basis_circuit(
    operations: tuple[CompiledGate, ...],
    state: int,
) -> int:
    for operation in operations:
        controls_active = all(
            (state >> control) & 1
            for control in operation.controls
        )

        if controls_active:
            state ^= 1 << operation.target

    return state


def apply_sparse_state(
    operations: tuple[CompiledGate, ...],
    amplitudes: dict[int, complex],
) -> dict[int, complex]:
    output: dict[int, complex] = {}

    for basis_state, amplitude in amplitudes.items():
        mapped = apply_basis_circuit(
            operations,
            basis_state,
        )

        output[mapped] = (
            output.get(mapped, 0j)
            + amplitude
        )

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


def prepare_alu_input(
    layout: ALULayout,
    opcode: int,
    a: int,
    b: int,
    output_initial: int = 0,
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

    state = write_register(
        state,
        circuit,
        layout.opcode,
        opcode,
    )

    state = write_register(
        state,
        circuit,
        layout.output,
        output_initial,
    )

    return state


@dataclass(frozen=True)
class ALUOutput:
    a: int
    b: int
    b_not: int

    papo: int
    yo: int
    difference: int

    papo_carries: tuple[int, ...]
    yo_carries: tuple[int, ...]

    seda: int
    ju: int
    kere: int

    opcode: int
    output: int


def decode_alu_output(
    layout: ALULayout,
    state: int,
) -> ALUOutput:
    circuit = layout.circuit

    papo_carries = tuple(
        read_qubit(
            state,
            circuit,
            layout.papo_carry[index],
        )
        for index in range(WIDTH + 1)
    )

    yo_carries = tuple(
        read_qubit(
            state,
            circuit,
            layout.yo_carry[index],
        )
        for index in range(WIDTH + 1)
    )

    return ALUOutput(
        a=read_register(state, circuit, layout.a),
        b=read_register(state, circuit, layout.b),

        b_not=read_register(
            state,
            circuit,
            layout.b_not,
        ),

        papo=read_register(
            state,
            circuit,
            layout.papo,
        ),

        yo=read_register(
            state,
            circuit,
            layout.yo,
        ),

        difference=read_register(
            state,
            circuit,
            layout.difference,
        ),

        papo_carries=papo_carries,
        yo_carries=yo_carries,

        seda=read_register(
            state,
            circuit,
            layout.seda,
        ),

        ju=read_register(
            state,
            circuit,
            layout.ju,
        ),

        kere=read_register(
            state,
            circuit,
            layout.kere,
        ),

        opcode=read_register(
            state,
            circuit,
            layout.opcode,
        ),

        output=read_register(
            state,
            circuit,
            layout.output,
        ),
    )


# ================================================================
# Expected candidate state
# ================================================================

def expected_alu_output(
    opcode: int,
    a: int,
    b: int,
    output_initial: int = 0,
) -> ALUOutput:
    papo, papo_carries = ripple_reference(
        a,
        b,
        0,
    )

    b_not = (~b) & MASK

    yo, yo_carries = ripple_reference(
        a,
        b_not,
        1,
    )

    difference = a ^ b

    seda = int(a == b)
    ju = int(a > b)
    kere = int(a < b)

    selected = operation_reference(
        opcode,
        a,
        b,
    )

    return ALUOutput(
        a=a,
        b=b,
        b_not=b_not,
        papo=papo,
        yo=yo,
        difference=difference,
        papo_carries=papo_carries,
        yo_carries=yo_carries,
        seda=seda,
        ju=ju,
        kere=kere,
        opcode=opcode,
        output=output_initial ^ selected,
    )


# ================================================================
# Exhaustive tests
# ================================================================

def test_exhaustive_native_operations(
    layout: ALULayout,
    operations: tuple[CompiledGate, ...],
) -> int:
    failures = 0
    tests = 0

    print("=== EXHAUSTIVE INTEGRATED IFÁ ALU TEST ===")
    print()

    for opcode in VALID_OPERATIONS:
        for a in range(256):
            for b in range(256):
                tests += 1

                original = prepare_alu_input(
                    layout,
                    opcode,
                    a,
                    b,
                )

                processed = apply_basis_circuit(
                    operations,
                    original,
                )

                observed = decode_alu_output(
                    layout,
                    processed,
                )

                expected = expected_alu_output(
                    opcode,
                    a,
                    b,
                )

                if observed != expected:
                    failures += 1

                    if failures <= 20:
                        print(
                            "FAIL "
                            f"OP={VALID_OPERATIONS[opcode]} "
                            f"A={a:02X} "
                            f"B={b:02X}"
                        )
                        print("  observed:", observed)
                        print("  expected:", expected)

    print(f"Native operations            : {len(VALID_OPERATIONS)}")
    print("Ordered pairs per operation  : 65536")
    print(f"Total integrated cases       : {tests}")
    print(f"Integrated ALU failures      : {failures}")

    return failures


def test_candidate_generators(
    layout: ALULayout,
    operations: tuple[CompiledGate, ...],
) -> int:
    """
    Test the actual arithmetic and comparison generators independently
    of which result the opcode selector chooses.
    """

    failures = 0
    tests = 0

    print()
    print("=== EXHAUSTIVE CANDIDATE-GENERATOR TEST ===")
    print()

    for a in range(256):
        for b in range(256):
            tests += 1

            original = prepare_alu_input(
                layout,
                OP_PAPO,
                a,
                b,
            )

            processed = apply_basis_circuit(
                operations,
                original,
            )

            observed = decode_alu_output(
                layout,
                processed,
            )

            papo_total = (
                observed.papo
                | (
                    observed.papo_carries[-1]
                    << WIDTH
                )
            )

            expected_papo_total = a + b

            expected_yo = (a - b) & MASK

            passed = (
                papo_total == expected_papo_total
                and observed.yo == expected_yo
                and observed.seda == int(a == b)
                and observed.ju == int(a > b)
                and observed.kere == int(a < b)
                and (
                    observed.seda
                    + observed.ju
                    + observed.kere
                ) == 1
            )

            if not passed:
                failures += 1

                if failures <= 20:
                    print(
                        "FAIL candidate "
                        f"A={a:02X} "
                        f"B={b:02X} "
                        f"PAPO={observed.papo:02X} "
                        f"YO={observed.yo:02X} "
                        f"SEDA={observed.seda} "
                        f"JU={observed.ju} "
                        f"KERE={observed.kere}"
                    )

    print(f"Operand pairs tested     : {tests}")
    print(f"Candidate failures       : {failures}")

    return failures


def test_reserved_opcodes(
    layout: ALULayout,
    operations: tuple[CompiledGate, ...],
) -> int:
    failures = 0
    tests = 0

    print()
    print("=== RESERVED OPCODE TEST ===")
    print()

    samples = (
        (0x00, 0x00),
        (0x01, 0xFF),
        (0x55, 0xAA),
        (0xA5, 0x5A),
        (0xFF, 0xFF),
    )

    for opcode in (0b101, 0b110, 0b111):
        for a, b in samples:
            tests += 1

            original = prepare_alu_input(
                layout,
                opcode,
                a,
                b,
            )

            processed = apply_basis_circuit(
                operations,
                original,
            )

            observed = decode_alu_output(
                layout,
                processed,
            )

            if observed.output != 0:
                failures += 1

                print(
                    "FAIL reserved "
                    f"OP={opcode:03b} "
                    f"A={a:02X} "
                    f"B={b:02X} "
                    f"OUT={observed.output:02X}"
                )

    print(f"Reserved cases tested : {tests}")
    print(f"Reserved failures     : {failures}")

    return failures


def test_arbitrary_output_target(
    layout: ALULayout,
    operations: tuple[CompiledGate, ...],
) -> int:
    failures = 0
    tests = 0

    operands = (
        (0x00, 0x00),
        (0x01, 0xFF),
        (0x55, 0xAA),
        (0xA5, 0x5A),
        (0xFF, 0x01),
    )

    targets = (
        0x00,
        0x01,
        0x55,
        0xAA,
        0xFF,
    )

    print()
    print("=== ARBITRARY OUTPUT-TARGET TEST ===")
    print()

    for opcode in VALID_OPERATIONS:
        for a, b in operands:
            for output_initial in targets:
                tests += 1

                original = prepare_alu_input(
                    layout,
                    opcode,
                    a,
                    b,
                    output_initial,
                )

                processed = apply_basis_circuit(
                    operations,
                    original,
                )

                observed = decode_alu_output(
                    layout,
                    processed,
                )

                expected = (
                    output_initial
                    ^ operation_reference(
                        opcode,
                        a,
                        b,
                    )
                )

                if observed.output != expected:
                    failures += 1

                    print(
                        "FAIL target "
                        f"OP={VALID_OPERATIONS[opcode]} "
                        f"A={a:02X} "
                        f"B={b:02X} "
                        f"OUT0={output_initial:02X} "
                        f"OUT={observed.output:02X} "
                        f"expected={expected:02X}"
                    )

    print(f"Target cases tested : {tests}")
    print(f"Target failures     : {failures}")

    return failures


def test_inverse_round_trip(
    layout: ALULayout,
    operations: tuple[CompiledGate, ...],
) -> int:
    inverse = inverse_compiled_circuit(operations)

    failures = 0
    tests = 0

    samples = (
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
    )

    print()
    print("=== COMPLETE ALU INVERSE TEST ===")
    print()

    for opcode in range(8):
        for a in samples:
            for b in samples:
                for output_initial in (0x00, 0xA5):
                    tests += 1

                    original = prepare_alu_input(
                        layout,
                        opcode,
                        a,
                        b,
                        output_initial,
                    )

                    processed = apply_basis_circuit(
                        operations,
                        original,
                    )

                    restored = apply_basis_circuit(
                        inverse,
                        processed,
                    )

                    if restored != original:
                        failures += 1

                        if failures <= 20:
                            print(
                                "FAIL inverse "
                                f"OP={opcode:03b} "
                                f"A={a:02X} "
                                f"B={b:02X}"
                            )

    print(f"Inverse cases tested : {tests}")
    print(f"Inverse failures     : {failures}")

    return failures


# ================================================================
# Sparse quantum-superposition test
# ================================================================

def sparse_state_norm(
    state: dict[int, complex],
) -> float:
    return math.sqrt(
        sum(
            abs(amplitude) ** 2
            for amplitude in state.values()
        )
    )


def sparse_states_equal(
    first: dict[int, complex],
    second: dict[int, complex],
) -> bool:
    keys = set(first) | set(second)

    return all(
        abs(
            first.get(key, 0j)
            - second.get(key, 0j)
        )
        <= TOLERANCE
        for key in keys
    )


def test_operation_superposition(
    layout: ALULayout,
    operations: tuple[CompiledGate, ...],
) -> int:
    print()
    print("=== INTEGRATED ALU SUPERPOSITION TEST ===")
    print()

    a = 0xA5
    b = 0x5A

    amplitude = 1 / math.sqrt(
        len(VALID_OPERATIONS)
    )

    input_state: dict[int, complex] = {}

    for opcode in VALID_OPERATIONS:
        basis_state = prepare_alu_input(
            layout,
            opcode,
            a,
            b,
        )

        input_state[basis_state] = amplitude

    observed = apply_sparse_state(
        operations,
        input_state,
    )

    expected: dict[int, complex] = {}

    for basis_state, basis_amplitude in input_state.items():
        mapped = apply_basis_circuit(
            operations,
            basis_state,
        )

        expected[mapped] = basis_amplitude

    mapping_correct = sparse_states_equal(
        observed,
        expected,
    )

    norm = sparse_state_norm(observed)

    print("Input operation branches :", len(input_state))
    print("Output branches          :", len(observed))
    print("State norm               :", f"{norm:.12f}")
    print("Linear mapping           :", mapping_correct)

    print()
    print("Observed coherent ALU branches:")

    for basis_state, branch_amplitude in observed.items():
        output = decode_alu_output(
            layout,
            basis_state,
        )

        operation_name = VALID_OPERATIONS.get(
            output.opcode,
            "RESERVED",
        )

        print(
            f"  amplitude={branch_amplitude} "
            f"OP={operation_name:<5} "
            f"PAPO={output.papo:02X} "
            f"YO={output.yo:02X} "
            f"SEDA={output.seda} "
            f"JU={output.ju} "
            f"KERE={output.kere} "
            f"OUT={output.output:02X}"
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
# Selected examples
# ================================================================

def display_selected_examples(
    layout: ALULayout,
    operations: tuple[CompiledGate, ...],
) -> None:
    examples = (
        (OP_PAPO, 0xA5, 0x5A),
        (OP_PAPO, 0xFF, 0x01),
        (OP_YO, 0x10, 0x01),
        (OP_YO, 0x00, 0x01),
        (OP_SEDA, 0x55, 0x55),
        (OP_SEDA, 0x55, 0xAA),
        (OP_JU, 0xFF, 0x01),
        (OP_KERE, 0x01, 0xFF),
    )

    print()
    print("=== SELECTED INTEGRATED IFÁ ALU STATES ===")
    print()

    print(
        "OP     A   B  | PAPO YO | SEDA JU KERE | OUT"
    )
    print(
        "------------------------------------------------"
    )

    for opcode, a, b in examples:
        original = prepare_alu_input(
            layout,
            opcode,
            a,
            b,
        )

        processed = apply_basis_circuit(
            operations,
            original,
        )

        observed = decode_alu_output(
            layout,
            processed,
        )

        print(
            f"{VALID_OPERATIONS[opcode]:<5}  "
            f"{a:02X}  {b:02X} | "
            f" {observed.papo:02X}   "
            f"{observed.yo:02X} | "
            f"  {observed.seda}    "
            f"{observed.ju}    "
            f"{observed.kere}  | "
            f"{observed.output:02X}"
        )


# ================================================================
# Main
# ================================================================

def main() -> int:
    layout = build_integrated_ifa_alu()
    circuit = layout.circuit
    operations = compile_circuit(circuit)

    print("=== INTEGRATED 8-BIT IFÁ QUANTUM ALU ===")
    print()

    print("Width               :", WIDTH)
    print("Qubits              :", circuit.num_qubits)
    print("Circuit depth       :", circuit.depth())
    print("Qiskit gate count   :", circuit.count_ops())
    print("Compiled operations :", len(operations))

    print()
    print("Native operations:")
    print("  000  PAPO  A + B")
    print("  001  YO    A - B")
    print("  010  SEDA  A == B")
    print("  011  JU    A > B")
    print("  100  KERE  A < B")

    print()
    print("Generation pipeline:")
    print("  A,B -> PAPO carry-ripple")
    print("  A,B -> B_NOT -> YO subtraction ripple")
    print("  A,B -> difference/equality relation")
    print("  YO final carry + equality -> JU/KERE")
    print("  OP -> reversible native-result selection")

    display_selected_examples(
        layout,
        operations,
    )

    failures = 0

    failures += test_candidate_generators(
        layout,
        operations,
    )

    failures += test_exhaustive_native_operations(
        layout,
        operations,
    )

    failures += test_reserved_opcodes(
        layout,
        operations,
    )

    failures += test_arbitrary_output_target(
        layout,
        operations,
    )

    failures += test_inverse_round_trip(
        layout,
        operations,
    )

    failures += test_operation_superposition(
        layout,
        operations,
    )

    print()
    print("=== REVERSIBLE ALU STATEMENT ===")
    print()
    print(
        "PAPO, YO, SEDA, JU and KERE are generated inside "
        "the circuit."
    )
    print(
        "No candidate result is preloaded by the classical test "
        "harness."
    )
    print(
        "The ALU consists exclusively of X and controlled-X "
        "permutation gates."
    )
    print(
        "Therefore the complete 8-bit ALU is a reversible "
        "unitary quantum operator."
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


