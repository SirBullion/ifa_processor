"""Quantum backend for the canonical IFÁ V4.5 ExecutionRequest interface."""

from core.exceptions import UnsupportedQuantumOperation
from core.operations import normalise_operation
from quantum.comparison import SUPPORTED_OPERATIONS
from quantum.measurement import execute_native_operation


class QuantumBackend:
    supported_operations = SUPPORTED_OPERATIONS

    def __init__(self):
        self.last_execution = None

    def execute(self, request):
        operation = normalise_operation(request.operator_name)
        if operation not in self.supported_operations:
            supported = ", ".join(sorted(self.supported_operations))
            raise UnsupportedQuantumOperation(
                f"Quantum backend does not implement '{operation}'. "
                f"Existing verified quantum operations: {supported}."
            )
        self.last_execution = execute_native_operation(
            operation,
            request.operand_a,
            request.operand_b,
        )
        return self.last_execution.logical_result


quantum_backend = QuantumBackend()
