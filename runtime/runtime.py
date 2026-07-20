"""
IFÁ Processor V4.5

Runtime

The Runtime is responsible for executing an
ExecutionRequest.

It coordinates the execution pipeline.

Current pipeline:

    Execution Request
            ↓
        (placeholder)
            ↓
        Execution Result

Future pipeline:

    Execution Request
            ↓
          Φ-P8
            ↓
     Relation Frame
            ↓
           RMU
            ↓
      Execution Result
"""

#!/usr/bin/env python3
"""
============================================================================
IFÁ Processor V4.5

Runtime

Executes a single ExecutionRequest using the canonical IFÁ native
operations.
============================================================================
"""
from runtime.execution_request import ExecutionRequest
from runtime.backend_manager import backend_manager


class Runtime:

    def execute(self, request: ExecutionRequest):

        result = backend_manager.backend.execute(request)

        return {
            "service": "Runtime",
            "backend": backend_manager.backend_name,
            "status": "executed",
            "operator": request.operator_name,
            "operand_a": request.operand_a,
            "operand_b": request.operand_b,
            "result": result,
        }


runtime = Runtime()
