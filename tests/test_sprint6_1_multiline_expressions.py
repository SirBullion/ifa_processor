import io
import unittest
from contextlib import redirect_stdout

from interpreter.environment import environment
from interpreter.interpreter import interpreter
from parser.parser import parser
from runtime.backend_manager import backend_manager


class Sprint61MultilineExpressionTests(unittest.TestCase):

    def setUp(self):
        interpreter.reset()
        backend_manager.use("python")

    def tearDown(self):
        backend_manager.use("python")
        interpreter.reset()

    def execute(self, source):
        return interpreter.execute(parser.parse_program(source))

    def test_deeply_nested_multiline_function_calls(self):
        output = io.StringIO()
        source = """ISE DOUBLE(X)
            RETURN DAGBA X ATI 2
        PARI
        ISE INC(X)
            RETURN PAPO X ATI 1
        PARI
        PRINT(
            PE DOUBLE(
                PE INC(
                    PE DOUBLE(5)
                )
            )
        )"""

        with redirect_stdout(output):
            self.execute(source)

        self.assertEqual(output.getvalue().strip(), "22")

    def test_multiline_nested_arithmetic(self):
        output = io.StringIO()
        source = """PRINT(

            YO(

                DAGBA(

                    PAPO 2 ATI 3

                )

                ATI

                PIN 20 ATI 5

            )

        )"""

        with redirect_stdout(output):
            self.execute(source)

        self.assertEqual(output.getvalue().strip(), "1")

    def test_multiline_assignment_expression(self):
        output = io.StringIO()
        source = """JE KI A =
            PAPO
            10
            ATI
            20

        PRINT(A)"""

        with redirect_stdout(output):
            self.execute(source)

        self.assertEqual(environment.get("A"), 30)
        self.assertEqual(output.getvalue().strip(), "30")

    def test_multiline_return_expression(self):
        source = """ISE ADD(A, B)
            RETURN
            PAPO
            A
            ATI
            B
        PARI
        ADD(8, 9)"""

        self.assertEqual(self.execute(source), 17)

    def test_multiline_recursive_return_call(self):
        source = """ISE FACT(N)
            BI N <= 1
                RETURN 1
            PARI
            RETURN
            DAGBA N ATI
            PE FACT(
                YO
                N
                ATI
                1
            )
        PARI
        FACT(5)"""

        self.assertEqual(self.execute(source), 120)

    def test_multiline_array_index(self):
        source = """JE KI I = 0
        JE KI A = [10, 20, 30]
        A[
            PAPO
            I
            ATI
            1
        ]"""

        self.assertEqual(self.execute(source), 20)

    def test_nested_arrays_across_lines(self):
        source = """JE KI MATRIX = [
            [
                1,
                2
            ],
            [
                3,
                4
            ]
        ]
        MATRIX[
            1
        ][
            0
        ]"""

        self.assertEqual(self.execute(source), 3)

    def test_multiple_multiline_function_arguments(self):
        source = """ISE ADD(A, B)
            RETURN PAPO A ATI B
        PARI
        ADD(
            PAPO
            1
            ATI
            2,
            DAGBA
            3
            ATI
            4
        )"""

        self.assertEqual(self.execute(source), 15)

    def test_one_line_syntax_remains_compatible(self):
        self.assertEqual(self.execute("PAPO 2 ATI 3"), 5)


if __name__ == "__main__":
    unittest.main()
