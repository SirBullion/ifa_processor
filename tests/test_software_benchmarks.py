import unittest
from pathlib import Path

from interpreter.interpreter import interpreter
from parser.parser import parser
from runtime.backend_manager import backend_manager


ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS = ROOT / "benchmarks" / "software"


class SoftwareBenchmarkTests(unittest.TestCase):
    EXPECTED = {
        "factorial.ifa": 40320,
        "fibonacci.ifa": 144,
        "tower_of_hanoi.ifa": 255,
        "sorting.ifa": [1,2,3,4,5,6,7,8,9],
        "matrix_arithmetic.ifa": [[6,8],[10,12]],
        "search.ifa": 4,
        "array_operations.ifa": [1,2,15,4,5],
        "recursive_stress.ifa": 64,
    }

    def setUp(self):
        interpreter.reset(); backend_manager.use("python")

    def test_algorithm_benchmarks(self):
        for filename, expected in self.EXPECTED.items():
            with self.subTest(filename=filename):
                interpreter.reset()
                path = BENCHMARKS / filename
                ast = parser.parse_program(path.read_text(encoding="utf-8"), source_name=str(path))
                self.assertEqual(interpreter.execute(ast), expected)

    def test_stress_benchmarks_execute(self):
        for filename in ("relation_arithmetic.ifa", "transport_stress.ifa"):
            with self.subTest(filename=filename):
                interpreter.reset()
                path = BENCHMARKS / filename
                ast = parser.parse_program(path.read_text(encoding="utf-8"), source_name=str(path))
                self.assertIsNotNone(interpreter.execute(ast))


if __name__ == "__main__": unittest.main()
