import unittest

from interpreter.interpreter import interpreter
from parser.parser import parser
from runtime.backend_manager import backend_manager


class Sprint62MultilineComparisonTests(unittest.TestCase):

    def setUp(self):
        interpreter.reset()
        backend_manager.use("python")

    def tearDown(self):
        backend_manager.use("python")
        interpreter.reset()

    def execute(self, source):
        return interpreter.execute(parser.parse_program(source))

    def assert_condition(self, condition, expected=1, setup=""):
        source = f"""{setup}
        JE KI RESULT = 0
        BI
        {condition}
            JE KI RESULT = 1
        PARI
        RESULT"""
        self.assertEqual(self.execute(source), expected)

    def test_multiline_greater_than(self):
        self.assert_condition(
            """A
            >
            5""",
            setup="JE KI A = 6",
        )

    def test_multiline_less_than(self):
        self.assert_condition(
            """A
            <
            5""",
            setup="JE KI A = 4",
        )

    def test_multiline_equal(self):
        self.assert_condition(
            """A
            ==
            5""",
            setup="JE KI A = 5",
        )

    def test_multiline_greater_than_or_equal(self):
        self.assert_condition(
            """A
            >=
            5""",
            setup="JE KI A = 5",
        )

    def test_multiline_less_than_or_equal(self):
        self.assert_condition(
            """A
            <=
            5""",
            setup="JE KI A = 5",
        )

    def test_multiline_not_equal(self):
        self.assert_condition(
            """A
            !=
            5""",
            setup="JE KI A = 6",
        )

    def test_arithmetic_expressions_inside_comparison(self):
        self.assert_condition(
            """PAPO
            A
            ATI
            1
            >=
            DAGBA
            B
            ATI
            2""",
            setup="JE KI A = 5\nJE KI B = 3",
        )

    def test_nested_function_call_inside_comparison(self):
        source = """ISE FACT(N)
            BI N <= 1
                RETURN 1
            PARI
            RETURN DAGBA N ATI FACT(YO N ATI 1)
        PARI
        JE KI RESULT = 0
        BI
        PE FACT(
            YO
            6
            ATI
            1
        )
        ==
        120
            JE KI RESULT = 1
        PARI
        RESULT"""

        self.assertEqual(self.execute(source), 1)

    def test_multiline_index_comparison_in_while(self):
        source = """JE KI A = [10, 20, 100]
        JE KI I = 0
        NIGBATI
        A[
            I
        ]
        <
        100
            JE KI I = PAPO I ATI 1
        PARI
        I"""

        self.assertEqual(self.execute(source), 2)

    def test_one_line_comparison_remains_compatible(self):
        self.assert_condition("A > 5", setup="JE KI A = 6")


if __name__ == "__main__":
    unittest.main()
