"""
IFÁ Processor V4.5

Arithmetic Service

Receives a ParseObject and converts it into an
ExecutionRequest for the Runtime.

The Arithmetic Service does NOT:

    • parse commands
    • perform Φ-P8
    • build Relation Frames
    • execute the RMU

It only prepares the execution request.
"""

from runtime.execution_request import ExecutionRequest
from runtime.runtime import runtime


class ArithmeticService:

    def __init__(self):
        pass

    # --------------------------------------------------

    def execute(self, parse_object):

        request = ExecutionRequest(
            operator_name=parse_object.operator_name,
            operator=parse_object.operator,
            operand_a=parse_object.operand_a,
            operand_b=parse_object.operand_b,
        )

        return runtime.execute(request)


arithmetic_service = ArithmeticService()
