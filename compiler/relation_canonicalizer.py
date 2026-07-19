#!/usr/bin/env python3
"""
======================================================================

IFÁ Processor V4.5
Relation Canonicalizer

Purpose
-------
Convert an operation into a canonical relation signature.

Used for

    • compile-time relation deduplication
    • runtime RMU lookup
    • dependency graph construction
    • parallel scheduler

Pipeline

Binary
   ↓
Φ-P8
   ↓
Relation Signature
   ↓
Relation Key

======================================================================
"""

from dataclasses import dataclass
from hashlib import sha256

from compiler.phi_p8_adapter import backend_description, phi_p8

# ------------------------------------------------------------
# Operation properties
# ------------------------------------------------------------

COMMUTATIVE = {
    "PAPO",
    "DAGBA",
    "KU",
    "GBE",
    "XOR",
}

NON_COMMUTATIVE = {
    "YO",
    "PIN",
    "SEDA",
}


@dataclass(frozen=True)
class RelationSignature:

    op: str

    phi_a: str
    phi_b: str

    canonical_a: str
    canonical_b: str

    relation_key: tuple
    relation_hash: str


# ------------------------------------------------------------
# Real Φ-P8 is supplied by compiler.phi_p8_adapter
# ------------------------------------------------------------

# ------------------------------------------------------------
# Canonical operand ordering
# ------------------------------------------------------------

def canonical_operands(op, a, b):

    op = op.upper()

    if op in COMMUTATIVE:
        return tuple(sorted((a, b)))

    return a, b


# ------------------------------------------------------------
# Build relation signature
# ------------------------------------------------------------

def build_relation_signature(op, a, b):

    op = op.upper()

    if isinstance(a, int):
        phi_a = phi_p8(a)
    else:
        phi_a = ("REF", str(a))

    if isinstance(b, int):
        phi_b = phi_p8(b)
    else:
        phi_b = ("REF", str(b))

    ca, cb = canonical_operands(
        op,
        phi_a,
        phi_b,
    )

    relation_key = (
        op,
        ca,
        cb,
    )

    relation_hash = sha256(
        str(relation_key).encode()
    ).hexdigest()

    return RelationSignature(
        op=op,

        phi_a=phi_a,
        phi_b=phi_b,

        canonical_a=ca,
        canonical_b=cb,

        relation_key=relation_key,
        relation_hash=relation_hash,
    )


# ------------------------------------------------------------
# Pretty printer
# ------------------------------------------------------------

def print_signature(sig):

    print("=" * 70)

    print("Relation Signature\n")

    print(f"Operation        : {sig.op}")
    print(f"ΦA               : {sig.phi_a}")
    print(f"ΦB               : {sig.phi_b}")

    print()

    print(f"Canonical A      : {sig.canonical_a}")
    print(f"Canonical B      : {sig.canonical_b}")

    print()

    print(f"Relation Key     : {sig.relation_key}")
    print(f"Relation Hash    : {sig.relation_hash}")

    print("=" * 70)


# ------------------------------------------------------------
# Demo
# ------------------------------------------------------------

if __name__ == "__main__":

    print(f"Φ-P8 backend     : {backend_description()}")

    tests = [

        ("PAPO",3,4),
        ("PAPO",4,3),

        ("YO",8,9),
        ("YO",9,8),

        ("KU",5,2),
        ("KU",2,5),

        ("GBE",6,1),
        ("GBE",1,6),

    ]

    for t in tests:

        sig = build_relation_signature(*t)

        print_signature(sig)
