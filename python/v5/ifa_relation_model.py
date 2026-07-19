#!/usr/bin/env python3
"""
IFÁ Processor V5
Canonical classical Relation Frame model.

Locked definition:

    Y  = (A + B) mod 2^width
    RA = A AND B
    RD = A XOR B
    R0 = NOT(A OR B), restricted to width bits
    T  = RD XOR Y

The model is intentionally independent of V2, V3, V4, RTL,
Qiskit, and every external quantum package.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True, slots=True)
class RelationFrame:
    """Complete classical IFÁ Relation Frame."""

    y: int
    ra: int
    rd: int
    r0: int
    t: int

    def as_tuple(self) -> tuple[int, int, int, int, int]:
        return self.y, self.ra, self.rd, self.r0, self.t

    def packed(self, width: int) -> int:
        """
        Pack the five width-bit fields as:

            Y | RA | RD | R0 | T

        Y occupies the most significant field.
        """
        validate_width(width)

        mask = width_mask(width)

        for name, value in zip(
            ("Y", "RA", "RD", "R0", "T"),
            self.as_tuple(),
            strict=True,
        ):
            if value < 0 or value > mask:
                raise ValueError(
                    f"{name}=0x{value:X} does not fit in {width} bits"
                )

        result = 0
        for value in self.as_tuple():
            result = (result << width) | value

        return result

    def bit_string(self, width: int, separator: str = " ") -> str:
        """Return the frame as Y RA RD R0 T binary fields."""
        validate_width(width)
        return separator.join(
            format(value, f"0{width}b")
            for value in self.as_tuple()
        )


def validate_width(width: int) -> None:
    if not isinstance(width, int):
        raise TypeError("width must be an integer")
    if width < 1:
        raise ValueError("width must be at least 1")


def width_mask(width: int) -> int:
    validate_width(width)
    return (1 << width) - 1


def validate_operand(value: int, width: int, name: str) -> None:
    mask = width_mask(width)

    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")

    if value < 0 or value > mask:
        raise ValueError(
            f"{name}=0x{value:X} does not fit in {width} bits"
        )


def relation_frame(a: int, b: int, width: int) -> RelationFrame:
    """
    Compute the locked IFÁ V5 classical Relation Frame.
    """
    validate_operand(a, width, "A")
    validate_operand(b, width, "B")

    mask = width_mask(width)

    y = (a + b) & mask
    ra = a & b
    rd = a ^ b
    r0 = (~(a | b)) & mask
    t = rd ^ y

    return RelationFrame(
        y=y,
        ra=ra,
        rd=rd,
        r0=r0,
        t=t,
    )


def enumerate_inputs(
    width: int,
) -> Iterator[tuple[int, int, RelationFrame]]:
    """Yield every A, B and Relation Frame for the selected width."""
    validate_width(width)

    limit = 1 << width

    for a in range(limit):
        for b in range(limit):
            yield a, b, relation_frame(a, b, width)


def tensor_register_dimension(width: int) -> int:
    """
    Dimension of the full five-register relation space.

    Five registers, each containing `width` bits:

        dimension = 2^(5 * width)
    """
    validate_width(width)
    return 1 << (5 * width)


def compact_qubit_count(number_of_states: int) -> int:
    """Minimum qubits required to encode number_of_states basis states."""
    if number_of_states < 1:
        raise ValueError("number_of_states must be at least 1")

    return (number_of_states - 1).bit_length()


if __name__ == "__main__":
    width = 1

    print("IFÁ V5 CANONICAL RELATION MODEL")
    print("=" * 60)
    print(f"width = {width}")
    print()

    for a, b, frame in enumerate_inputs(width):
        print(
            f"A={a:0{width}b} "
            f"B={b:0{width}b} | "
            f"Y RA RD R0 T = {frame.bit_string(width)} | "
            f"packed={frame.packed(width):0{5 * width}b}"
        )
