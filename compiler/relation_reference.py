#!/usr/bin/env python3
"""
======================================================================
IFÁ Processor V4.5

Relation Reference
======================================================================

A symbolic operand should refer to the relation that produced it,
not merely the destination name.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RelationReference:

    producer: str
    destination: str

    def key(self):
        return (
            self.producer,
            self.destination,
        )

    def __repr__(self):

        return (
            f"{self.producer}:{self.destination}"
        )
