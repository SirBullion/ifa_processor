#!/usr/bin/env python3
"""
============================================================================
IFÁ Processor V4.5
RMU-Integrated Relation Execution Engine
============================================================================

Execution path:

    Relation graph
        ↓
    Resolve operands through RMU
        ↓
    Execute native operation
        ↓
    Build RelationFrame
        ↓
    RMU.store(frame, destinations)
        ↓
    Broadcast destinations through RelationReference
"""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral, Real
from typing import Any

from compiler.relation_graph import (
    RelationDependencyGraph,
    build_relation_graph,
)
from compiler.relation_reference import RelationReference

from runtime.frame_builder import build_relation_frame
from runtime.relation_frame import RelationFrame
from runtime.relation_memory_unit import (
    RelationAbsent,
    RelationMemoryUnit,
)


from core.operations import (
    execute_operation,
    normalise_operation,
    require_numeric,
    UnsupportedRelationOperation,
)


# --------------------------------------------------------------------------
# Runtime errors
# --------------------------------------------------------------------------

class RelationExecutionError(RuntimeError):
    """Base error for relation execution."""


class RelationValueAbsent(RelationExecutionError):
    """A required producer relation is absent."""


class UnsupportedRelationOperation(RelationExecutionError):
    """The requested operation is not implemented."""


# --------------------------------------------------------------------------
# Execution record
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class RelationExecutionRecord:
    relation_id: str
    wave: int
    operation: str
    operand_a: Any
    operand_b: Any
    result: Any
    destinations: tuple[str, ...]



# --------------------------------------------------------------------------
# RMU-integrated executor
# --------------------------------------------------------------------------

class RelationExecutor:
    """
    Execute RelationDependencyGraph objects through the RMU.

    The executor no longer owns separate relation-result,
    relation-frame, or destination-value dictionaries.

    The RMU is authoritative.
    """

    def __init__(
        self,
        rmu: RelationMemoryUnit | None = None,
        *,
        width: int = 8,
    ) -> None:
        if width <= 0:
            raise ValueError(
                "Execution width must be positive."
            )

        self.width = width

        self.rmu = (
            rmu
            if rmu is not None
            else RelationMemoryUnit()
        )

        self.execution_records: list[
            RelationExecutionRecord
        ] = []

    # ------------------------------------------------------------------
    # Compatibility views
    # ------------------------------------------------------------------

    @property
    def relation_frames(
        self,
    ) -> dict[str, RelationFrame]:
        """
        Compatibility view backed by the RMU.
        """

        return self.rmu.frames

    @property
    def relation_results(
        self,
    ) -> dict[str, Any]:
        """
        Derived scalar view of RMU frames.
        """

        return {
            relation_id: frame.VALUE
            for relation_id, frame
            in self.rmu.frames.items()
        }

    @property
    def destination_values(
        self,
    ) -> dict[str, Any]:
        """
        Derived destination view from the RMU.
        """

        values: dict[str, Any] = {}

        for destination, reference in (
            self.rmu.destination_map.items()
        ):
            frame = self.rmu.frames.get(
                reference.producer
            )

            if frame is not None:
                values[destination] = frame.VALUE

        return values

    @property
    def values(
        self,
    ) -> dict[str, Any]:
        """
        Compatibility alias.
        """

        return self.destination_values

    # ------------------------------------------------------------------

    def reset(self) -> None:
        self.rmu.clear()
        self.execution_records.clear()

    # ------------------------------------------------------------------
    # Operand resolution
    # ------------------------------------------------------------------

    def resolve_reference(
        self,
        reference: RelationReference,
    ) -> Any:
        """
        Resolve a symbolic reference through the RMU.
        """

        try:
            frame = self.rmu.fetch(
                reference.producer
            )

        except RelationAbsent as error:
            raise RelationValueAbsent(
                "RELATION_ABSENT: "
                f"{reference.producer} has not produced "
                f"the value required by "
                f"{reference.destination!r}."
            ) from error

        if not frame.VALID:
            raise RelationExecutionError(
                f"Relation {reference.producer} exists "
                "but its frame is invalid."
            )

        return frame.VALUE

    def resolve_operand(
        self,
        operand: Any,
        graph: RelationDependencyGraph,
    ) -> Any:
        """
        Resolve literals directly and symbolic operands through
        graph RelationReferences and the RMU.
        """

        if not isinstance(operand, str):
            return operand

        reference = (
            graph.destination_to_relation.get(
                operand
            )
        )

        if reference is None:
            raise RelationValueAbsent(
                "RELATION_ABSENT: "
                f"no producer relation exists for "
                f"symbolic operand {operand!r}."
            )

        if not isinstance(
            reference,
            RelationReference,
        ):
            raise TypeError(
                "Expected RelationReference for "
                f"{operand!r}; received {reference!r}."
            )

        return self.resolve_reference(
            reference
        )

    # ------------------------------------------------------------------
    # Relation execution
    # ------------------------------------------------------------------

    def execute_relation(
        self,
        relation_id: str,
        wave_number: int,
        graph: RelationDependencyGraph,
    ) -> RelationExecutionRecord:
        node = graph.nodes[
            relation_id
        ]

        relation = node.relation
        request = relation.representative

        operand_a = self.resolve_operand(
            request.a,
            graph,
        )

        operand_b = self.resolve_operand(
            request.b,
            graph,
        )

        result = execute_operation(
            request.op,
            operand_a,
            operand_b,
        )

        frame = build_relation_frame(
            relation_id=relation_id,
            operation=request.op,
            operand_a=operand_a,
            operand_b=operand_b,
            value=result,
            width=self.width,
        )

        destinations = tuple(
            str(destination)
            for destination
            in relation.destinations
        )

        # --------------------------------------------------------------
        # RMU is now the single authoritative store.
        # --------------------------------------------------------------

        self.rmu.store(
            frame,
            destinations,
        )

        # Verify the graph and RMU destination mappings agree.
        for destination in destinations:
            graph_reference = (
                graph.destination_to_relation.get(
                    destination
                )
            )

            rmu_reference = (
                self.rmu.destination_map.get(
                    destination
                )
            )

            if graph_reference is None:
                raise RelationExecutionError(
                    f"Graph has no reference for "
                    f"destination {destination!r}."
                )

            if rmu_reference is None:
                raise RelationExecutionError(
                    f"RMU failed to register "
                    f"destination {destination!r}."
                )

            if (
                graph_reference.producer
                != rmu_reference.producer
            ):
                raise RelationExecutionError(
                    "Producer mismatch for "
                    f"{destination!r}: "
                    f"graph={graph_reference.producer}, "
                    f"rmu={rmu_reference.producer}."
                )

        record = RelationExecutionRecord(
            relation_id=relation_id,
            wave=wave_number,
            operation=normalise_operation(
                request.op
            ),
            operand_a=operand_a,
            operand_b=operand_b,
            result=result,
            destinations=destinations,
        )

        self.execution_records.append(
            record
        )

        return record

    # ------------------------------------------------------------------

    def run(
        self,
        graph: RelationDependencyGraph,
        *,
        reset: bool = True,
        print_report: bool = True,
    ) -> dict[str, Any]:
        """
        Execute every dependency wave.

        Relations in the same wave are independent. This software
        reference model executes them sequentially while preserving
        the wave structure required for future YÀRÁ workers.
        """

        if reset:
            self.reset()

        if print_report:
            print("=" * 72)
            print(
                "IFÁ RMU-INTEGRATED RELATION EXECUTION"
            )
            print("=" * 72)

        for wave_number, wave in enumerate(
            graph.execution_waves
        ):
            if print_report:
                print()
                print(
                    f"WAVE {wave_number}"
                )
                print("-" * 72)

            for relation_id in wave:
                record = self.execute_relation(
                    relation_id,
                    wave_number,
                    graph,
                )

                frame = self.rmu.fetch(
                    relation_id
                )

                if print_report:
                    print(
                        f"{record.relation_id:<4}"
                        f"{record.operation:<8}"
                        f"{record.operand_a} ATI "
                        f"{record.operand_b} = "
                        f"{record.result}"
                    )

                    print(
                        "      RMU frame       "
                        f"-> {frame}"
                    )

                    for destination in (
                        record.destinations
                    ):
                        reference = (
                            self.rmu.destination_map[
                                destination
                            ]
                        )

                        print(
                            "      RMU broadcast   "
                            f"-> {reference} = "
                            f"{frame.VALUE}"
                        )

        if print_report:
            self.print_final_report(
                graph
            )

        return self.destination_values

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def print_final_report(
        self,
        graph: RelationDependencyGraph,
    ) -> None:
        print()
        print("=" * 72)
        print("RMU RELATION FRAMES")
        print("=" * 72)

        for relation_id in sorted(
            self.rmu.frames,
            key=lambda value: int(value[1:]),
        ):
            frame = self.rmu.frames[
                relation_id
            ]

            print(frame)

        print()
        print("=" * 72)
        print("RMU RELATION RESULTS")
        print("=" * 72)

        for relation_id in sorted(
            self.rmu.frames,
            key=lambda value: int(value[1:]),
        ):
            print(
                f"{relation_id:<12}"
                f"{self.rmu.frames[relation_id].VALUE}"
            )

        print()
        print("=" * 72)
        print("RMU DESTINATION VALUES")
        print("=" * 72)

        for destination in sorted(
            self.rmu.destination_map
        ):
            reference = (
                self.rmu.destination_map[
                    destination
                ]
            )

            value = self.rmu.destination_result(
                destination
            )

            print(
                f"{destination:<12}"
                f"{value:<12}"
                f"via {reference}"
            )

        print()
        print("=" * 72)
        print("EXECUTION STATISTICS")
        print("=" * 72)

        print(
            f"Relations executed : "
            f"{len(self.execution_records)}"
        )

        print(
            f"Execution waves    : "
            f"{graph.wave_count}"
        )

        print(
            f"Maximum parallelism: "
            f"{graph.maximum_parallelism}"
        )

        print(
            f"RMU frames         : "
            f"{self.rmu.stats.frames}"
        )

        print(
            f"RMU destinations   : "
            f"{self.rmu.stats.destinations}"
        )

        print(
            f"RMU broadcasts     : "
            f"{self.rmu.stats.broadcasts}"
        )

        print(
            f"RMU fetches        : "
            f"{self.rmu.stats.fetches}"
        )


# --------------------------------------------------------------------------
# Demonstration
# --------------------------------------------------------------------------

if __name__ == "__main__":
    program = [
        ("PAPO", 2, 3, "A"),
        ("YO", 10, 4, "B"),
        ("DAGBA", 5, 6, "C"),

        # Duplicate relation, reused through broadcast.
        ("PAPO", 3, 2, "A_COPY"),

        # Symbolic operands resolve through the RMU.
        ("PAPO", "A", "B", "D"),
        ("YO", "C", 2, "E"),
        ("DAGBA", "D", "E", "F"),
    ]

    graph = build_relation_graph(
        program
    )

    executor = RelationExecutor(
        width=8
    )

    executor.run(
        graph
    )
