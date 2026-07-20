from runtime.runtime import runtime


VARIABLES = {}


class StatementService:

    def execute(self, parse_object):

        if parse_object.statement == "LET":

            VARIABLES[
                parse_object.variable.upper()
            ] = parse_object.value

            return {
                "service": "Statement",
                "status": "assigned",
                "variable": parse_object.variable.upper(),
                "value": parse_object.value,
            }

        raise NotImplementedError(
            f"Unknown statement: {parse_object.statement}"
        )


statement_service = StatementService()
