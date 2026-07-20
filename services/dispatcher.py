#========================================
"""
IFÁ Processor V4.5
Service Dispatcher

The dispatcher receives a ParseObject and routes it
to the correct service.

It does NOT execute the processor itself.
"""

from services.arithmetic import ArithmeticService
from services.relation import RelationService
from services.statement import StatementService
from services.equation import EquationService



class Dispatcher:

    def __init__(self):

        self.services = {
            "arithmetic": ArithmeticService(),
            "relation": RelationService(),
            "statement": StatementService(),
            "equation": EquationService(),
        }

    # --------------------------------------------------

    def dispatch(self, parse_object):

        # ----------------------------------------------
        # Statements
        # ----------------------------------------------

        if parse_object.statement is not None:

            service = self.services["statement"]

            return service.execute(parse_object)

        # ----------------------------------------------
        # Operators
        # ----------------------------------------------

        operator = parse_object.operator

        family = operator.get("family")

        if family is None:
            raise ValueError(
                f"Operator '{parse_object.operator_name}' has no family."
            )

        family = family.lower()

        if family not in self.services:
            raise NotImplementedError(
                f"No service registered for '{family}'."
            )

        service = self.services[family]

        return service.execute(parse_object)


dispatcher = Dispatcher()
