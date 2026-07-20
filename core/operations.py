#!/usr/bin/env python3
"""
============================================================================
IFÁ Processor V4.5

Canonical Native Operations

This module contains the single implementation of the IFÁ native
arithmetic and comparison operations.

Every execution engine must import from here.
============================================================================
"""

from __future__ import annotations

from numbers import Integral, Real
from typing import Any


class UnsupportedRelationOperation(RuntimeError):
    """Raised when an unknown IFÁ operation is requested."""


ALIASES = {
    "PAPO": "PAPO",
    "YO": "YO",

    "DAGBA": "DAGBA",
    "DÁGBA": "DAGBA",

    "PIN": "PIN",

    "KU": "KU",
    "KÙ": "KU",

    "GBE": "GBE",
    "GBÉ": "GBE",

    "SEDA": "SEDA",

    "JU": "JU",

    "KERE": "KERE",
    "KERÉ": "KERE",
}


def normalise_operation(operation: str) -> str:
    operation = str(operation).strip().upper()
    return ALIASES.get(operation, operation)


def require_numeric(value: Any, operand_name: str) -> Real:
    if isinstance(value, bool):
        return int(value)

    if not isinstance(value, Real):
        raise TypeError(
            f"{operand_name} must resolve to a numeric value; "
            f"received {value!r}."
        )

    return value


def execute_operation(
    operation: str,
    operand_a: Any,
    operand_b: Any,
) -> Any:
    """
    Locked IFÁ native operations.

        PAPO   A + B
        YO     A - B
        DAGBA  A * B
        PIN    A / B
        KU     A % B
        GBE    A ** B
        SEDA   A == B
        JU     A > B
        KERE   A < B
    """

    op = normalise_operation(operation)

    a = require_numeric(operand_a, "operand A")
    b = require_numeric(operand_b, "operand B")

    if op == "PAPO":
        return a + b

    if op == "YO":
        return a - b

    if op == "DAGBA":
        return a * b

    if op == "PIN":
        if b == 0:
            raise ZeroDivisionError(
                "PIN relation cannot divide by zero."
            )

        result = a / b

        if (
            isinstance(a, Integral)
            and isinstance(b, Integral)
            and a % b == 0
        ):
            return a // b

        return result

    if op == "KU":
        if b == 0:
            raise ZeroDivisionError(
                "KU relation cannot calculate modulo zero."
            )

        return a % b

    if op == "GBE":
        return a ** b

    if op == "SEDA":
        return int(a == b)

    if op == "JU":
        return int(a > b)

    if op == "KERE":
        return int(a < b)

    raise UnsupportedRelationOperation(
        f"Unsupported IFÁ operation: {operation!r}"
    )
