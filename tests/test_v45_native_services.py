import io
import random
import unittest
from contextlib import redirect_stdout

from backends.python.backend import PythonBackend
from backends.quantum.backend import QuantumBackend
from backends.rtl.backend import RTLBackend
from language_v45.kernel import kernel
from runtime.backend_manager import backend_manager
from runtime.execution_request import ExecutionRequest
from runtime.ifa_services_v45 import IfaServicesV45
from runtime.runtime import runtime


class V45NativeServiceTests(unittest.TestCase):
    def setUp(self):
        backend_manager.use("python")
        self.services = IfaServicesV45(random.Random(7))

    def output(self, command):
        stream = io.StringIO()
        with redirect_stdout(stream):
            handled = self.services.handle(command)
        return handled, stream.getvalue()

    def test_daifa_lists_sixteen_oju_odu(self):
        handled, output = self.output("DÁIFÁ")
        self.assertTrue(handled)
        self.assertIn("THE SIXTEEN OJÚ ODÙ", output)
        self.assertEqual(output.count("0x"), 16)
        self.assertIn("ÒGBÈ", output)
        self.assertIn("ÒFÚN", output)

    def test_printodu_uses_v45_canonical_relation_frame(self):
        request = ExecutionRequest("PAPO", kernel.operators["PAPO"], 2, 3)
        result = backend_manager.backend.execute(request)
        self.services.record_execution(request, result)
        handled, output = self.output("PRINTODUALL")
        self.assertTrue(handled)
        for field in ("OYÈLÁ", "FARAPỌ̀", "YÀTỌ̀", "ÌPÌLẸ̀", "GBÉ"):
            self.assertIn(field, output)
        self.assertIn("0x05", output)

    def test_runtime_records_literal_native_execution(self):
        from runtime.ifa_services_v45 import ifa_services_v45
        ifa_services_v45.reset()
        runtime.execute(ExecutionRequest("PAPO", kernel.operators["PAPO"], 2, 3))
        self.assertIsNotNone(ifa_services_v45.last_frame)
        self.assertEqual(ifa_services_v45.last_frame.Y, 5)

    def test_opele_and_last_repeat_same_cast(self):
        _, first = self.output("ÒPẸ̀LẸ̀")
        _, repeated = self.output("OPELE LAST")
        self.assertEqual(first, repeated)
        self.assertIn("ÈṢÙ", first)
        self.assertIn("Ọ̀TÚN", first)
        self.assertIn("ÒSÌ", first)

    def test_teifa_accepts_bits_names_compact_meji_and_last(self):
        for command, expected in (
            ("TEIFA 0000", "ÒGBÈ"),
            ("TẸ IFÁ OYEKU", "ÒYÈKÚ"),
            ("TEIFA 00001111", "ÒGBÈ ÒYÈKÚ"),
            ("TEIFA OYEKU MEJI", "ÒYÈKÚ MÉJÌ"),
            ("TEIFA LAST", "ÒYÈKÚ MÉJÌ"),
        ):
            with self.subTest(command=command):
                handled, output = self.output(command)
                self.assertTrue(handled)
                self.assertIn(expected, output)

    def test_service_channels_match_across_backends(self):
        request = ExecutionRequest("DAGBA", kernel.operators["DAGBA"], 3, 7)
        channel_sets = []
        for backend in (PythonBackend(), RTLBackend(), QuantumBackend()):
            with self.subTest(backend=type(backend).__name__):
                result = backend.execute(request)
                services = IfaServicesV45()
                services.record_execution(request, result, backend.last_execution)
                channel_sets.append(services.last_channels)
        self.assertEqual(channel_sets[0], channel_sets[1])
        self.assertEqual(channel_sets[1], channel_sets[2])

    def test_quantum_pin_preserves_existing_y_and_t_channels(self):
        request = ExecutionRequest("PIN", kernel.operators["PIN"], 7, 2)
        backend = QuantumBackend()
        result = backend.execute(request)
        self.services.record_execution(request, result, backend.last_execution)
        self.assertEqual(result, 3.5)
        self.assertEqual(self.services.last_channels["y"], 3)
        self.assertEqual(self.services.last_channels["t"], 1)

    def test_security_and_yara_commands_are_not_service_commands(self):
        for command in (
            "BABALAWO TAN", "ONILE", "YARA OGBE", "GRANT 0 1", "SHARE 0 1"
        ):
            with self.subTest(command=command):
                self.assertFalse(self.services.handle(command))


if __name__ == "__main__":
    unittest.main()
