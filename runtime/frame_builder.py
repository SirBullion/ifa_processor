#!/usr/bin/env python3
"""
============================================================================
IFÁ Processor V4.5
Relation Frame Builder
============================================================================

Architecture:

    Binary A,B
        ↓
    Φ-P8(A), Φ-P8(B)
        ↓
    Relation coordinates RA/RD/R0
        ↓
    Native operation result
        ↓
    Y and Φ-P8(Y)
        ↓
    Transport/state preservation
"""

from __future__ import annotations

from numbers import Integral
from typing import Any

from compiler.phi_p8_adapter import phi_p8
from runtime.relation_frame import RelationFrame


def require_integer(value: Any, name: str) -> int:
    if isinstance(value, bool):
        return int(value)

    if not isinstance(value, Integral):
        raise TypeError(
            f"{name} must be an integer for an IFÁ relation frame; "
            f"received {value!r}."
        )

    return int(value)


def normalise_phi(value: Any) -> tuple[int, ...]:
    """
    The adapter normally returns a tuple. This validation prevents an
    unstable backend representation from entering the native frame.
    """

    transformed = phi_p8(value)

    if isinstance(transformed, tuple):
        return tuple(int(bit) for bit in transformed)

    if isinstance(transformed, list):
        return tuple(int(bit) for bit in transformed)

    if isinstance(transformed, str):
        compact = transformed.replace(" ", "")

        if compact and set(compact) <= {"0", "1"}:
            return tuple(int(bit) for bit in compact)

    raise TypeError(
        "Φ-P8 backend did not return a supported coordinate sequence: "
        f"{transformed!r}"
    )


def calculate_transport(
    raw_value: int,
    width: int,
) -> int:
    """
    Transport is active when the unrestricted operation result moves
    beyond the current relation window.

    For addition this is the ordinary carry-out condition.

    Examples for width=8:

        200 + 100 = 300  -> T=1
        2 + 3     = 5    -> T=0
        2 - 3     = -1   -> T=1
    """

    maximum = (1 << width) - 1

    return int(
        raw_value < 0
        or raw_value > maximum
    )


def build_relation_frame(
    relation_id: str,
    operation: str,
    operand_a: Any,
    operand_b: Any,
    value: Any,
    *,
    width: int = 8,
) -> RelationFrame:
    """
    Construct and validate one native IFÁ relation frame.
    """

    if width <= 0:
        raise ValueError("Relation-frame width must be positive.")

    raw_a = require_integer(
        operand_a,
        "operand A",
    )

    raw_b = require_integer(
        operand_b,
        "operand B",
    )

    raw_value = require_integer(
        value,
        "operation result",
    )

    mask = (1 << width) - 1

    # Project operands into the active relation window.
    a = raw_a & mask
    b = raw_b & mask

    # Locked IFÁ universal relation channels.
    ra = a & b
    rd = a ^ b
    r0 = (~(a | b)) & mask

    # Width-projected native output.
    y = raw_value & mask

    transport = calculate_transport(
        raw_value,
        width,
    )

    frame = RelationFrame(
        relation_id=str(relation_id),
        operation=str(operation).upper(),
        width=width,

        operand_a=a,
        operand_b=b,

        PHI_A=normalise_phi(a),
        PHI_B=normalise_phi(b),

        Y=y,
        PHI_Y=normalise_phi(y),

        RA=ra,
        RD=rd,
        R0=r0,

        T=transport,

        EQ=int(raw_a == raw_b),
        GT=int(raw_a > raw_b),
        LT=int(raw_a < raw_b),

        # Transport is preserved as the current execution state bit.
        STATE=transport,

        VALID=True,

        # Preserve the unrestricted result as well as projected Y.
        VALUE=raw_value,
    )

    frame.validate()

    return frame


if __name__ == "__main__":
    examples = [
        ("R0", "PAPO", 2, 3, 5),
        ("R1", "YO", 10, 4, 6),
        ("R2", "DAGBA", 5, 6, 30),
        ("R3", "PAPO", 200, 100, 300),
        ("R4", "YO", 2, 3, -1),
    ]

    print("=" * 76)
    print("IFÁ PROCESSOR V4.5 RELATION FRAME TEST")
    print("=" * 76)

    for example in examples:
        frame = build_relation_frame(
            *example,
            width=8,
        )

        print(frame)
        print(
            f"    Aφ={''.join(map(str, frame.PHI_A))} "
            f"Bφ={''.join(map(str, frame.PHI_B))} "
            f"Yφ={''.join(map(str, frame.PHI_Y))}"
        )
        print(
            f"    partition_complete="
            f"{frame.partition_is_complete} "
            f"disjoint={frame.channels_are_disjoint}"
        )
