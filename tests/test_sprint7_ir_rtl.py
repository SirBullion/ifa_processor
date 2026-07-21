import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from compiler.ast_optimizer import ast_optimizer
from compiler.ir import IRInstruction, IRProgram, ir_lowerer
from compiler.rtl_generator import systemverilog_generator
from interpreter.interpreter import interpreter
from parser.parser import parser
from runtime.backend_manager import backend_manager
from tools.ohunifa_v45 import OhunIFAShell


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Sprint7IRTests(unittest.TestCase):
    def setUp(self):
        interpreter.reset(); backend_manager.use("python")

    def tearDown(self):
        backend_manager.use("python"); interpreter.reset()

    def compile_example(self, filename):
        path = PROJECT_ROOT / "examples" / filename
        ast = parser.parse_program(path.read_text(encoding="utf-8"), source_name=str(path))
        return ast, ir_lowerer.lower(ast_optimizer.optimize(ast))

    def test_three_address_ir_for_factorial(self):
        ast, ir = self.compile_example("factorial.ifa")
        self.assertIsInstance(ir, IRProgram)
        self.assertTrue(all(isinstance(item, IRInstruction) for item in ir.instructions))
        self.assertIn("FACTORIAL", ir.functions)
        opcodes = [item.opcode for item in ir.functions["FACTORIAL"].instructions]
        for opcode in ("LOAD", "CALL", "MUL", "RETURN", "JUMP_IF_FALSE"):
            self.assertIn(opcode, opcodes)
        text = ir.to_text()
        self.assertIn("CALL", text); self.assertIn(".function FACTORIAL(N)", text)

    def test_fibonacci_and_hanoi_generate_recursive_calls(self):
        for filename, function in (("fibonacci.ifa", "FIBONACCI"), ("tower_of_hanoi.ifa", "HANOI")):
            with self.subTest(filename=filename):
                _, ir = self.compile_example(filename)
                calls = [item for item in ir.functions[function].instructions if item.opcode == "CALL" and item.operands[1] == function]
                self.assertGreaterEqual(len(calls), 2)

    def test_python_and_rtl_backends_execute_same_ir(self):
        source = """ISE FACT(N)
        BI N <= 1
            RETURN 1
        PARI
        RETURN DAGBA N ATI FACT(YO N ATI 1)
        PARI
        FACT(6)"""
        ast = parser.parse_program(source)
        results = {}
        for backend in ("python", "rtl"):
            interpreter.reset(); backend_manager.use(backend)
            results[backend] = interpreter.execute(ast)
        self.assertEqual(results, {"python": 720, "rtl": 720})

    def test_ir_execution_matches_legacy_ast_visitor(self):
        source = """ISE FIB(N)
        BI N <= 1
            RETURN N
        PARI
        RETURN PAPO FIB(YO N ATI 1) ATI FIB(YO N ATI 2)
        PARI
        FIB(8)"""
        ast = parser.parse_program(source)
        legacy = interpreter.visit(ast)
        interpreter.reset()
        compiled = interpreter.execute(ast)
        self.assertEqual(legacy, compiled)
        self.assertEqual(compiled, 21)


class Sprint7RTLTests(unittest.TestCase):
    def setUp(self):
        interpreter.reset(); backend_manager.use("python")

    def tearDown(self):
        backend_manager.use("python"); interpreter.reset()

    def test_rtl_generation_emits_main_and_function_modules(self):
        path = PROJECT_ROOT / "examples" / "factorial.ifa"
        ast = parser.parse_program(path.read_text(encoding="utf-8"), source_name=str(path))
        ir = ir_lowerer.lower(ast_optimizer.optimize(ast))
        rtl = systemverilog_generator.generate(ir, "factorial")
        self.assertIn("module factorial_main", rtl)
        self.assertIn("module factorial_factorial", rtl)
        self.assertIn("always_ff @(posedge clk)", rtl)
        self.assertIn("call_valid", rtl)
        self.assertNotIn("TODO", rtl)

    def test_compile_command_writes_ir_and_systemverilog(self):
        shell = OhunIFAShell()
        output = io.StringIO()
        with redirect_stdout(output):
            shell.onecmd("COMPILE examples/factorial.ifa")
        ir_path = PROJECT_ROOT / "build" / "factorial.ir"
        rtl_path = PROJECT_ROOT / "build" / "factorial.sv"
        self.assertTrue(ir_path.is_file()); self.assertTrue(rtl_path.is_file())
        self.assertIn(".function FACTORIAL", ir_path.read_text(encoding="utf-8"))
        self.assertIn("module factorial_factorial", rtl_path.read_text(encoding="utf-8"))


if __name__ == "__main__": unittest.main()
