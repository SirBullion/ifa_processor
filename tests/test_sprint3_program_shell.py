import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from interpreter.environment import environment
from interpreter.interpreter import interpreter
from parser.nodes import ProgramNode
from parser.parser import parser
from runtime.backend_manager import backend_manager
from tools.ohunifa_v45 import OhunIFAShell


PROGRAM_SOURCE = """ISE DOUBLE(X)
    RETURN DAGBA X ATI 2
PARI

ISE ADD(X, Y)
    RETURN PAPO X ATI Y
PARI

JE KI A = 5
JE KI B = 7
JE KI C = PE ADD(A, B)
JE KI D = PE DOUBLE(C)

PAPO D ATI 100
"""


class Sprint3ProgramTests(unittest.TestCase):

    def setUp(self):
        interpreter.reset()
        backend_manager.use("python")

    def tearDown(self):
        backend_manager.use("python")
        interpreter.reset()

    def test_multiline_program_ast_and_execution_order(self):
        program = parser.parse_program(PROGRAM_SOURCE)

        self.assertIsInstance(program, ProgramNode)
        self.assertEqual(len(program.statements), 7)
        self.assertEqual(interpreter.visit(program), 124)

    def test_variables_persist_through_complete_program(self):
        interpreter.visit(parser.parse(PROGRAM_SOURCE))

        self.assertEqual(environment.get("A"), 5)
        self.assertEqual(environment.get("B"), 7)
        self.assertEqual(environment.get("C"), 12)
        self.assertEqual(environment.get("D"), 24)

    def test_multiline_program_preserves_nested_expressions(self):
        result = interpreter.visit(
            parser.parse(
                """JE KI A = PAPO 2 ATI DAGBA 3 ATI 4
                JE KI B = YO (PAPO A ATI 10) ATI 1
                PAPO A ATI B"""
            )
        )

        self.assertEqual(result, 37)


class Sprint3ShellTests(unittest.TestCase):

    def setUp(self):
        interpreter.reset()
        backend_manager.use("python")
        self.shell = OhunIFAShell()

    def tearDown(self):
        backend_manager.use("python")
        interpreter.reset()

    def test_paste_otan_executes_source_as_one_program(self):
        output = io.StringIO()

        with redirect_stdout(output):
            self.shell.onecmd("PASTE")

            for line in PROGRAM_SOURCE.splitlines():
                self.shell.onecmd(line)

            self.assertIsNotNone(self.shell.paste_lines)
            self.assertEqual(environment.variables, {})
            self.assertEqual(interpreter.functions, {})
            self.shell.onecmd("OTAN")

        self.assertIsNone(self.shell.paste_lines)
        self.assertEqual(self.shell.prompt, "OHUNIFA> ")
        self.assertEqual(output.getvalue().strip(), "124")
        self.assertEqual(environment.get("D"), 24)

    def test_end_remains_a_paste_compatibility_alias(self):
        output = io.StringIO()

        with redirect_stdout(output):
            self.shell.onecmd("PASTE")
            self.shell.onecmd("PAPO 2 ATI 3")
            self.shell.onecmd("END")

        self.assertEqual(output.getvalue().strip(), "5")

    def test_parse_program_always_returns_program_node(self):
        program = parser.parse_program("PAPO 2 ATI 3")

        self.assertIsInstance(program, ProgramNode)
        self.assertEqual(len(program.statements), 1)

    def test_run_filename_executes_complete_source_file(self):
        output = io.StringIO()

        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "program.ifa"
            source_path.write_text(PROGRAM_SOURCE, encoding="utf-8")

            with redirect_stdout(output):
                self.shell.onecmd(f"RUN {source_path}")

        self.assertEqual(output.getvalue().strip(), "124")
        self.assertEqual(environment.get("C"), 12)

    def test_single_line_mode_remains_available(self):
        output = io.StringIO()

        with redirect_stdout(output):
            self.shell.onecmd("PAPO 2 ATI 3")

        self.assertEqual(output.getvalue().strip(), "5")

    def test_interactive_function_declaration_collects_until_pari(self):
        output = io.StringIO()

        with redirect_stdout(output):
            self.shell.onecmd("ISE ADD(X, Y)")
            self.assertIsNotNone(self.shell.declaration_lines)
            self.shell.onecmd("RETURN PAPO X ATI Y")
            self.shell.onecmd("PARI")
            self.assertIsNone(self.shell.declaration_lines)
            self.shell.onecmd("PE ADD(5, 7)")

        lines = output.getvalue().strip().splitlines()
        self.assertTrue(lines[0].startswith("FunctionNode("))
        self.assertEqual(lines[-1], "12")

    def test_interactive_function_collects_nested_control_flow(self):
        output = io.StringIO()

        with redirect_stdout(output):
            self.shell.onecmd("ISE POSITIVE(X)")
            self.shell.onecmd("BI X > 0")
            self.shell.onecmd("RETURN 1")
            self.shell.onecmd("TABI")
            self.shell.onecmd("RETURN 0")
            self.shell.onecmd("PARI")
            self.assertIsNotNone(self.shell.declaration_lines)
            self.shell.onecmd("PARI")
            self.assertIsNone(self.shell.declaration_lines)
            self.shell.onecmd("PE POSITIVE(5)")

        self.assertEqual(output.getvalue().strip().splitlines()[-1], "1")


if __name__ == "__main__":
    unittest.main()
