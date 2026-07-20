from core.operations import execute_operation


class RTLBackend:
    """
    RTL Backend.

    Behavioral execution model for IR validation against generated RTL.
    """

    def execute(self, request):

        return execute_operation(
            request.operator_name,
            request.operand_a,
            request.operand_b,
        )


rtl_backend = RTLBackend()
