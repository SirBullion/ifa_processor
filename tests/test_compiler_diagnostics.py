import io
import unittest
from contextlib import redirect_stdout

from compiler.diagnostics import diagnostic_from_exception
from parser.parser import IfaSyntaxError, parser
from tools.ohunifa_v45 import OhunIFAShell


class CompilerDiagnosticTests(unittest.TestCase):
    SOURCE = "JE KI A = 1\n    PAPO A 2"

    def syntax_error(self):
        try:
            parser.parse_program(self.SOURCE, source_name="broken.ifa")
        except IfaSyntaxError as error:
            return error
        self.fail("Expected a syntax error")

    def test_structured_diagnostic_has_source_position_and_expectation(self):
        diagnostic = diagnostic_from_exception(
            self.syntax_error(), self.SOURCE, "broken.ifa"
        )
        self.assertEqual(diagnostic.filename, "broken.ifa")
        self.assertEqual(diagnostic.line, 2)
        self.assertGreaterEqual(diagnostic.column, 1)
        self.assertEqual(diagnostic.expected_token, "ATI")
        self.assertIn("Expected keyword ATI", diagnostic.message)

    def test_shell_preserves_error_prefix_and_adds_column(self):
        output = io.StringIO()
        with redirect_stdout(output):
            OhunIFAShell().execute_program(self.SOURCE, "broken.ifa")
        rendered = output.getvalue()
        self.assertIn("ERROR: broken.ifa:2:", rendered)
        self.assertIn("expected token: ATI", rendered)


if __name__ == "__main__": unittest.main()
