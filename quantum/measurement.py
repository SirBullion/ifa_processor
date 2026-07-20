"""Basis-state preparation, exact execution, and canonical result decoding."""

from numbers import Integral

from core.exceptions import QuantumDomainError
from quantum.comparison import ORACLE_OPERATIONS, QUANTUM_OPERATION_CODES
from quantum.native import ORACLES, relation_output


class QuantumDependencyError(RuntimeError):
    """Raised when the optional Qiskit dependency is unavailable."""


def require_byte(value, name):
    if isinstance(value, bool):
        value = int(value)
    if not isinstance(value, Integral) or not 0 <= value <= 0xFF:
        raise QuantumDomainError(
            f"{name} must be an integer between 0 and 255; received {value!r}."
        )
    return int(value)


def execute_native_operation(operation, operand_a, operand_b):
    """Execute one supported operation through the verified reversible ALU."""
    from quantum.gates import compiled_alu

    name = str(operation).strip().upper()
    a = require_byte(operand_a, "operand A")
    b = require_byte(operand_b, "operand B")

    if name in ORACLE_OPERATIONS:
        return ORACLES[name].execute(a, b)

    opcode = QUANTUM_OPERATION_CODES[name]

    # The verified circuit is byte-wide. Refuse cases where modular output
    # would disagree with the canonical Python backend.
    if name == "PAPO" and a + b > 0xFF:
        raise QuantumDomainError("PAPO result exceeds the verified 8-bit quantum domain.")
    if name == "YO" and a < b:
        raise QuantumDomainError("YO result is negative and outside the verified 8-bit quantum domain.")

    module, layout, operations = compiled_alu()
    prepared = module.prepare_alu_input(layout, opcode, a, b)
    measured_basis_state = module.apply_basis_circuit(operations, prepared)
    decoded = module.decode_alu_output(layout, measured_basis_state).output
    relation = relation_output(name, a, b)
    if decoded != relation.logical_result:
        raise RuntimeError(
            f"Quantum measurement decoded {decoded!r}; expected "
            f"{relation.logical_result!r}."
        )
    return relation


__all__ = [
    "QuantumDependencyError", "QuantumDomainError", "require_byte",
    "execute_native_operation",
]
