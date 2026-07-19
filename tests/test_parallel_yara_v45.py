#!/usr/bin/env python3
"""
IFÁ Processor V4.5
Parallel YÀRÁ Equivalence Tests
"""

from __future__ import annotations

import unittest

from compiler.relation_graph import build_relation_graph
from runtime.parallel_yara_executor import (
    ParallelYaraExecutor,
)
from runtime.relation_executor import RelationExecutor


PROGRAM = [
    ("PAPO", 2, 3, "A"),
    ("YO", 10, 4, "B"),
    ("DAGBA", 5, 6, "C"),
    ("PAPO", 3, 2, "A_COPY"),
    ("PAPO", "A", "B", "D"),
    ("YO", "C", 2, "E"),
    ("DAGBA", "D", "E", "F"),
]


class TestParallelYaraExecution(unittest.TestCase):

    def setUp(self):
        self.graph = build_relation_graph(
            PROGRAM
        )

        self.sequential = RelationExecutor(
            width=8
        )

        self.parallel = ParallelYaraExecutor(
            worker_count=3,
            width=8,
        )

        self.sequential_values = (
            self.sequential.run(
                self.graph,
                print_report=False,
            )
        )

        self.parallel_values = (
            self.parallel.run(
                self.graph,
                print_report=False,
            )
        )

    def test_destination_values_match(self):
        self.assertEqual(
            self.parallel_values,
            self.sequential_values,
        )

    def test_relation_results_match(self):
        self.assertEqual(
            self.parallel.relation_results,
            self.sequential.relation_results,
        )

    def test_relation_frames_match(self):
        self.assertEqual(
            self.parallel.rmu.frames,
            self.sequential.rmu.frames,
        )

    def test_destination_references_match(self):
        self.assertEqual(
            self.parallel.rmu.destination_map,
            self.sequential.rmu.destination_map,
        )

    def test_every_relation_executes_once(self):
        relation_ids = [
            result.relation_id
            for result in self.parallel.results
        ]

        self.assertEqual(
            len(relation_ids),
            6,
        )

        self.assertEqual(
            len(set(relation_ids)),
            6,
        )

    def test_worker_count_used(self):
        self.assertEqual(
            self.parallel.stats.maximum_workers_used,
            3,
        )

    def test_wave_assignments(self):
        relation_waves = {
            result.relation_id: result.wave
            for result in self.parallel.results
        }

        self.assertEqual(
            relation_waves,
            {
                "R0": 0,
                "R1": 0,
                "R2": 0,
                "R3": 1,
                "R4": 1,
                "R5": 2,
            },
        )

    def test_rmu_counts(self):
        self.assertEqual(
            self.parallel.rmu.stats.frames,
            6,
        )

        self.assertEqual(
            self.parallel.rmu.stats.destinations,
            7,
        )

        self.assertEqual(
            self.parallel.rmu.stats.broadcasts,
            7,
        )

    def test_single_worker_mode_matches(self):
        executor = ParallelYaraExecutor(
            worker_count=1,
            width=8,
        )

        values = executor.run(
            self.graph,
            print_report=False,
        )

        self.assertEqual(
            values,
            self.sequential_values,
        )

        self.assertEqual(
            executor.rmu.frames,
            self.sequential.rmu.frames,
        )

    def test_excess_worker_mode_matches(self):
        executor = ParallelYaraExecutor(
            worker_count=16,
            width=8,
        )

        values = executor.run(
            self.graph,
            print_report=False,
        )

        self.assertEqual(
            values,
            self.sequential_values,
        )

        self.assertEqual(
            executor.stats.maximum_workers_used,
            3,
        )


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )
