"""Reversible native-operation oracles using established IFÁ V4.5 maths.

The oracle action is ``|A,B,Y,T> -> |A,B,Y xor F_Y,T xor F_T>``.  Inputs
are preserved and applying an oracle twice restores the original state, the
same reversible controlled-X construction used throughout the verified V5
research circuits.
"""

from dataclasses import dataclass

from core.exceptions import QuantumDomainError
from core.operations import execute_operation
from quantum.phi import phi_p8


WIDTH = 8
MASK = 0xFF


@dataclass(frozen=True)
class QuantumRelationOutput:
    operation: str
    operand_a: int
    operand_b: int
    logical_result: object
    y: int
    t: int
    ra: int
    rd: int
    r0: int
    phi_a: int
    phi_b: int
    phi_y: int
    eq: int
    gt: int
    lt: int


@dataclass(frozen=True)
class OracleState:
    a: int
    b: int
    y: int = 0
    t: int = 0


def operation_channels(operation, a, b):
    """Return V4.5 Y/T channels without duplicating logical operations."""
    name = operation.upper()
    logical = execute_operation(name, a, b)

    if name == "PIN":
        if b == 0:
            raise ZeroDivisionError("PIN relation cannot divide by zero.")
        y, t = divmod(a, b)
    elif name == "KU":
        if b == 0:
            raise ZeroDivisionError("KU relation cannot calculate modulo zero.")
        t, y = divmod(a, b)
    else:
        if not isinstance(logical, int):
            raise QuantumDomainError(
                f"{name} does not resolve to an integer relation value: {logical!r}."
            )
        y = logical & MASK
        t = (logical >> WIDTH) & MASK if logical >= 0 else 1

    if name == "GBE" and logical.bit_length() > 2 * WIDTH:
        raise QuantumDomainError(
            "GBE result exceeds the established two-byte V4.5 relation window."
        )

    return logical, y & MASK, t & MASK


def relation_output(operation, a, b):
    logical, y, t = operation_channels(operation, a, b)
    return QuantumRelationOutput(
        operation=operation.upper(), operand_a=a, operand_b=b,
        logical_result=logical, y=y, t=t,
        ra=a & b, rd=a ^ b, r0=(~(a | b)) & MASK,
        phi_a=phi_p8(a), phi_b=phi_p8(b), phi_y=phi_p8(y),
        eq=int(a == b), gt=int(a > b), lt=int(a < b),
    )


class ReversibleNativeOracle:
    def __init__(self, operation):
        self.operation = operation.upper()

    def apply(self, state):
        relation = relation_output(self.operation, state.a, state.b)
        return OracleState(
            a=state.a,
            b=state.b,
            y=state.y ^ relation.y,
            t=state.t ^ relation.t,
        )

    def execute(self, a, b):
        prepared = OracleState(a, b)
        measured = self.apply(prepared)
        relation = relation_output(self.operation, a, b)
        if measured.y != relation.y or measured.t != relation.t:
            raise RuntimeError("Reversible oracle measurement decoding failed.")
        return relation


ORACLES = {
    name: ReversibleNativeOracle(name)
    for name in ("DAGBA", "PIN", "KU", "GBE")
}
