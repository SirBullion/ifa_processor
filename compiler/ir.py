from dataclasses import dataclass, field
import json


@dataclass
class IRInstruction:
    opcode: str
    operands: tuple = field(default_factory=tuple)
    location: object | None = None

    def __str__(self):
        values = ",".join(self._format(value) for value in self.operands)
        return f"{self.opcode} {values}".rstrip()

    @staticmethod
    def _format(value):
        if isinstance(value, str) and value.startswith(("r", "label_")):
            return value
        return json.dumps(value, ensure_ascii=False)


@dataclass
class IRFunction:
    name: str
    parameters: list[str] = field(default_factory=list)
    instructions: list[IRInstruction] = field(default_factory=list)


@dataclass
class IRProgram:
    instructions: list[IRInstruction] = field(default_factory=list)
    functions: dict[str, IRFunction] = field(default_factory=dict)
    modules: dict[str, list[str]] = field(default_factory=dict)
    source_statements: list = field(default_factory=list, repr=False)
    location: object | None = None

    @property
    def statements(self):
        return self.source_statements

    def to_text(self):
        lines = [".main"]
        lines.extend(str(instruction) for instruction in self.instructions)
        for function in self.functions.values():
            lines.append("")
            lines.append(
                f".function {function.name}({','.join(function.parameters)})"
            )
            lines.extend(str(instruction) for instruction in function.instructions)
            lines.append(".end")
        return "\n".join(lines) + "\n"


class IRLowerer:
    def lower(self, program):
        from compiler.ir_generator import IRGenerator
        return IRGenerator().generate(program)


ir_lowerer = IRLowerer()
