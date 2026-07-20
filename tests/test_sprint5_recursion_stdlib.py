import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from backends.python.backend import python_backend
from interpreter.environment import environment
from interpreter.interpreter import interpreter
from parser.parser import parser
from runtime.backend_manager import backend_manager


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class RecordingBackend:

    def __init__(self):
        self.operators = []

    def execute(self, request):
        self.operators.append(request.operator_name)
        return python_backend.execute(request)


class Sprint5RecursionTests(unittest.TestCase):

    def setUp(self):
        interpreter.reset()
        backend_manager.use("python")

    def tearDown(self):
        backend_manager.use("python")
        interpreter.reset()

    def execute(self, source):
        return interpreter.visit(parser.parse_program(source))

    def test_recursive_factorial(self):
        recording = RecordingBackend()
        backend_manager.register("recursive-recording", recording)
        backend_manager.use("recursive-recording")

        result = self.execute(
            """ISE FACTORIAL(N)
            BI N <= 1
                RETURN 1
            TABI
                RETURN DAGBA N ATI FACTORIAL(YO N ATI 1)
            PARI
            PARI
            FACTORIAL(6)"""
        )

        self.assertEqual(result, 720)
        self.assertEqual(recording.operators.count("DAGBA"), 5)
        self.assertEqual(recording.operators.count("YO"), 5)
        self.assertEqual(environment.call_stack, [])

    def test_recursive_fibonacci(self):
        result = self.execute(
            """ISE FIBONACCI(N)
            BI N <= 1
                RETURN N
            TABI
                RETURN PAPO FIBONACCI(YO N ATI 1) ATI FIBONACCI(YO N ATI 2)
            PARI
            PARI
            FIBONACCI(10)"""
        )

        self.assertEqual(result, 55)
        self.assertEqual(environment.call_stack, [])

    def test_recursive_frames_do_not_leak_caller_locals(self):
        with self.assertRaisesRegex(NameError, "SECRET"):
            self.execute(
                """ISE INNER(N)
                BI N == 0
                    RETURN SECRET
                PARI
                RETURN INNER(YO N ATI 1)
                PARI
                ISE OUTER(N)
                JE KI SECRET = 99
                RETURN INNER(N)
                PARI
                OUTER(1)"""
            )

        self.assertEqual(environment.call_stack, [])

    def test_tower_of_hanoi(self):
        output = io.StringIO()

        with redirect_stdout(output):
            self.execute(
                """ISE HANOI(N, SOURCE, TARGET, AUXILIARY)
                BI N <= 0
                    RETURN 0
                PARI
                HANOI(YO N ATI 1, SOURCE, AUXILIARY, TARGET)
                PRINT("MOVE", N, "FROM", SOURCE, "TO", TARGET)
                HANOI(YO N ATI 1, AUXILIARY, TARGET, SOURCE)
                RETURN 0
                PARI
                HANOI(3, "A", "C", "B")"""
            )

        moves = output.getvalue().strip().splitlines()
        self.assertEqual(len(moves), 7)
        self.assertEqual(moves[0], "MOVE 1 FROM A TO C")
        self.assertEqual(moves[-1], "MOVE 1 FROM A TO C")


class Sprint5StandardLibraryTests(unittest.TestCase):

    def setUp(self):
        interpreter.reset()
        backend_manager.use("python")

    def tearDown(self):
        interpreter.reset()

    def execute(self, source):
        return interpreter.visit(parser.parse_program(source))

    def test_arrays_indexing_and_assignment(self):
        result = self.execute(
            """JE KI A = [1, 2, 3]
            A[1] = 99
            JE KI FIRST = A[0]
            JE KI LAST = A[2]
            A"""
        )

        self.assertEqual(result, [1, 99, 3])
        self.assertEqual(environment.get("FIRST"), 1)
        self.assertEqual(environment.get("LAST"), 3)

    def test_print_and_conversion_builtins(self):
        output = io.StringIO()

        with redirect_stdout(output):
            result = self.execute(
                """JE KI A = [1, 2, 3]
                PRINT(LEN(A))
                PRINT(TYPE(A))
                PRINT(INT("12"))
                PRINT(FLOAT("2.5"))
                STRING(42)"""
            )

        self.assertEqual(output.getvalue().splitlines(), ["3", "LIST", "12", "2.5"])
        self.assertEqual(result, "42")

    def test_input_builtin(self):
        with patch("builtins.input", return_value="17"):
            self.assertEqual(self.execute("INT(INPUT())"), 17)

    def test_for_loop_is_inclusive(self):
        result = self.execute(
            """JE KI TOTAL = 0
            FUN I LATI 1 SI 10
                JE KI TOTAL = PAPO TOTAL ATI I
            PARI
            TOTAL"""
        )

        self.assertEqual(result, 55)

    def test_foreach_loop(self):
        result = self.execute(
            """JE KI TOTAL = 0
            JE KI VALUES = [2, 4, 6]
            FUN ITEM NINU VALUES
                JE KI TOTAL = PAPO TOTAL ATI ITEM
            PARI
            TOTAL"""
        )

        self.assertEqual(result, 12)

    def test_example_programs_parse_and_execute(self):
        expected_output = {
            "factorial.ifa": "720",
            "fibonacci.ifa": "55",
            "sorting.ifa": "[1, 2, 3, 4, 5]",
            "matrix_add.ifa": "[[6, 8], [10, 12]]",
        }

        for filename, expected in expected_output.items():
            with self.subTest(filename=filename):
                interpreter.reset()
                source = (PROJECT_ROOT / "examples" / filename).read_text(
                    encoding="utf-8"
                )
                output = io.StringIO()

                with redirect_stdout(output):
                    interpreter.visit(parser.parse_program(source))

                self.assertEqual(output.getvalue().strip(), expected)

    def test_tower_of_hanoi_example_program(self):
        source = (
            PROJECT_ROOT / "examples" / "tower_of_hanoi.ifa"
        ).read_text(encoding="utf-8")
        output = io.StringIO()

        with redirect_stdout(output):
            interpreter.visit(parser.parse_program(source))

        moves = output.getvalue().strip().splitlines()
        self.assertEqual(len(moves), 7)
        self.assertEqual(moves[3], "MOVE 3 FROM A TO C")


if __name__ == "__main__":
    unittest.main()
