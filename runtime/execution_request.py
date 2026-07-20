from dataclasses import dataclass


@dataclass
class ExecutionRequest:

    operator_name: str
    operator: dict

    operand_a: object
    operand_b: object

