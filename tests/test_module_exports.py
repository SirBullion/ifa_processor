import tempfile
import unittest
from pathlib import Path

from interpreter.interpreter import interpreter
from parser.parser import parser
from runtime.backend_manager import backend_manager


class ModuleExportTests(unittest.TestCase):
    def setUp(self):
        interpreter.reset(); backend_manager.use("python")

    def execute_files(self, library_source, main_source):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library = root / "library.ifa"
            main = root / "main.ifa"
            library.write_text(library_source, encoding="utf-8")
            main.write_text(main_source, encoding="utf-8")
            ast = parser.parse_program(main_source, source_name=str(main))
            return interpreter.execute(ast)

    def test_explicit_export_is_callable(self):
        result = self.execute_files(
            """MODULE VALUES
ISE PUBLIC(X)
    RETURN PRIVATE(X)
PARI
ISE PRIVATE(X)
    RETURN PAPO X ATI 1
PARI
EXPORT("PUBLIC")
PARI""",
            "GBA library.ifa\nVALUES.PUBLIC(4)",
        )
        self.assertEqual(result, 5)

    def test_private_qualified_function_is_rejected(self):
        with self.assertRaisesRegex(NameError, "private"):
            self.execute_files(
                """MODULE VALUES
ISE PUBLIC(X)
    RETURN X
PARI
ISE PRIVATE(X)
    RETURN X
PARI
EXPORT("PUBLIC")
PARI""",
                "GBA library.ifa\nVALUES.PRIVATE(4)",
            )

    def test_module_without_export_retains_export_all_behavior(self):
        result = self.execute_files(
            """MODULE VALUES
ISE FIRST()
    RETURN 1
PARI
ISE SECOND()
    RETURN 2
PARI
PARI""",
            "GBA library.ifa\nVALUES.SECOND()",
        )
        self.assertEqual(result, 2)

    def test_unknown_export_fails_during_compilation(self):
        with self.assertRaisesRegex(ValueError, "undefined"):
            interpreter.execute(parser.parse_program(
                "MODULE BAD\nEXPORT(\"MISSING\")\nPARI"
            ))


if __name__ == "__main__": unittest.main()
