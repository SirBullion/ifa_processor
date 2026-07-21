import unittest
from pathlib import Path

from tools import ifaasm_v4, ifaasm_v45


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class V45AssemblerTests(unittest.TestCase):
    def test_all_v45_data_movement_encodings(self):
        source = """MOVY_A
MOVY_B
MOVADDR_A
MOVADDR_B
LOAD_A
LOAD_B
STORE_A
STORE_B
"""
        program, _ = ifaasm_v45.assemble(source.splitlines())
        self.assertEqual(
            program,
            [0x4000, 0x4100, 0x4200, 0x4300,
             0x4400, 0x4500, 0x4600, 0x4700],
        )

    def test_v45_retains_v4_encodings(self):
        source = """start: LDAI 5
LDBI 7
PAPO
BR_EQ done
JMP start
done: HALT
"""
        v4_program, _ = ifaasm_v4.assemble(source.splitlines())
        v45_program, _ = ifaasm_v45.assemble(source.splitlines())
        self.assertEqual(v45_program, v4_program)

    def test_v45_call_accepts_numeric_and_label_targets(self):
        source = """CALL worker
CALL 0x0a
HALT
worker: RET
"""
        program, _ = ifaasm_v45.assemble(source.splitlines())
        self.assertEqual(program, [0xFB03, 0xFB0A, 0xF100, 0xFC00])

    def test_v4_does_not_accept_v45_instruction(self):
        with self.assertRaisesRegex(ValueError, "Unknown V4 instruction"):
            ifaasm_v4.assemble(["MOVY_A"])

    def test_v45_executor_has_memory_and_return_data_paths(self):
        executor = (
            PROJECT_ROOT / "rtl" / "v45" / "ifa_program_executor_v45.sv"
        ).read_text(encoding="utf-8")
        self.assertIn("4'h4: begin", executor)
        self.assertIn("ST_WAIT_MEMORY", executor)
        self.assertIn("active_frame_y,", executor)
        self.assertIn("pending_return_y <= active_frame_y", executor)
        self.assertIn("saved_b,", executor)
        self.assertIn("saved_address,", executor)

    def test_v4_sources_remain_unmodified_by_v45_extension(self):
        executor = (
            PROJECT_ROOT / "rtl" / "v4" / "ifa_program_executor_v4.sv"
        ).read_text(encoding="utf-8")
        self.assertNotIn("ST_WAIT_MEMORY", executor)
        self.assertNotIn("MOVY_A", executor)

    def test_v45_native_rau_is_exact_v4_service_copy(self):
        v4 = (
            PROJECT_ROOT / "rtl" / "v4" / "ifa_native_rau_v4.sv"
        ).read_text(encoding="utf-8")
        v45 = (
            PROJECT_ROOT / "rtl" / "v45" / "ifa_native_rau_v45.sv"
        ).read_text(encoding="utf-8")
        normalized = v45.replace("IFÁ Processor V4.5", "IFÁ Processor V4")
        normalized = normalized.replace("ifa_native_rau_v45", "ifa_native_rau_v4")
        self.assertEqual(normalized.rstrip(), v4.rstrip())

    def test_v45_native_rau_test_covers_all_operations(self):
        testbench = (
            PROJECT_ROOT / "tb" / "v45" / "tb_ifa_native_rau_v45.sv"
        ).read_text(encoding="utf-8")
        for operation in (
            "PAPO", "YO", "DAGBA", "PIN", "KU",
            "GBE", "SEDA", "JU", "KERE",
        ):
            self.assertIn(f"OP_{operation}", testbench)
        self.assertIn("PASS: ALL NATIVE IFÁ MATHEMATICAL FUNCTIONS VERIFIED", testbench)


if __name__ == "__main__":
    unittest.main()
