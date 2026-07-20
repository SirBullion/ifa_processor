import unittest

from backends.python.backend import python_backend
from interpreter.environment import environment
from interpreter.interpreter import interpreter
from parser.nodes import IfNode, WhileNode
from parser.parser import parser
from runtime.backend_manager import backend_manager


class RecordingBackend:

    def __init__(self):
        self.operators = []

    def execute(self, request):
        self.operators.append(request.operator_name)
        return python_backend.execute(request)


class Sprint4ControlFlowTests(unittest.TestCase):

    def setUp(self):
        interpreter.reset()
        backend_manager.use("python")

    def tearDown(self):
        backend_manager.use("python")
        interpreter.reset()

    def execute(self, source):
        return interpreter.visit(parser.parse_program(source))

    def test_if_executes_true_branch(self):
        program = parser.parse_program(
            """JE KI X = 8
            BI X JU 5
                JE KI RESULT = X
            PARI
            RESULT"""
        )

        self.assertIsInstance(program.statements[1], IfNode)
        self.assertEqual(interpreter.visit(program), 8)

    def test_else_executes_false_branch(self):
        result = self.execute(
            """JE KI X = 2
            BI X > 5
                JE KI RESULT = X
            TABI
                JE KI RESULT = 0
            PARI
            RESULT"""
        )

        self.assertEqual(result, 0)

    def test_nested_if(self):
        result = self.execute(
            """JE KI X = 7
            BI X >= 5
                BI X <= 10
                    JE KI RESULT = 1
                TABI
                    JE KI RESULT = 2
                PARI
            TABI
                JE KI RESULT = 3
            PARI
            RESULT"""
        )

        self.assertEqual(result, 1)

    def test_while_loop(self):
        program = parser.parse_program(
            """JE KI I = 0
            NIGBATI I KERÉ 10
                JE KI I = PAPO I ATI 1
            PARI
            I"""
        )

        self.assertIsInstance(program.statements[1], WhileNode)
        self.assertEqual(interpreter.visit(program), 10)

    def test_break(self):
        result = self.execute(
            """JE KI I = 0
            NIGBATI TRUE
                JE KI I = PAPO I ATI 1
                BI I == 4
                    BREAK
                PARI
            PARI
            I"""
        )

        self.assertEqual(result, 4)

    def test_continue(self):
        result = self.execute(
            """JE KI I = 0
            JE KI TOTAL = 0
            NIGBATI I < 5
                JE KI I = PAPO I ATI 1
                BI I == 3
                    CONTINUE
                PARI
                JE KI TOTAL = PAPO TOTAL ATI I
            PARI
            TOTAL"""
        )

        self.assertEqual(result, 12)

    def test_all_symbolic_comparisons(self):
        expected = {
            "==": 1,
            "!=": 1,
            ">": 1,
            "<": 1,
            ">=": 1,
            "<=": 1,
        }
        sources = {
            "==": "5 == 5",
            "!=": "5 != 4",
            ">": "5 > 4",
            "<": "4 < 5",
            ">=": "5 >= 5",
            "<=": "5 <= 5",
        }

        for operator, source in sources.items():
            with self.subTest(operator=operator):
                self.assertEqual(self.execute(source), expected[operator])

    def test_comparisons_use_runtime_backend(self):
        recording = RecordingBackend()
        backend_manager.register("sprint4-recording", recording)
        backend_manager.use("sprint4-recording")

        result = self.execute(
            """JE KI A = 5 >= 5
            JE KI B = 5 != 4
            AND A ATI B"""
        )

        self.assertEqual(result, 1)
        self.assertEqual(recording.operators, ["KERE", "SEDA"])

    def test_boolean_expressions(self):
        result = self.execute(
            """JE KI X = 5
            BI AND (X >= 5) ATI NOT (X == 0)
                JE KI RESULT = TRUE
            TABI
                JE KI RESULT = FALSE
            PARI
            RESULT"""
        )

        self.assertIs(result, True)

    def test_nested_loops_break_only_innermost_loop(self):
        result = self.execute(
            """JE KI OUTER = 0
            JE KI COUNT = 0
            NIGBATI OUTER < 3
                JE KI OUTER = PAPO OUTER ATI 1
                JE KI INNER = 0
                NIGBATI INNER < 5
                    JE KI INNER = PAPO INNER ATI 1
                    BI INNER == 2
                        BREAK
                    PARI
                    JE KI COUNT = PAPO COUNT ATI 100
                PARI
                JE KI COUNT = PAPO COUNT ATI INNER
            PARI
            COUNT"""
        )

        self.assertEqual(result, 306)

    def test_break_and_continue_outside_loop_are_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "inside a loop"):
            self.execute("BREAK")

        with self.assertRaisesRegex(RuntimeError, "inside a loop"):
            self.execute("CONTINUE")


if __name__ == "__main__":
    unittest.main()
