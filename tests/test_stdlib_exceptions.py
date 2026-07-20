import unittest

from core.exceptions import (
    CompilerError, ExecutionError, IfaError, MemoryError, PermissionDenied,
    QuantumDomainError, RelationError, StackTransport, TransportError,
    UnsupportedQuantumOperation,
)
from stdlib.bit import absence, agreement, disagreement
from stdlib.math import dagba, gbe, ku, papo, pin, yo


class StandardLibraryTests(unittest.TestCase):
    def test_math_wrappers_use_native_semantics(self):
        self.assertEqual(
            [papo(9, 4), yo(9, 4), dagba(9, 4), pin(9, 4), ku(9, 4), gbe(2, 5)],
            [13, 5, 36, 2.25, 1, 32],
        )

    def test_bit_relations(self):
        self.assertEqual(agreement(0b1100, 0b1010), 0b1000)
        self.assertEqual(disagreement(0b1100, 0b1010), 0b0110)
        self.assertEqual(absence(0b1100, 0b1010, 4), 0b0001)


class CanonicalExceptionTests(unittest.TestCase):
    def test_exception_hierarchy(self):
        classes = (
            RelationError, TransportError, MemoryError, QuantumDomainError,
            UnsupportedQuantumOperation, PermissionDenied, ExecutionError,
            CompilerError,
        )
        for exception_type in classes:
            self.assertTrue(issubclass(exception_type, IfaError))
        self.assertTrue(issubclass(StackTransport, TransportError))


if __name__ == "__main__":
    unittest.main()
