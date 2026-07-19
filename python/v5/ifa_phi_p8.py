#!/usr/bin/env python3
"""
Canonical IFÁ Φ-P8 Anchor–Agreement transform.

For each adjacent pair (A, B):

    Anchor    = A
    Agreement = NOT(A XOR B)

The four byte pairs are:

    (x7, x6), (x5, x4), (x3, x2), (x1, x0)

The transform is self-inverse:

    Φ-P8(Φ-P8(x)) = x
"""

from __future__ import annotations


WIDTH = 8
MASK = (1 << WIDTH) - 1


def validate_bit(value: int, name: str = "bit") -> None:
    if value not in (0, 1):
        raise ValueError(f"{name} must be 0 or 1, received {value!r}")


def validate_byte(value: int, name: str = "value") -> None:
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")

    if not 0 <= value <= MASK:
        raise ValueError(f"{name} must be in the range 0..255")


def phi_p2(a: int, b: int) -> tuple[int, int]:
    """Map raw pair (A,B) to (Anchor,Agreement)."""
    validate_bit(a, "A")
    validate_bit(b, "B")

    anchor = a
    agreement = 1 ^ a ^ b

    return anchor, agreement


def phi_p2_inverse(
    anchor: int,
    agreement: int,
) -> tuple[int, int]:
    """Recover raw pair (A,B) from Anchor–Agreement."""
    validate_bit(anchor, "Anchor")
    validate_bit(agreement, "Agreement")

    a = anchor
    b = 1 ^ anchor ^ agreement

    return a, b


def phi_p8(value: int) -> int:
    """Apply Φ-P2 independently to all four adjacent byte pairs."""
    validate_byte(value)

    output = 0

    for b_position in (6, 4, 2, 0):
        a_position = b_position + 1

        a = (value >> a_position) & 1
        b = (value >> b_position) & 1

        anchor, agreement = phi_p2(a, b)

        output |= anchor << a_position
        output |= agreement << b_position

    return output


def phi_p8_inverse(value: int) -> int:
    """Apply the explicit inverse Φ-P8 reconstruction."""
    validate_byte(value)

    output = 0

    for agreement_position in (6, 4, 2, 0):
        anchor_position = agreement_position + 1

        anchor = (value >> anchor_position) & 1
        agreement = (value >> agreement_position) & 1

        a, b = phi_p2_inverse(anchor, agreement)

        output |= a << anchor_position
        output |= b << agreement_position

    return output


def bit_string(value: int, width: int = WIDTH) -> str:
    return format(value, f"0{width}b")


def permutation_vector() -> tuple[int, ...]:
    return tuple(phi_p8(value) for value in range(256))
