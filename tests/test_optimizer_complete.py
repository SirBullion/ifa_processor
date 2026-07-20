import unittest

from compiler.ast_optimizer import ast_optimizer
from interpreter.interpreter import interpreter
from parser.nodes import (
    AssignmentNode, BinaryExpressionNode, IfNode, LiteralNode, ReturnNode,
    VariableNode, WhileNode,
)
from parser.parser import parser
from runtime.backend_manager import backend_manager


class CompleteOptimizerTests(unittest.TestCase):
    def setUp(self):
        interpreter.reset()
        backend_manager.use("python")

    def optimize(self, source):
        return ast_optimizer.optimize(parser.parse_program(source))

    def test_constant_propagation_and_folding(self):
        program = self.optimize("""JE KI A = 5
JE KI B = PAPO A ATI 3
B""")
        second = program.statements[1]
        self.assertIsInstance(second, AssignmentNode)
        self.assertEqual(second.expression.value, 8)
        self.assertEqual(interpreter.execute(program), 8)

    def test_algebraic_simplification(self):
        program = self.optimize("JE KI A = 9\nPAPO A ATI 0")
        expression = program.statements[-1].expression
        self.assertIsInstance(expression, LiteralNode)
        self.assertEqual(expression.value, 9)

    def test_constant_false_if_and_while_are_eliminated(self):
        program = self.optimize("""BI 0
    JE KI A = 10
PARI
NIGBATI 0
    JE KI A = 20
PARI
42""")
        self.assertFalse(any(isinstance(item, (IfNode, WhileNode)) for item in program.statements))
        self.assertEqual(interpreter.execute(program), 42)

    def test_unreachable_code_after_return_is_eliminated(self):
        program = self.optimize("""ISE VALUE()
    RETURN 7
    RETURN 9
PARI
VALUE()""")
        function = next(item for item in program.statements if hasattr(item, "body"))
        self.assertEqual(len(function.body.statements), 1)
        self.assertIsInstance(function.body.statements[0], ReturnNode)
        self.assertEqual(interpreter.execute(program), 7)

    def test_common_subexpression_is_reused_without_calls(self):
        program = self.optimize("""JE KI X = INPUT_VALUE
JE KI A = PAPO X ATI 2
JE KI B = PAPO X ATI 2""")
        expression = program.statements[2].expression
        self.assertIsInstance(expression, VariableNode)
        self.assertEqual(expression.name, "A")

    def test_optimizer_preserves_call_side_effect_expressions(self):
        program = self.optimize("""JE KI A = PRINT(1)
JE KI B = PRINT(1)""")
        self.assertNotIsInstance(program.statements[1].expression, VariableNode)


if __name__ == "__main__":
    unittest.main()
