from core.operations import execute_operation


class PythonBackend:

    def execute(self, request):

        return execute_operation(
            request.operator_name,
            request.operand_a,
            request.operand_b,
        )


python_backend = PythonBackend()
