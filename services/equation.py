from runtime.runtime import runtime

from services.statement import VARIABLES


class EquationService:

    def execute(self, parse_object):

        result = runtime.execute(parse_object)

        VARIABLES[
            parse_object.variable.upper()
        ] = result["result"]

        return {
            "service": "Equation",
            "status": "assigned",
            "variable": parse_object.variable.upper(),
            "value": result["result"],
        }


equation_service = EquationService()

