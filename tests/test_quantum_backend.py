import importlib.util
import unittest
from pathlib import Path

from backends.python.backend import python_backend
from backends.quantum.backend import (
    QuantumBackend,
    UnsupportedQuantumOperation,
)
from quantum.comparison import (
    SUPPORTED_OPERATIONS,
    UNSUPPORTED_NATIVE_OPERATIONS,
)
from quantum.measurement import QuantumDependencyError, QuantumDomainError
from quantum.native import ORACLES, OracleState
from quantum.phi import phi_p2, phi_p2_inverse, phi_p8, phi_p8_inverse
from runtime.backend_manager import backend_manager
from runtime.execution_request import ExecutionRequest


QISKIT_AVAILABLE = importlib.util.find_spec("qiskit") is not None
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def request(operation, a, b):
    return ExecutionRequest(operation, {"opcode": operation}, a, b)


class QuantumBackendInfrastructureTests(unittest.TestCase):
    def test_backend_is_registered(self):
        self.assertIn("quantum", backend_manager.available())

    def test_supported_operations_are_only_verified_v5_operations(self):
        self.assertEqual(
            SUPPORTED_OPERATIONS,
            frozenset({
                "PAPO", "YO", "DAGBA", "PIN", "KU",
                "GBE", "SEDA", "JU", "KERE",
            }),
        )
        self.assertEqual(UNSUPPORTED_NATIVE_OPERATIONS, frozenset())

    def test_unsupported_operations_fail_before_loading_qiskit(self):
        backend = QuantumBackend()
        for operation in UNSUPPORTED_NATIVE_OPERATIONS:
            with self.subTest(operation=operation):
                with self.assertRaisesRegex(UnsupportedQuantumOperation, operation):
                    backend.execute(request(operation, 2, 2))

    def test_verified_byte_domain_is_enforced(self):
        backend = QuantumBackend()
        for operation, a, b in (
            ("PAPO", 255, 1),
            ("YO", 1, 2),
            ("PAPO", -1, 2),
            ("PAPO", 2, 256),
            ("PAPO", 1.5, 2),
        ):
            with self.subTest(operation=operation, a=a, b=b):
                with self.assertRaises(QuantumDomainError):
                    backend.execute(request(operation, a, b))

    def test_phi_library_reuses_canonical_transform(self):
        for value in range(256):
            self.assertEqual(phi_p8_inverse(phi_p8(value)), value)
        for a in (0, 1):
            for b in (0, 1):
                self.assertEqual(phi_p2_inverse(*phi_p2(a, b)), (a, b))

    def test_new_reversible_oracles_match_python_backend(self):
        cases = {
            "DAGBA": ((0, 8), (3, 7), (15, 15)),
            "PIN": ((8, 2), (7, 2), (255, 16)),
            "KU": ((8, 3), (7, 2), (255, 16)),
            "GBE": ((2, 8), (3, 4), (10, 3)),
        }
        backend = QuantumBackend()
        for operation, values in cases.items():
            for a, b in values:
                with self.subTest(operation=operation, a=a, b=b):
                    item = request(operation, a, b)
                    self.assertEqual(backend.execute(item), python_backend.execute(item))
                    relation = backend.last_execution
                    self.assertEqual(relation.ra, a & b)
                    self.assertEqual(relation.rd, a ^ b)
                    self.assertEqual(relation.r0, (~(a | b)) & 0xFF)
                    self.assertEqual(phi_p8_inverse(relation.phi_y), relation.y)

    def test_new_oracles_are_self_inverse(self):
        for operation, oracle in ORACLES.items():
            with self.subTest(operation=operation):
                initial = OracleState(7, 2, y=0xA5, t=0x5A)
                self.assertEqual(oracle.apply(oracle.apply(initial)), initial)

    def test_research_entry_points_are_thin_wrappers(self):
        wrappers = {
            "simulate_phi_p2_qiskit.py": "quantum.verified_phi_p2",
            "simulate_phi_p8_qiskit.py": "quantum.verified_phi_p8",
            "simulate_relation_frame_qiskit.py": "quantum.verified_relation",
            "simulate_quantum_full_adder.py": "quantum.verified_full_adder",
            "simulate_quantum_dual_carry_ripple_4bit.py": "quantum.verified_ripple",
            "simulate_quantum_ifa_alu_integrated.py": "quantum.verified_alu",
            "ifa_quantum_processor.py": "quantum.verified_processor",
        }
        for filename, module in wrappers.items():
            with self.subTest(filename=filename):
                text = (PROJECT_ROOT / "python" / "v5" / filename).read_text(
                    encoding="utf-8"
                )
                self.assertIn(f"from {module} import *", text)
                self.assertLess(len(text), 400)

    @unittest.skipIf(QISKIT_AVAILABLE, "Dependency-missing behavior only")
    def test_missing_qiskit_has_backend_specific_error(self):
        with self.assertRaises(QuantumDependencyError):
            QuantumBackend().execute(request("PAPO", 2, 3))


@unittest.skipUnless(QISKIT_AVAILABLE, "Qiskit is not installed")
class QuantumBackendParityTests(unittest.TestCase):
    CASES = {
        "PAPO": ((0, 0), (2, 3), (100, 55)),
        "YO": ((0, 0), (7, 2), (255, 1)),
        "SEDA": ((0, 0), (5, 5), (5, 7)),
        "JU": ((9, 2), (2, 9), (4, 4)),
        "KERE": ((2, 9), (9, 2), (4, 4)),
        "DAGBA": ((0, 8), (3, 7), (15, 15)),
        "PIN": ((8, 2), (7, 2), (255, 16)),
        "KU": ((8, 3), (7, 2), (255, 16)),
        "GBE": ((2, 8), (3, 4), (10, 3)),
    }

    def test_python_quantum_parity(self):
        quantum = QuantumBackend()
        for operation, cases in self.CASES.items():
            for a, b in cases:
                with self.subTest(operation=operation, a=a, b=b):
                    item = request(operation, a, b)
                    self.assertEqual(quantum.execute(item), python_backend.execute(item))

    def test_backend_manager_selection_uses_runtime_contract(self):
        previous = backend_manager.backend_name
        try:
            backend_manager.use("quantum")
            self.assertIsInstance(backend_manager.backend, QuantumBackend)
        finally:
            backend_manager.use(previous)


if __name__ == "__main__":
    unittest.main()
