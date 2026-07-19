#!/usr/bin/env python3
"""
============================================================================
IFÁ Processor V4.5
Native Relation Frame
============================================================================

The frame preserves both direct and Φ-P8 information:

    Binary A,B
        ↓
    Φ-P8(A), Φ-P8(B)
        ↓
    RA / RD / R0 relation coordinates
        ↓
    Native operation
        ↓
    Y and Φ-P8(Y)

Locked relation equations:

    RA = A AND B
    RD = A XOR B
    R0 = NOT(A OR B)

For a fixed width, RA, RD and R0 form a complete disjoint partition.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RelationFrame:
    # Identity
    relation_id: str
    operation: str
    width: int

    # Resolved binary operands
    operand_a: int
    operand_b: int

    # Φ-P8 operand coordinates
    PHI_A: tuple[int, ...]
    PHI_B: tuple[int, ...]

    # Native result
    Y: int
    PHI_Y: tuple[int, ...]

    # Relation-frame channels
    RA: int
    RD: int
    R0: int

    # Transport beyond the active relation window
    T: int

    # Comparison channels
    EQ: int
    GT: int
    LT: int

    # Runtime state
    STATE: int
    VALID: bool

    # Unrestricted arithmetic result before width projection
    VALUE: Any

    @property
    def mask(self) -> int:
        return (1 << self.width) - 1

    @property
    def relation_partition(self) -> int:
        return self.RA | self.RD | self.R0

    @property
    def partition_is_complete(self) -> bool:
        return self.relation_partition == self.mask

    @property
    def channels_are_disjoint(self) -> bool:
        return (
            (self.RA & self.RD) == 0
            and (self.RA & self.R0) == 0
            and (self.RD & self.R0) == 0
        )

    def validate(self) -> None:
        """
        Validate the mathematical relation-frame invariants.
        """

        if self.width <= 0:
            raise ValueError("Relation-frame width must be positive.")

        bounded_fields = {
            "operand_a": self.operand_a,
            "operand_b": self.operand_b,
            "Y": self.Y,
            "RA": self.RA,
            "RD": self.RD,
            "R0": self.R0,
        }

        for name, value in bounded_fields.items():
            if not 0 <= value <= self.mask:
                raise ValueError(
                    f"{name}={value} is outside the "
                    f"{self.width}-bit relation window."
                )

        bit_fields = {
            "T": self.T,
            "EQ": self.EQ,
            "GT": self.GT,
            "LT": self.LT,
            "STATE": self.STATE,
        }

        for name, value in bit_fields.items():
            if value not in (0, 1):
                raise ValueError(
                    f"{name} must be a state bit; received {value!r}."
                )

        if self.EQ + self.GT + self.LT != 1:
            raise ValueError(
                "Exactly one comparison channel must be active."
            )

        if not self.partition_is_complete:
            raise ValueError(
                "RA, RD and R0 do not cover the complete relation window."
            )

        if not self.channels_are_disjoint:
            raise ValueError(
                "RA, RD and R0 must be mutually disjoint."
            )

        if self.STATE != self.T:
            raise ValueError(
                "For the current V4.5 execution model, STATE must "
                "preserve the transport state bit."
            )

    def summary(self) -> dict[str, Any]:
        return asdict(self)

    def binary(self, value: int) -> str:
        return f"{value:0{self.width}b}"

    def compact(self) -> str:
        return (
            f"{self.relation_id} "
            f"Y=0x{self.Y:0{max(2, self.width // 4)}X} "
            f"RA=0x{self.RA:0{max(2, self.width // 4)}X} "
            f"RD=0x{self.RD:0{max(2, self.width // 4)}X} "
            f"R0=0x{self.R0:0{max(2, self.width // 4)}X} "
            f"T={self.T} "
            f"EQ={self.EQ} "
            f"GT={self.GT} "
            f"LT={self.LT} "
            f"STATE={self.STATE} "
            f"VALID={int(self.VALID)}"
        )

    def __str__(self) -> str:
        return self.compact()
