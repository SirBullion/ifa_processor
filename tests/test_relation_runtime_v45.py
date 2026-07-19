#!/usr/bin/env python3
"""
============================================================================
IFÁ Processor V4.5
Relation Runtime Verification Suite
============================================================================

Verifies:

1. Φ-P8 integration
2. Relation-frame equations
3. Relation-frame partition invariants
4. Transport and state semantics
5. RMU storage and destination lookup
6. Relation deduplication
7. Dependency graph correctness
8. Execution-wave independence
9. End-to-end runtime execution
10. Broadcast reuse
"""

from __future__ import annotations

import unittest
from itertools import combinations

from compiler.phi_p8_adapter import (
    backend_description,
    phi_p8,
)
from compiler.relation_deduplicator import (
    deduplicate_relations,
)
from compiler.relation_graph import (
    build_relation_graph,
)
from compiler.relation_reference import (
    RelationReference,
)
from runtime.frame_builder import (
    build_relation_frame,
)
from runtime.relation_executor import (
    RelationExecutor,
    execute_operation,
)
from runtime.relation_memory_unit import (
    DuplicateRelation,
    RelationAbsent,
    RelationMemoryUnit,
)


class TestPhiP8Integration(unittest.TestCase):

    def test_real_backend_is_loaded(self):
        description = backend_description()

        self.assertEqual(
            description,
            "python.v5.ifa_phi_p8:phi_p8",
        )

    def test_phi_p8_all_bytes(self):
        outputs = []

        for value in range(256):
            transformed = phi_p8(value)

            self.assertIsInstance(
                transformed,
                tuple,
            )

            self.assertEqual(
                len(transformed),
                8,
            )

            self.assertTrue(
                all(bit in (0, 1) for bit in transformed)
            )

            outputs.append(transformed)

        self.assertEqual(
            len(set(outputs)),
            256,
            "Φ-P8 must remain injective over all byte values.",
        )


class TestRelationFrameExhaustive(unittest.TestCase):

    def test_all_65536_operand_pairs(self):
        """
        Exhaustively verify every 8-bit operand pair.
        """

        mask = 0xFF

        tested = 0

        for a in range(256):
            for b in range(256):
                raw_value = a + b

                frame = build_relation_frame(
                    relation_id="RTEST",
                    operation="PAPO",
                    operand_a=a,
                    operand_b=b,
                    value=raw_value,
                    width=8,
                )

                expected_ra = a & b
                expected_rd = a ^ b
                expected_r0 = (~(a | b)) & mask
                expected_y = raw_value & mask
                expected_t = int(raw_value > mask)

                self.assertEqual(
                    frame.RA,
                    expected_ra,
                )

                self.assertEqual(
                    frame.RD,
                    expected_rd,
                )

                self.assertEqual(
                    frame.R0,
                    expected_r0,
                )

                self.assertEqual(
                    frame.Y,
                    expected_y,
                )

                self.assertEqual(
                    frame.T,
                    expected_t,
                )

                self.assertEqual(
                    frame.STATE,
                    expected_t,
                )

                self.assertTrue(
                    frame.partition_is_complete
                )

                self.assertTrue(
                    frame.channels_are_disjoint
                )

                self.assertEqual(
                    frame.RA | frame.RD | frame.R0,
                    mask,
                )

                self.assertEqual(
                    frame.RA & frame.RD,
                    0,
                )

                self.assertEqual(
                    frame.RA & frame.R0,
                    0,
                )

                self.assertEqual(
                    frame.RD & frame.R0,
                    0,
                )

                self.assertEqual(
                    frame.VALUE,
                    raw_value,
                )

                self.assertTrue(
                    frame.VALID
                )

                tested += 1

        self.assertEqual(
            tested,
            65_536,
        )

    def test_negative_result_transport(self):
        frame = build_relation_frame(
            relation_id="RNEG",
            operation="YO",
            operand_a=2,
            operand_b=3,
            value=-1,
            width=8,
        )

        self.assertEqual(
            frame.VALUE,
            -1,
        )

        self.assertEqual(
            frame.Y,
            0xFF,
        )

        self.assertEqual(
            frame.T,
            1,
        )

        self.assertEqual(
            frame.STATE,
            1,
        )

    def test_comparison_partition(self):
        examples = [
            (5, 5, 1, 0, 0),
            (8, 2, 0, 1, 0),
            (2, 8, 0, 0, 1),
        ]

        for a, b, eq, gt, lt in examples:
            frame = build_relation_frame(
                relation_id="RCMP",
                operation="SEDA",
                operand_a=a,
                operand_b=b,
                value=int(a == b),
                width=8,
            )

            self.assertEqual(
                frame.EQ,
                eq,
            )

            self.assertEqual(
                frame.GT,
                gt,
            )

            self.assertEqual(
                frame.LT,
                lt,
            )

            self.assertEqual(
                frame.EQ + frame.GT + frame.LT,
                1,
            )


class TestNativeOperations(unittest.TestCase):

    def test_arithmetic_operations(self):
        self.assertEqual(
            execute_operation("PAPO", 7, 4),
            11,
        )

        self.assertEqual(
            execute_operation("YO", 7, 4),
            3,
        )

        self.assertEqual(
            execute_operation("DAGBA", 7, 4),
            28,
        )

        self.assertEqual(
            execute_operation("PIN", 8, 4),
            2,
        )

        self.assertEqual(
            execute_operation("KU", 9, 4),
            1,
        )

        self.assertEqual(
            execute_operation("GBE", 2, 4),
            16,
        )

    def test_comparison_operations(self):
        self.assertEqual(
            execute_operation("SEDA", 5, 5),
            1,
        )

        self.assertEqual(
            execute_operation("SEDA", 5, 6),
            0,
        )

        self.assertEqual(
            execute_operation("JU", 8, 2),
            1,
        )

        self.assertEqual(
            execute_operation("JU", 2, 8),
            0,
        )

        self.assertEqual(
            execute_operation("KERE", 2, 8),
            1,
        )

        self.assertEqual(
            execute_operation("KERE", 8, 2),
            0,
        )

    def test_diacritic_aliases(self):
        self.assertEqual(
            execute_operation("DÁGBA", 3, 4),
            12,
        )

        self.assertEqual(
            execute_operation("KÙ", 10, 3),
            1,
        )

        self.assertEqual(
            execute_operation("GBÉ", 2, 3),
            8,
        )

        self.assertEqual(
            execute_operation("KERÉ", 2, 3),
            1,
        )


class TestRelationMemoryUnit(unittest.TestCase):

    def setUp(self):
        self.rmu = RelationMemoryUnit()

        self.frame = build_relation_frame(
            relation_id="R0",
            operation="PAPO",
            operand_a=2,
            operand_b=3,
            value=5,
            width=8,
        )

    def test_store_and_fetch_by_relation(self):
        self.rmu.store(
            self.frame,
            ["A"],
        )

        fetched = self.rmu.fetch(
            "R0"
        )

        self.assertIs(
            fetched,
            self.frame,
        )

        self.assertEqual(
            fetched.VALUE,
            5,
        )

    def test_fetch_by_destination(self):
        self.rmu.store(
            self.frame,
            [
                "A",
                "A_COPY",
            ],
        )

        frame_a = self.rmu.fetch_by_destination(
            "A"
        )

        frame_copy = self.rmu.fetch_by_destination(
            "A_COPY"
        )

        self.assertIs(
            frame_a,
            self.frame,
        )

        self.assertIs(
            frame_copy,
            self.frame,
        )

        self.assertEqual(
            self.rmu.destination_result("A"),
            5,
        )

        self.assertEqual(
            self.rmu.destination_result("A_COPY"),
            5,
        )

    def test_destination_references(self):
        self.rmu.store(
            self.frame,
            [
                "A",
                "A_COPY",
            ],
        )

        self.assertEqual(
            self.rmu.destination_map["A"],
            RelationReference(
                producer="R0",
                destination="A",
            ),
        )

        self.assertEqual(
            self.rmu.destination_map["A_COPY"],
            RelationReference(
                producer="R0",
                destination="A_COPY",
            ),
        )

    def test_duplicate_relation_rejected(self):
        self.rmu.store(
            self.frame,
            ["A"],
        )

        with self.assertRaises(
            DuplicateRelation
        ):
            self.rmu.store(
                self.frame,
                ["B"],
            )

    def test_missing_relation_rejected(self):
        with self.assertRaises(
            RelationAbsent
        ):
            self.rmu.fetch(
                "R404"
            )

    def test_statistics(self):
        self.rmu.store(
            self.frame,
            [
                "A",
                "A_COPY",
            ],
        )

        self.rmu.fetch(
            "R0"
        )

        self.rmu.fetch_by_destination(
            "A"
        )

        summary = self.rmu.summary()

        self.assertEqual(
            summary["frames"],
            1,
        )

        self.assertEqual(
            summary["destinations"],
            2,
        )

        self.assertEqual(
            summary["broadcasts"],
            2,
        )

        self.assertEqual(
            summary["fetches"],
            2,
        )


class TestRelationDeduplication(unittest.TestCase):

    def test_commutative_relations_are_reused(self):
        program = [
            ("PAPO", 2, 3, "A"),
            ("PAPO", 3, 2, "A_COPY"),
            ("DAGBA", 5, 6, "B"),
            ("DAGBA", 6, 5, "B_COPY"),
        ]

        result = deduplicate_relations(
            program
        )

        self.assertEqual(
            len(result.requests),
            4,
        )

        self.assertEqual(
            len(result.relations),
            2,
        )

        self.assertEqual(
            result.request_to_relation[0],
            result.request_to_relation[1],
        )

        self.assertEqual(
            result.request_to_relation[2],
            result.request_to_relation[3],
        )

    def test_noncommutative_relations_remain_distinct(self):
        program = [
            ("YO", 8, 3, "A"),
            ("YO", 3, 8, "B"),
        ]

        result = deduplicate_relations(
            program
        )

        self.assertEqual(
            len(result.relations),
            2,
        )

        self.assertNotEqual(
            result.request_to_relation[0],
            result.request_to_relation[1],
        )


class TestDependencyGraph(unittest.TestCase):

    def setUp(self):
        self.program = [
            ("PAPO", 2, 3, "A"),
            ("YO", 10, 4, "B"),
            ("DAGBA", 5, 6, "C"),
            ("PAPO", 3, 2, "A_COPY"),
            ("PAPO", "A", "B", "D"),
            ("YO", "C", 2, "E"),
            ("DAGBA", "D", "E", "F"),
        ]

        self.graph = build_relation_graph(
            self.program
        )

    def test_graph_counts(self):
        self.assertEqual(
            self.graph.relation_count,
            6,
        )

        self.assertEqual(
            self.graph.wave_count,
            3,
        )

        self.assertEqual(
            self.graph.maximum_parallelism,
            3,
        )

    def test_destination_references(self):
        expected = {
            "A": ("R0", "A"),
            "A_COPY": ("R0", "A_COPY"),
            "B": ("R1", "B"),
            "C": ("R2", "C"),
            "D": ("R3", "D"),
            "E": ("R4", "E"),
            "F": ("R5", "F"),
        }

        for destination, (
            producer,
            expected_destination,
        ) in expected.items():
            reference = (
                self.graph.destination_to_relation[
                    destination
                ]
            )

            self.assertEqual(
                reference.producer,
                producer,
            )

            self.assertEqual(
                reference.destination,
                expected_destination,
            )

    def test_dependencies(self):
        self.assertEqual(
            self.graph.nodes["R0"].dependencies,
            set(),
        )

        self.assertEqual(
            self.graph.nodes["R1"].dependencies,
            set(),
        )

        self.assertEqual(
            self.graph.nodes["R2"].dependencies,
            set(),
        )

        self.assertEqual(
            self.graph.nodes["R3"].dependencies,
            {
                "R0",
                "R1",
            },
        )

        self.assertEqual(
            self.graph.nodes["R4"].dependencies,
            {
                "R2",
            },
        )

        self.assertEqual(
            self.graph.nodes["R5"].dependencies,
            {
                "R3",
                "R4",
            },
        )

    def test_execution_waves(self):
        self.assertEqual(
            self.graph.execution_waves,
            [
                [
                    "R0",
                    "R1",
                    "R2",
                ],
                [
                    "R3",
                    "R4",
                ],
                [
                    "R5",
                ],
            ],
        )

    def test_no_dependency_inside_same_wave(self):
        for wave in self.graph.execution_waves:
            wave_set = set(wave)

            for relation_id in wave:
                dependencies = (
                    self.graph.nodes[
                        relation_id
                    ].dependencies
                )

                self.assertTrue(
                    dependencies.isdisjoint(
                        wave_set
                    ),
                    (
                        f"{relation_id} has a dependency "
                        "inside its own wave."
                    ),
                )

    def test_all_dependencies_are_in_earlier_waves(self):
        wave_of = {}

        for wave_index, wave in enumerate(
            self.graph.execution_waves
        ):
            for relation_id in wave:
                wave_of[relation_id] = wave_index

        for relation_id, node in (
            self.graph.nodes.items()
        ):
            for dependency_id in (
                node.dependencies
            ):
                self.assertLess(
                    wave_of[dependency_id],
                    wave_of[relation_id],
                )

    def test_relations_within_wave_are_independent(self):
        for wave in self.graph.execution_waves:
            for left, right in combinations(
                wave,
                2,
            ):
                left_node = self.graph.nodes[
                    left
                ]

                right_node = self.graph.nodes[
                    right
                ]

                self.assertNotIn(
                    left,
                    right_node.dependencies,
                )

                self.assertNotIn(
                    right,
                    left_node.dependencies,
                )


class TestEndToEndExecution(unittest.TestCase):

    def setUp(self):
        self.program = [
            ("PAPO", 2, 3, "A"),
            ("YO", 10, 4, "B"),
            ("DAGBA", 5, 6, "C"),
            ("PAPO", 3, 2, "A_COPY"),
            ("PAPO", "A", "B", "D"),
            ("YO", "C", 2, "E"),
            ("DAGBA", "D", "E", "F"),
        ]

        self.graph = build_relation_graph(
            self.program
        )

        self.executor = RelationExecutor(
            width=8
        )

        self.result = self.executor.run(
            self.graph,
            print_report=False,
        )

    def test_final_values(self):
        expected = {
            "A": 5,
            "A_COPY": 5,
            "B": 6,
            "C": 30,
            "D": 11,
            "E": 28,
            "F": 308,
        }

        self.assertEqual(
            self.result,
            expected,
        )

    def test_relation_results(self):
        expected = {
            "R0": 5,
            "R1": 6,
            "R2": 30,
            "R3": 11,
            "R4": 28,
            "R5": 308,
        }

        self.assertEqual(
            self.executor.relation_results,
            expected,
        )

    def test_one_frame_per_unique_relation(self):
        self.assertEqual(
            len(self.executor.rmu.frames),
            6,
        )

        self.assertEqual(
            len(self.executor.execution_records),
            6,
        )

    def test_duplicate_relation_broadcast(self):
        self.assertEqual(
            self.executor.rmu.destination_map[
                "A"
            ].producer,
            "R0",
        )

        self.assertEqual(
            self.executor.rmu.destination_map[
                "A_COPY"
            ].producer,
            "R0",
        )

        self.assertEqual(
            self.executor.rmu.destination_result(
                "A"
            ),
            5,
        )

        self.assertEqual(
            self.executor.rmu.destination_result(
                "A_COPY"
            ),
            5,
        )

    def test_every_frame_matches_operation(self):
        for record in (
            self.executor.execution_records
        ):
            frame = self.executor.rmu.frames[
                record.relation_id
            ]

            expected = execute_operation(
                record.operation,
                record.operand_a,
                record.operand_b,
            )

            self.assertEqual(
                frame.VALUE,
                expected,
            )

            self.assertEqual(
                frame.Y,
                int(expected) & 0xFF,
            )

            self.assertEqual(
                frame.STATE,
                frame.T,
            )

            self.assertTrue(
                frame.VALID
            )

    def test_transport_on_final_multiplication(self):
        frame = self.executor.rmu.fetch(
            "R5"
        )

        self.assertEqual(
            frame.VALUE,
            308,
        )

        self.assertEqual(
            frame.Y,
            52,
        )

        self.assertEqual(
            frame.Y,
            0x34,
        )

        self.assertEqual(
            frame.T,
            1,
        )

        self.assertEqual(
            frame.STATE,
            1,
        )

    def test_rmu_statistics(self):
        self.assertEqual(
            self.executor.rmu.stats.frames,
            6,
        )

        self.assertEqual(
            self.executor.rmu.stats.destinations,
            7,
        )

        self.assertEqual(
            self.executor.rmu.stats.broadcasts,
            7,
        )


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )
