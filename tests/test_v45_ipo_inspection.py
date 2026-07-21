import io
import unittest
from contextlib import redirect_stdout

from runtime.backend_manager import backend_manager
from runtime.ifa_services_v45 import ifa_services_v45
from tools.ohunifa_v45 import OhunIFAShell


class V45IpoInspectionTests(unittest.TestCase):
    def setUp(self):
        ifa_services_v45.reset()
        backend_manager.use("python")
        self.shell = OhunIFAShell("python")

    def tearDown(self):
        ifa_services_v45.reset()
        backend_manager.use("python")

    def command(self, line):
        output = io.StringIO()
        with redirect_stdout(output):
            self.shell.onecmd(line)
        return output.getvalue()

    def test_empty_inspection_is_explicit(self):
        self.assertIn("no native execution", self.command("IPO FRAME"))
        self.assertIn("no Φ-P8 execution", self.command("IPO PHI"))
        self.assertIn("Frames       : 0", self.command("IPO RMU"))

    def test_python_execution_connects_all_ipo_views(self):
        self.assertEqual(self.command("PAPO 2 ATI 3").strip(), "5")
        frame = self.command("IPO FRAME")
        self.assertIn("Operation: PAPO", frame)
        self.assertIn("Y        : 0x05", frame)
        self.assertIn("RA       : 0x02", frame)
        self.assertIn("RD       : 0x01", frame)
        self.assertIn("R0       : 0xFC", frame)
        self.assertIn("T        : 0x00", frame)
        self.assertIn("PHI_A", self.command("IPO PHI"))
        rmu = self.command("IPO RMU")
        self.assertIn("Frames       : 1", rmu)
        self.assertIn("R1:", rmu)

    def test_quantum_pin_preserves_native_channels_without_invalid_rmu_frame(self):
        self.shell.onecmd("BACKEND quantum")
        self.assertEqual(self.command("PIN 7 ATI 2").strip(), "3.5")
        frame = self.command("IPO FRAME")
        self.assertIn("Y        : 0x03", frame)
        self.assertIn("T        : 0x01", frame)
        self.assertIn("PHI_Y", self.command("IPO PHI"))
        self.assertIn("Frames       : 0", self.command("IPO RMU"))


if __name__ == "__main__":
    unittest.main()
