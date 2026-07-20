import unittest

from interpreter.environment import environment
from interpreter.interpreter import interpreter
from parser.nodes import AssignmentNode, BinaryExpressionNode
from parser.parser import parser
from runtime.backend_manager import backend_manager


class Sprint2ExpressionTests(unittest.TestCase):

    def setUp(self):
        environment.variables.clear()
        backend_manager.use("python")

    def evaluate(self, source):
        return interpreter.visit(parser.parse(source))

    def test_nested_expression_on_left(self):
        self.assertEqual(
            self.evaluate("PAPO DAGBA 2 ATI 3 ATI 4"),
            10,
        )

    def test_nested_expression_on_right(self):
        self.assertEqual(
            self.evaluate("DAGBA 2 ATI PAPO 3 ATI 4"),
            14,
        )

    def test_parenthesized_nested_expression(self):
        self.assertEqual(
            self.evaluate("YO (PAPO 10 ATI 5) ATI (DAGBA 2 ATI 3)"),
            9,
        )

    def test_expression_assignment_can_be_reused(self):
        assignment = parser.parse(
            "JE KI TOTAL = PAPO 2 ATI DAGBA 3 ATI 4"
        )

        self.assertIsInstance(assignment, AssignmentNode)
        self.assertIsInstance(assignment.expression, BinaryExpressionNode)
        self.assertEqual(interpreter.visit(assignment), 14)
        self.assertEqual(self.evaluate("YO TOTAL ATI 5"), 9)

    def test_malformed_nested_expression_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "ATI"):
            parser.parse("PAPO PAPO 1 ATI 2 3")


if __name__ == "__main__":
    unittest.main()
