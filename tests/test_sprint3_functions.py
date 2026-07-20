import unittest

from backends.python.backend import python_backend
from interpreter.environment import environment
from interpreter.interpreter import interpreter
from parser.nodes import FunctionNode, ProgramNode, ReturnNode
from parser.parser import parser
from runtime.backend_manager import backend_manager


class RecordingBackend:

    def __init__(self):
        self.requests = []
        self.frames = []

    def execute(self, request):
        self.requests.append(request)
        frame = environment.current_frame
        self.frames.append(
            None if frame is None else frame.function_name
        )
        return python_backend.execute(request)


class Sprint3FunctionTests(unittest.TestCase):

    def setUp(self):
        interpreter.reset()
        backend_manager.use("python")

    def tearDown(self):
        backend_manager.use("python")
        interpreter.reset()

    def execute(self, source):
        return interpreter.visit(parser.parse(source))

    def test_function_definition(self):
        function = parser.parse(
            """ISE ADD(X, Y)
            PAPO X ATI Y
            PARI"""
        )

        self.assertIsInstance(function, FunctionNode)
        self.assertEqual(function.name, "ADD")
        self.assertEqual(function.parameters, ["X", "Y"])
        self.assertEqual(len(function.body.statements), 1)
        self.assertIs(interpreter.visit(function), function)
        self.assertIs(interpreter.functions["ADD"], function)

    def test_function_call_and_assignment(self):
        result = self.execute(
            """ISE ADD(X, Y)
            PAPO X ATI Y
            PARI
            JE KI Z = PE ADD(5, 7)"""
        )

        self.assertEqual(result, 12)
        self.assertEqual(environment.get("Z"), 12)
        self.assertEqual(environment.call_stack, [])

    def test_nested_function_call(self):
        result = self.execute(
            """ISE DOUBLE(X)
            RETURN DAGBA X ATI 2
            PARI
            ISE ADD_DOUBLE(X, Y)
            RETURN PAPO PE DOUBLE(X) ATI PE DOUBLE(Y)
            PARI
            PE ADD_DOUBLE(3, 4)"""
        )

        self.assertEqual(result, 14)
        self.assertEqual(environment.call_stack, [])

    def test_local_scope_and_global_access(self):
        self.execute("JE KI OFFSET = 10")
        result = self.execute(
            """ISE SHIFT(OFFSET)
            JE KI LOCAL = PAPO OFFSET ATI 1
            RETURN PAPO LOCAL ATI GLOBAL_VALUE
            PARI
            JE KI GLOBAL_VALUE = 5
            PE SHIFT(20)"""
        )

        self.assertEqual(result, 26)
        self.assertEqual(environment.get("OFFSET"), 10)

        with self.assertRaises(NameError):
            environment.get("LOCAL")

    def test_explicit_return_stops_function_body(self):
        program = parser.parse(
            """ISE DOUBLE(X)
            RETURN DAGBA X ATI 2
            JE KI UNREACHABLE = 99
            PARI
            PE DOUBLE(6)"""
        )

        self.assertIsInstance(program, ProgramNode)
        function = program.statements[0]
        self.assertIsInstance(function.body.statements[0], ReturnNode)
        self.assertEqual(interpreter.visit(program), 12)

        with self.assertRaises(NameError):
            environment.get("UNREACHABLE")

    def test_function_arithmetic_uses_selected_backend(self):
        recording_backend = RecordingBackend()
        backend_manager.register("recording", recording_backend)
        backend_manager.use("recording")

        result = self.execute(
            """ISE DOUBLE(X)
            RETURN DAGBA X ATI 2
            PARI
            PE DOUBLE(8)"""
        )

        self.assertEqual(result, 16)
        self.assertEqual(len(recording_backend.requests), 1)
        self.assertEqual(
            recording_backend.requests[0].operator_name,
            "DAGBA",
        )
        self.assertEqual(recording_backend.frames, ["DOUBLE"])

    def test_call_frame_tracks_parent_parameters_and_return_address(self):
        observed = []

        class FrameBackend:

            def execute(self, request):
                frame = environment.current_frame
                observed.append(frame)
                return python_backend.execute(request)

        backend_manager.register("frames", FrameBackend())
        backend_manager.use("frames")

        result = self.execute(
            """ISE INNER(Y)
            RETURN PAPO Y ATI 1
            PARI
            ISE OUTER(X)
            RETURN PE INNER(X)
            PARI
            PE OUTER(4)"""
        )

        self.assertEqual(result, 5)
        inner = observed[0]
        self.assertEqual(inner.function_name, "INNER")
        self.assertEqual(inner.parameters, {"Y": 4})
        self.assertEqual(inner.variables, {"Y": 4})
        self.assertEqual(inner.parent.function_name, "OUTER")
        self.assertIsNotNone(inner.return_address)
        self.assertEqual(environment.call_stack, [])

    def test_return_outside_function_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "inside a function"):
            self.execute("RETURN 1")

    def test_wrong_argument_count_is_rejected(self):
        self.execute(
            """ISE IDENTITY(X)
            RETURN X
            PARI"""
        )

        with self.assertRaisesRegex(TypeError, "expects 1 arguments"):
            self.execute("PE IDENTITY(1, 2)")


if __name__ == "__main__":
    unittest.main()
