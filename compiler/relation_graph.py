#!/usr/bin/env python3
"""
IFÁ Processor V4.5
Relation Dependency Graph

Purpose
-------
Build a directed acyclic graph of unique relation computations.

The graph identifies:

    • which relations depend on earlier relations
    • which relations are immediately ready
    • which relations can execute in parallel
    • the execution wave for every relation
    • cycles or invalid dependency structures

Pipeline
--------
Program operations
        ↓
Relation canonicalisation
        ↓
Relation deduplication
        ↓
Dependency graph
        ↓
Parallel execution waves
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from compiler.relation_reference import RelationReference
from compiler.relation_deduplicator import (
    DeduplicationResult,
    RelationClass,
    RelationRequest,
    deduplicate_relations,
)


@dataclass
class RelationGraphNode:
    """
    One unique relation inside the dependency graph.
    """

    relation_id: str
    relation: RelationClass

    dependencies: set[str] = field(default_factory=set)
    dependents: set[str] = field(default_factory=set)

    wave: int | None = None

    @property
    def ready_without_dependencies(self) -> bool:
        return len(self.dependencies) == 0


@dataclass
class RelationDependencyGraph:
    """
    Complete relation dependency graph.
    """

    nodes: dict[str, RelationGraphNode]

    destination_to_relation: dict[str, RelationReference]
    request_to_relation: dict[int, str]

    execution_waves: list[list[str]]

    @property
    def relation_count(self) -> int:
        return len(self.nodes)

    @property
    def wave_count(self) -> int:
        return len(self.execution_waves)

    @property
    def maximum_parallelism(self) -> int:
        if not self.execution_waves:
            return 0

        return max(
            len(wave)
            for wave in self.execution_waves
        )


def is_symbolic_operand(value: Any) -> bool:
    """
    Return True when an operand refers to a previous destination.

    Integers and floats are treated as constants.

    Strings are treated as symbolic references only when they match a
    previously produced destination.
    """

    return isinstance(value, str)


def build_destination_table(
    result: DeduplicationResult,
) -> dict[str, RelationReference]:
    """
    Map every destination name to the relation that produces it.

    Example:

        A -> R0
        B -> R1
        C -> R2
    """

    destination_to_relation: dict[str, RelationReference] = {}

    for request in result.requests:
        if request.destination is None:
            continue

        destination = str(request.destination)

        if destination in destination_to_relation:
            raise ValueError(
                f"Destination {destination!r} is assigned more than once."
            )

        relation_id = result.request_to_relation[
            request.request_id
        ]

        destination_to_relation[
            destination
        ] = RelationReference(
            producer=relation_id,
            destination=destination,
        )

    return destination_to_relation


def resolve_operand_dependency(
    operand: Any,
    destination_to_relation: dict[str, RelationReference],
) -> str | None:
    """
    Resolve one operand into its producer relation.

    Constants return None.

    Symbolic operands return the relation that produced them.
    """

    if not is_symbolic_operand(operand):
        return None

    reference = destination_to_relation.get(
        operand
    )

    if reference is None:
        return None

    return reference.producer


def build_graph_nodes(
    result: DeduplicationResult,
    destination_to_relation: dict[str, RelationReference],
) -> dict[str, RelationGraphNode]:
    """
    Create graph nodes and dependency edges.
    """

    nodes: dict[str, RelationGraphNode] = {}

    for relation in result.relations:
        nodes[relation.relation_id] = RelationGraphNode(
            relation_id=relation.relation_id,
            relation=relation,
        )

    for relation in result.relations:
        node = nodes[relation.relation_id]

        representative = relation.representative

        operands = (
            representative.a,
            representative.b,
        )

        for operand in operands:
            dependency_id = resolve_operand_dependency(
                operand,
                destination_to_relation,
            )

            if dependency_id is None:
                continue

            if dependency_id == relation.relation_id:
                raise ValueError(
                    f"Relation {relation.relation_id} depends on itself."
                )

            node.dependencies.add(
                dependency_id
            )

            nodes[
                dependency_id
            ].dependents.add(
                relation.relation_id
            )

    return nodes


def calculate_execution_waves(
    nodes: dict[str, RelationGraphNode],
) -> list[list[str]]:
    """
    Perform topological scheduling.

    Relations in the same wave have no unresolved dependency between them
    and may execute concurrently.
    """

    unresolved_dependencies = {
        relation_id: set(node.dependencies)
        for relation_id, node in nodes.items()
    }

    unscheduled = set(nodes)
    waves: list[list[str]] = []

    wave_number = 0

    while unscheduled:
        ready = sorted(
            relation_id
            for relation_id in unscheduled
            if not unresolved_dependencies[
                relation_id
            ]
        )

        if not ready:
            remaining = sorted(unscheduled)

            raise ValueError(
                "Dependency cycle detected among relations: "
                + ", ".join(remaining)
            )

        waves.append(ready)

        for relation_id in ready:
            nodes[relation_id].wave = wave_number
            unscheduled.remove(relation_id)

        for relation_id in unscheduled:
            unresolved_dependencies[
                relation_id
            ].difference_update(
                ready
            )

        wave_number += 1

    return waves


def build_relation_graph(
    requests: Iterable[
        RelationRequest | tuple | dict
    ],
) -> RelationDependencyGraph:
    """
    Build the complete relation dependency graph.
    """

    deduplication = deduplicate_relations(
        requests
    )

    destination_to_relation = build_destination_table(
        deduplication
    )

    nodes = build_graph_nodes(
        deduplication,
        destination_to_relation,
    )

    execution_waves = calculate_execution_waves(
        nodes
    )

    return RelationDependencyGraph(
        nodes=nodes,
        destination_to_relation=destination_to_relation,
        request_to_relation=deduplication.request_to_relation,
        execution_waves=execution_waves,
    )


def format_operand(operand: Any) -> str:
    """
    Format an operand for reports.
    """

    if isinstance(operand, str):
        return operand

    return str(operand)


def print_relation_graph(
    graph: RelationDependencyGraph,
) -> None:
    """
    Print a readable dependency and scheduling report.
    """

    print("=" * 76)
    print("IFÁ PROCESSOR V4.5 RELATION DEPENDENCY GRAPH")
    print("=" * 76)

    print(
        f"Unique relations       : "
        f"{graph.relation_count}"
    )

    print(
        f"Execution waves        : "
        f"{graph.wave_count}"
    )

    print(
        f"Maximum parallelism    : "
        f"{graph.maximum_parallelism}"
    )

    print()

    print("DESTINATION PRODUCERS")
    print("-" * 76)

    for destination, reference in sorted(
        graph.destination_to_relation.items()
    ):
        print(
            f"{destination:<16} -> "
            f"{reference.producer}:{reference.destination}"
        )

    print()
    print("RELATION NODES")
    print("-" * 76)

    for relation_id in sorted(
        graph.nodes,
        key=lambda value: int(value[1:]),
    ):
        node = graph.nodes[relation_id]
        relation = node.relation
        request = relation.representative

        print(f"Relation ID     : {relation_id}")

        print(
            f"Operation       : "
            f"{request.op} "
            f"{format_operand(request.a)} ATI "
            f"{format_operand(request.b)}"
        )

        print(
            f"Destinations    : "
            f"{relation.destinations}"
        )

        print(
            f"Dependencies    : "
            f"{sorted(node.dependencies)}"
        )

        print(
            f"Dependents      : "
            f"{sorted(node.dependents)}"
        )

        print(
            f"Execution wave  : "
            f"{node.wave}"
        )

        print(
            f"Consumers       : "
            f"{relation.consumers}"
        )

        print(
            f"Reuse count     : "
            f"{relation.reuse_count}"
        )

        print("-" * 76)

    print()
    print("PARALLEL EXECUTION WAVES")
    print("-" * 76)

    for wave_number, relation_ids in enumerate(
        graph.execution_waves
    ):
        print(
            f"WAVE {wave_number}: "
            + ", ".join(relation_ids)
        )

        for relation_id in relation_ids:
            node = graph.nodes[relation_id]
            request = node.relation.representative

            print(
                f"    {relation_id:<4} "
                f"{request.op} "
                f"{format_operand(request.a)} ATI "
                f"{format_operand(request.b)}"
            )

    print("=" * 76)


if __name__ == "__main__":
    demo_program = [
        # Wave 0: three independent relations
        {
            "request_id": 0,
            "op": "PAPO",
            "a": 2,
            "b": 3,
            "destination": "A",
        },
        {
            "request_id": 1,
            "op": "YO",
            "a": 10,
            "b": 4,
            "destination": "B",
        },
        {
            "request_id": 2,
            "op": "DAGBA",
            "a": 5,
            "b": 6,
            "destination": "C",
        },

        # Duplicate of request 0
        {
            "request_id": 3,
            "op": "PAPO",
            "a": 3,
            "b": 2,
            "destination": "A_COPY",
        },

        # Wave 1: depends on A and B
        {
            "request_id": 4,
            "op": "PAPO",
            "a": "A",
            "b": "B",
            "destination": "D",
        },

        # Wave 1: depends only on C
        {
            "request_id": 5,
            "op": "YO",
            "a": "C",
            "b": 2,
            "destination": "E",
        },

        # Wave 2: depends on D and E
        {
            "request_id": 6,
            "op": "DAGBA",
            "a": "D",
            "b": "E",
            "destination": "F",
        },
    ]

    relation_graph = build_relation_graph(
        demo_program
    )

    print_relation_graph(
        relation_graph
    )
