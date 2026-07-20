import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from compiler.ast_optimizer import ast_optimizer
from compiler.ir import IRProgram, ir_lowerer
from interpreter.environment import environment
from interpreter.interpreter import interpreter
from parser.nodes import BinaryExpressionNode, LiteralNode, ProgramNode
from parser.parser import IfaSyntaxError, parser
from runtime.backend_manager import backend_manager
from tools.ohunifa_v45 import OhunIFAShell


class Sprint6PipelineTests(unittest.TestCase):

    def setUp(self):
        interpreter.reset()
        backend_manager.use("python")

    def tearDown(self):
        backend_manager.use("python")
        interpreter.reset()

    def test_ast_nodes_have_source_locations(self):
        program = parser.parse_program(
            """JE KI A = 1

            JE KI B = PAPO A ATI 2
            B""",
            source_name="location_test.ifa",
        )

        self.assertEqual(program.location.source, "location_test.ifa")
        self.assertEqual(program.statements[0].location.line, 1)
        self.assertEqual(program.statements[1].location.line, 3)
        self.assertEqual(program.statements[1].expression.location.line, 3)
        self.assertEqual(program.statements[2].location.line, 4)

    def test_syntax_errors_include_source_and_line(self):
        with self.assertRaises(IfaSyntaxError) as raised:
            parser.parse_program(
                """JE KI A = 1
                PAPO A 2""",
                source_name="broken.ifa",
            )

        self.assertIn("broken.ifa:2:", str(raised.exception))
        self.assertIn("ATI", str(raised.exception))

    def test_constant_folding(self):
        program = parser.parse_program(
            "JE KI RESULT = PAPO 2 ATI DAGBA 3 ATI 4"
        )
        original = program.statements[0].expression
        optimized = ast_optimizer.optimize(program)
        folded = optimized.statements[0].expression

        self.assertIsInstance(original, BinaryExpressionNode)
        self.assertIsInstance(folded, LiteralNode)
        self.assertEqual(folded.value, 14)
        self.assertEqual(folded.location, original.location)

    def test_ir_lowering_and_interpreter_pipeline(self):
        program = parser.parse_program(
            """JE KI A = PAPO 2 ATI 3
            PAPO A ATI 4"""
        )
        optimized = ast_optimizer.optimize(program)
        intermediate = ir_lowerer.lower(optimized)

        self.assertIsInstance(intermediate, IRProgram)
        self.assertEqual(len(intermediate.statements), 2)
        self.assertEqual(interpreter.visit(intermediate), 9)

        interpreter.reset()
        self.assertEqual(interpreter.execute(program), 9)

    def test_for_and_foreach_regression(self):
        result = interpreter.execute(
            parser.parse_program(
                """JE KI TOTAL = 0
                FUN I LATI 1 SI 3
                    JE KI TOTAL = PAPO TOTAL ATI I
                PARI
                JE KI VALUES = [4, 5]
                FUN ITEM NINU VALUES
                    JE KI TOTAL = PAPO TOTAL ATI ITEM
                PARI
                TOTAL"""
            )
        )

        self.assertEqual(result, 15)


class Sprint6ModuleTests(unittest.TestCase):

    def setUp(self):
        interpreter.reset()
        backend_manager.use("python")

    def tearDown(self):
        interpreter.reset()

    def test_import_and_qualified_module_function(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library = root / "math.ifa"
            main = root / "main.ifa"
            library.write_text(
                """MODULE MATH
                ISE ADD(X, Y)
                    RETURN PAPO X ATI Y
                PARI
                PARI
                """,
                encoding="utf-8",
            )
            main.write_text(
                """GBA math.ifa
                JE KI RESULT = MATH.ADD(5, 7)
                RESULT
                """,
                encoding="utf-8",
            )
            program = parser.parse_program(
                main.read_text(encoding="utf-8"),
                source_name=str(main),
            )

            self.assertEqual(interpreter.execute(program), 12)
            self.assertIn("MATH", interpreter.modules)
            self.assertIn("MATH.ADD", interpreter.functions)

    def test_duplicate_import_executes_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library = root / "once.ifa"
            main = root / "main.ifa"
            library.write_text(
                "PRINT(\"LOADED\")\n",
                encoding="utf-8",
            )
            main.write_text(
                "GBA once.ifa\nGBA once.ifa\n",
                encoding="utf-8",
            )
            program = parser.parse_program(
                main.read_text(encoding="utf-8"),
                source_name=str(main),
            )
            output = io.StringIO()

            with redirect_stdout(output):
                interpreter.execute(program)

            self.assertEqual(output.getvalue().strip().splitlines(), ["LOADED"])

    def test_run_uses_source_aware_pipeline(self):
        shell = OhunIFAShell()

        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "run.ifa"
            source_path.write_text(
                "JE KI A = PAPO 2 ATI 3\nPRINT(A)\n",
                encoding="utf-8",
            )
            output = io.StringIO()

            with redirect_stdout(output):
                shell.onecmd(f"RUN {source_path}")

            self.assertEqual(output.getvalue().strip(), "5")
            self.assertEqual(environment.get("A"), 5)


if __name__ == "__main__":
    unittest.main()
