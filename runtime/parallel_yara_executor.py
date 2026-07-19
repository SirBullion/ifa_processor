#!/usr/bin/env python3
"""
============================================================================
IFÁ Processor V4.5
Parallel Software YÀRÁ Execution Engine
============================================================================

Execution model:

    Dependency wave
        ↓
    concurrent YÀRÁ workers
        ↓
    RelationFrame construction
        ↓
    synchronized RMU commit
        ↓
    wave barrier
        ↓
    next dependency wave

The sequential RelationExecutor remains the verified golden model.
This module must produce exactly the same frames, values and broadcasts.
"""

from __future__ import annotations

from concurrent.futures import (
    Future,
    ThreadPoolExecutor,
    as_completed,
)
from dataclasses import dataclass
from threading import Lock
from time import perf_counter
from typing import Any

from compiler.relation_graph import (
    RelationDependencyGraph,
    build_relation_graph,
)
from compiler.relation_reference import RelationReference

from runtime.frame_builder import build_relation_frame
from runtime.relation_executor import (
    RelationExecutionError,
    RelationValueAbsent,
    execute_operation,
    normalise_operation,
)
from runtime.relation_frame import RelationFrame
from runtime.relation_memory_unit import (
    RelationAbsent,
    RelationMemoryUnit,
)


class YaraExecutionError(RelationExecutionError):
    """A YÀRÁ worker failed to complete its relation."""


@dataclass(frozen=True, slots=True)
class YaraTask:
    worker_id: int
    wave: int
    relation_id: str
    operation: str
    operand_a: Any
    operand_b: Any
    destinations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class YaraResult:
    worker_id: int
    wave: int
    relation_id: str
    operation: str
    operand_a: Any
    operand_b: Any
    value: Any
    frame: RelationFrame
    destinations: tuple[str, ...]
    elapsed_seconds: float


@dataclass(slots=True)
class ParallelExecutionStatistics:
    waves: int = 0
    relations: int = 0
    worker_tasks: int = 0
    maximum_workers_used: int = 0
    elapsed_seconds: float = 0.0


class ParallelYaraExecutor:
    """
    Execute dependency-independent relations concurrently.

    Workers never write partially constructed frames into the RMU.

    Each worker:
        1. resolves its operands from already completed waves,
        2. computes its scalar result,
        3. constructs and validates a RelationFrame,
        4. returns the completed frame.

    The coordinator commits completed frames into the RMU under a lock.
    """

    def __init__(
        self,
        worker_count: int = 4,
        *,
        width: int = 8,
        rmu: RelationMemoryUnit | None = None,
    ) -> None:
        if worker_count <= 0:
            raise ValueError(
                "YÀRÁ worker count must be positive."
            )

        if width <= 0:
            raise ValueError(
                "Execution width must be positive."
            )

        self.worker_count = worker_count
        self.width = width

        self.rmu = (
            rmu
            if rmu is not None
            else RelationMemoryUnit()
        )

        self._rmu_lock = Lock()

        self.results: list[YaraResult] = []

        self.stats = ParallelExecutionStatistics()

    @property
    def relation_results(self) -> dict[str, Any]:
        return {
            relation_id: frame.VALUE
            for relation_id, frame
            in self.rmu.frames.items()
        }

    @property
    def destination_values(self) -> dict[str, Any]:
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

    def reset(self) -> None:
        self.rmu.clear()
        self.results.clear()
        self.stats = ParallelExecutionStatistics()

    def resolve_reference(
        self,
        reference: RelationReference,
    ) -> Any:
        """
        Resolve a producer from an earlier completed wave.

        No current-wave dependency is permitted by graph construction.
        """

        try:
            frame = self.rmu.fetch(
                reference.producer
            )

        except RelationAbsent as error:
            raise RelationValueAbsent(
                "RELATION_ABSENT: "
                f"{reference.producer} has not produced "
                f"{reference.destination!r}."
            ) from error

        if not frame.VALID:
            raise RelationExecutionError(
                f"Relation {reference.producer} has an invalid frame."
            )

        return frame.VALUE

    def resolve_operand(
        self,
        operand: Any,
        graph: RelationDependencyGraph,
    ) -> Any:
        if not isinstance(operand, str):
            return operand

        reference = graph.destination_to_relation.get(
            operand
        )

        if reference is None:
            raise RelationValueAbsent(
                "RELATION_ABSENT: "
                f"no producer exists for {operand!r}."
            )

        if not isinstance(reference, RelationReference):
            raise TypeError(
                f"Expected RelationReference for {operand!r}; "
                f"received {reference!r}."
            )

        return self.resolve_reference(
            reference
        )

    def prepare_task(
        self,
        worker_id: int,
        wave_number: int,
        relation_id: str,
        graph: RelationDependencyGraph,
    ) -> YaraTask:
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

        destinations = tuple(
            str(destination)
            for destination
            in relation.destinations
        )

        return YaraTask(
            worker_id=worker_id,
            wave=wave_number,
            relation_id=relation_id,
            operation=normalise_operation(
                request.op
            ),
            operand_a=operand_a,
            operand_b=operand_b,
            destinations=destinations,
        )

    def execute_task(
        self,
        task: YaraTask,
    ) -> YaraResult:
        """
        Execute one complete relation inside a YÀRÁ worker.
        """

        started = perf_counter()

        value = execute_operation(
            task.operation,
            task.operand_a,
            task.operand_b,
        )

        frame = build_relation_frame(
            relation_id=task.relation_id,
            operation=task.operation,
            operand_a=task.operand_a,
            operand_b=task.operand_b,
            value=value,
            width=self.width,
        )

        elapsed = perf_counter() - started

        return YaraResult(
            worker_id=task.worker_id,
            wave=task.wave,
            relation_id=task.relation_id,
            operation=task.operation,
            operand_a=task.operand_a,
            operand_b=task.operand_b,
            value=value,
            frame=frame,
            destinations=task.destinations,
            elapsed_seconds=elapsed,
        )

    def commit_result(
        self,
        result: YaraResult,
        graph: RelationDependencyGraph,
    ) -> None:
        """
        Commit one completed frame atomically to the RMU.
        """

        with self._rmu_lock:
            self.rmu.store(
                result.frame,
                result.destinations,
            )

            for destination in result.destinations:
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
                    raise YaraExecutionError(
                        f"Graph reference absent for "
                        f"{destination!r}."
                    )

                if rmu_reference is None:
                    raise YaraExecutionError(
                        f"RMU reference absent for "
                        f"{destination!r}."
                    )

                if (
                    graph_reference.producer
                    != result.relation_id
                ):
                    raise YaraExecutionError(
                        f"Graph maps {destination!r} to "
                        f"{graph_reference.producer}, not "
                        f"{result.relation_id}."
                    )

                if (
                    rmu_reference.producer
                    != result.relation_id
                ):
                    raise YaraExecutionError(
                        f"RMU maps {destination!r} to "
                        f"{rmu_reference.producer}, not "
                        f"{result.relation_id}."
                    )

    def run_wave(
        self,
        wave_number: int,
        relation_ids: list[str],
        graph: RelationDependencyGraph,
        *,
        print_report: bool,
    ) -> list[YaraResult]:
        """
        Execute one graph wave concurrently.

        The method returns only after all workers have completed and all
        resulting frames have been committed to the RMU.
        """

        if not relation_ids:
            return []

        active_workers = min(
            self.worker_count,
            len(relation_ids),
        )

        self.stats.maximum_workers_used = max(
            self.stats.maximum_workers_used,
            active_workers,
        )

        tasks = [
            self.prepare_task(
                worker_id=index % active_workers,
                wave_number=wave_number,
                relation_id=relation_id,
                graph=graph,
            )
            for index, relation_id
            in enumerate(relation_ids)
        ]

        completed: list[YaraResult] = []

        with ThreadPoolExecutor(
            max_workers=active_workers,
            thread_name_prefix="yara",
        ) as pool:
            futures: dict[
                Future[YaraResult],
                YaraTask,
            ] = {
                pool.submit(
                    self.execute_task,
                    task,
                ): task
                for task in tasks
            }

            for future in as_completed(
                futures
            ):
                task = futures[future]

                try:
                    result = future.result()

                except Exception as error:
                    raise YaraExecutionError(
                        f"YÀRÁ {task.worker_id} failed "
                        f"while executing {task.relation_id}."
                    ) from error

                completed.append(
                    result
                )

        # Commit in stable relation order for deterministic reports and RMU
        # insertion order. Computation itself has already occurred in parallel.
        completed.sort(
            key=lambda item: int(
                item.relation_id[1:]
            )
        )

        for result in completed:
            self.commit_result(
                result,
                graph,
            )

            self.results.append(
                result
            )

            if print_report:
                print(
                    f"YÀRÁ {result.worker_id:<2} "
                    f"-> {result.relation_id:<4}"
                    f"{result.operation:<8}"
                    f"{result.operand_a} ATI "
                    f"{result.operand_b} = "
                    f"{result.value}"
                )

                print(
                    "          RMU frame     "
                    f"-> {result.frame}"
                )

                for destination in (
                    result.destinations
                ):
                    reference = (
                        self.rmu.destination_map[
                            destination
                        ]
                    )

                    print(
                        "          broadcast     "
                        f"-> {reference} = "
                        f"{result.value}"
                    )

        self.stats.worker_tasks += len(
            completed
        )

        return completed

    def run(
        self,
        graph: RelationDependencyGraph,
        *,
        reset: bool = True,
        print_report: bool = True,
    ) -> dict[str, Any]:
        if reset:
            self.reset()

        started = perf_counter()

        if print_report:
            print("=" * 76)
            print(
                "IFÁ V4.5 PARALLEL SOFTWARE YÀRÁ EXECUTION"
            )
            print("=" * 76)
            print(
                f"Configured YÀRÁ workers : "
                f"{self.worker_count}"
            )
            print(
                f"Execution waves         : "
                f"{graph.wave_count}"
            )

        for wave_number, relation_ids in enumerate(
            graph.execution_waves
        ):
            if print_report:
                print()
                print(
                    f"WAVE {wave_number} "
                    f"({len(relation_ids)} ready relations)"
                )
                print("-" * 76)

            self.run_wave(
                wave_number,
                relation_ids,
                graph,
                print_report=print_report,
            )

        self.stats.waves = graph.wave_count
        self.stats.relations = len(
            self.results
        )
        self.stats.elapsed_seconds = (
            perf_counter() - started
        )

        if print_report:
            self.print_final_report(
                graph
            )

        return self.destination_values

    def print_final_report(
        self,
        graph: RelationDependencyGraph,
    ) -> None:
        print()
        print("=" * 76)
        print("YÀRÁ EXECUTION RECORDS")
        print("=" * 76)

        for result in sorted(
            self.results,
            key=lambda item: int(
                item.relation_id[1:]
            ),
        ):
            print(
                f"{result.relation_id:<4}"
                f" wave={result.wave:<2}"
                f" yara={result.worker_id:<2}"
                f" value={result.value:<8}"
                f" elapsed={result.elapsed_seconds:.8f}s"
            )

        print()
        print("=" * 76)
        print("RMU DESTINATION VALUES")
        print("=" * 76)

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
        print("=" * 76)
        print("PARALLEL EXECUTION STATISTICS")
        print("=" * 76)

        print(
            f"Relations executed      : "
            f"{self.stats.relations}"
        )

        print(
            f"Execution waves         : "
            f"{self.stats.waves}"
        )

        print(
            f"Configured workers      : "
            f"{self.worker_count}"
        )

        print(
            f"Maximum workers used    : "
            f"{self.stats.maximum_workers_used}"
        )

        print(
            f"Worker tasks completed  : "
            f"{self.stats.worker_tasks}"
        )

        print(
            f"RMU frames              : "
            f"{self.rmu.stats.frames}"
        )

        print(
            f"RMU broadcasts          : "
            f"{self.rmu.stats.broadcasts}"
        )

        print(
            f"RMU fetches             : "
            f"{self.rmu.stats.fetches}"
        )

        print(
            f"Elapsed software time   : "
            f"{self.stats.elapsed_seconds:.8f}s"
        )


if __name__ == "__main__":
    program = [
        ("PAPO", 2, 3, "A"),
        ("YO", 10, 4, "B"),
        ("DAGBA", 5, 6, "C"),
        ("PAPO", 3, 2, "A_COPY"),
        ("PAPO", "A", "B", "D"),
        ("YO", "C", 2, "E"),
        ("DAGBA", "D", "E", "F"),
    ]

    graph = build_relation_graph(
        program
    )

    executor = ParallelYaraExecutor(
        worker_count=3,
        width=8,
    )

    executor.run(
        graph
    )
