#!/usr/bin/env python3
"""
IFÁ Processor V4.5
Relation Scheduler

Schedules relation graph execution into parallel waves.

Current version:
    • Simulates parallel execution
    • One worker per relation
    • Reports scheduling

Future versions:
    • Real YÀRÁ workers
    • RMU integration
    • Dynamic load balancing
"""

from dataclasses import dataclass, field

from compiler.relation_graph import (
    build_relation_graph,
)


@dataclass
class Worker:

    worker_id: int

    current_relation: str | None = None

    busy: bool = False


class RelationScheduler:

    def __init__(self, workers=4):

        self.workers = [
            Worker(i)
            for i in range(workers)
        ]

    def schedule(self, graph):

        print("="*72)
        print("IFÁ PROCESSOR V4.5 RELATION SCHEDULER")
        print("="*72)

        for wave_number, wave in enumerate(graph.execution_waves):

            print()
            print(f"WAVE {wave_number}")
            print("-"*72)

            for worker in self.workers:
                worker.busy = False
                worker.current_relation = None

            for relation, worker in zip(wave, self.workers):

                worker.busy = True
                worker.current_relation = relation

                node = graph.nodes[relation]

                req = node.relation.representative

                print(
                    f"Worker {worker.worker_id} "
                    f"→ {relation} : "
                    f"{req.op} {req.a} ATI {req.b}"
                )

            print()

            print("Executing...")

            print("Completed.")

        print()
        print("="*72)
        print("Scheduling complete.")
        print("="*72)


if __name__ == "__main__":

    program = [

        ("PAPO",2,3,"A"),
        ("YO",10,4,"B"),
        ("DAGBA",5,6,"C"),

        ("PAPO","A","B","D"),

        ("YO","C",2,"E"),

        ("DAGBA","D","E","F"),

    ]

    graph = build_relation_graph(program)

    scheduler = RelationScheduler(
        workers=4
    )

    scheduler.schedule(graph)
