#!/usr/bin/env python3
"""
======================================================================

IFÁ Processor V4.5
Relation Deduplication Pass

Purpose
-------
Group equivalent computations into unique relation classes.

Pipeline

Requested computations
        ↓
Binary operands
        ↓
Φ-P8 relation canonicalizer
        ↓
Relation equivalence classes
        ↓
Unique computations + consumers

======================================================================
"""

from dataclasses import dataclass, field
from typing import Any, Iterable

from compiler.relation_canonicalizer import (
    RelationSignature,
    build_relation_signature,
)


@dataclass(frozen=True)
class RelationRequest:
    """
    One requested computation in the original program.
    """

    request_id: int
    op: str
    a: Any
    b: Any
    destination: str | None = None


@dataclass
class RelationClass:
    """
    One unique computational relation.

    Several requests may point to the same RelationClass.
    """

    relation_id: str
    signature: RelationSignature

    representative: RelationRequest
    consumers: list[int] = field(default_factory=list)
    destinations: list[str] = field(default_factory=list)

    @property
    def reuse_count(self) -> int:
        return max(0, len(self.consumers) - 1)


@dataclass
class DeduplicationResult:
    """
    Full result of the relation deduplication pass.
    """

    requests: list[RelationRequest]
    relations: list[RelationClass]
    request_to_relation: dict[int, str]

    @property
    def requested_count(self) -> int:
        return len(self.requests)

    @property
    def unique_count(self) -> int:
        return len(self.relations)

    @property
    def reused_count(self) -> int:
        return self.requested_count - self.unique_count

    @property
    def reduction_ratio(self) -> float:
        if self.requested_count == 0:
            return 0.0

        return self.reused_count / self.requested_count


def normalize_request(
    request: RelationRequest | tuple | dict,
    fallback_id: int,
) -> RelationRequest:
    """
    Accept convenient tuple, dictionary or RelationRequest input.

    Supported tuple forms:

        ("YO", 8, 9)
        ("YO", 8, 9, "A")

    Supported dictionary form:

        {
            "op": "YO",
            "a": 8,
            "b": 9,
            "destination": "A"
        }
    """

    if isinstance(request, RelationRequest):
        return request

    if isinstance(request, dict):
        return RelationRequest(
            request_id=int(
                request.get(
                    "request_id",
                    fallback_id,
                )
            ),
            op=str(request["op"]),
            a=request["a"],
            b=request["b"],
            destination=request.get("destination"),
        )

    if isinstance(request, tuple):
        if len(request) == 3:
            op, a, b = request
            destination = None

        elif len(request) == 4:
            op, a, b, destination = request

        else:
            raise ValueError(
                "Tuple request must contain "
                "(op, a, b) or (op, a, b, destination)."
            )

        return RelationRequest(
            request_id=fallback_id,
            op=str(op),
            a=a,
            b=b,
            destination=destination,
        )

    raise TypeError(
        "Unsupported relation request type: "
        f"{type(request).__name__}"
    )


def deduplicate_relations(
    requests: Iterable[RelationRequest | tuple | dict],
) -> DeduplicationResult:
    """
    Convert requested operations into unique relation classes.
    """

    normalized_requests: list[RelationRequest] = []

    relation_table: dict[
        tuple,
        RelationClass,
    ] = {}

    relation_order: list[RelationClass] = []
    request_to_relation: dict[int, str] = {}

    for fallback_id, raw_request in enumerate(requests):
        request = normalize_request(
            raw_request,
            fallback_id,
        )

        normalized_requests.append(request)

        signature = build_relation_signature(
            request.op,
            request.a,
            request.b,
        )

        relation_key = signature.relation_key

        if relation_key not in relation_table:
            relation_id = f"R{len(relation_order)}"

            relation_class = RelationClass(
                relation_id=relation_id,
                signature=signature,
                representative=request,
            )

            relation_table[relation_key] = relation_class
            relation_order.append(relation_class)

        relation_class = relation_table[relation_key]

        relation_class.consumers.append(
            request.request_id
        )

        if request.destination is not None:
            relation_class.destinations.append(
                str(request.destination)
            )

        request_to_relation[
            request.request_id
        ] = relation_class.relation_id

    return DeduplicationResult(
        requests=normalized_requests,
        relations=relation_order,
        request_to_relation=request_to_relation,
    )


def print_deduplication_report(
    result: DeduplicationResult,
) -> None:
    """
    Display a readable relation-class report.
    """

    print("=" * 72)
    print("IFÁ PROCESSOR V4.5 RELATION DEDUPLICATION")
    print("=" * 72)

    print(
        f"Requested computations : "
        f"{result.requested_count}"
    )

    print(
        f"Unique relations       : "
        f"{result.unique_count}"
    )

    print(
        f"Reused computations    : "
        f"{result.reused_count}"
    )

    print(
        f"Reduction ratio        : "
        f"{result.reduction_ratio:.2%}"
    )

    print()

    for relation in result.relations:
        representative = relation.representative
        signature = relation.signature

        print("-" * 72)
        print(f"Relation ID     : {relation.relation_id}")

        print(
            f"Representative  : "
            f"{representative.op} "
            f"{representative.a} ATI "
            f"{representative.b}"
        )

        print(
            f"Relation key    : "
            f"{signature.relation_key}"
        )

        print(
            f"Relation hash   : "
            f"{signature.relation_hash}"
        )

        print(
            f"Consumers       : "
            f"{relation.consumers}"
        )

        print(
            f"Destinations    : "
            f"{relation.destinations}"
        )

        print(
            f"Reuse count     : "
            f"{relation.reuse_count}"
        )

    print("=" * 72)


if __name__ == "__main__":
    demo_program = [
        ("YO", 8, 9, "A"),
        ("YO", 8, 9, "B"),
        ("PAPO", 3, 4, "C"),
        ("PAPO", 4, 3, "D"),
        ("YO", 8, 9, "E"),
        ("YO", 9, 8, "F"),
        ("DAGBA", 5, 6, "G"),
        ("DAGBA", 6, 5, "H"),
    ]

    result = deduplicate_relations(
        demo_program
    )

    print_deduplication_report(
        result
    )
