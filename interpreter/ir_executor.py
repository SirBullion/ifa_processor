from pathlib import Path

from compiler.ast_optimizer import ast_optimizer
from compiler.ir import IRProgram, ir_lowerer
from interpreter.environment import environment
from language_v45.kernel import kernel
from runtime.execution_request import ExecutionRequest
from runtime.native_functions import NATIVE_FUNCTIONS, execute_native_function
from runtime.runtime import runtime


RUNTIME_OPERATIONS = {
    "ADD": "PAPO", "SUB": "YO", "MUL": "DAGBA", "DIV": "PIN",
    "MOD": "KU", "POW": "GBE", "CMP_EQ": "SEDA", "CMP_GT": "JU",
    "CMP_LT": "KERE",
}


class IRExecutor:
    def __init__(self):
        self.program = None
        self.result = None
        self.imported_sources = set()
        self.import_stack = []
        self.modules = {}

    def execute(self, program):
        self.program = program
        self.modules.update(program.modules)
        self.result = None
        self.execute_instructions(program.instructions, {})
        return self.result

    @staticmethod
    def labels(instructions):
        return {
            instruction.operands[0]: index
            for index, instruction in enumerate(instructions)
            if instruction.opcode == "LABEL"
        }

    @staticmethod
    def value(registers, operand):
        if isinstance(operand, str) and operand.startswith("r"):
            return registers[operand]
        return operand

    def runtime_operation(self, opcode, left, right):
        name = RUNTIME_OPERATIONS[opcode]
        request = ExecutionRequest(name, kernel.operators[name], left, right)
        return runtime.execute(request)["result"]

    def execute_instructions(self, instructions, registers):
        labels = self.labels(instructions)
        pc = 0
        while pc < len(instructions):
            instruction = instructions[pc]
            op, args = instruction.opcode, instruction.operands
            if op in ("LABEL", "HALT"):
                if op == "HALT": break
            elif op == "LOAD_CONST": registers[args[0]] = args[1]
            elif op == "LOAD": registers[args[0]] = environment.get(args[1])
            elif op == "STORE": environment.assign(args[0], self.value(registers, args[1]))
            elif op in RUNTIME_OPERATIONS:
                registers[args[0]] = self.runtime_operation(op, self.value(registers, args[1]), self.value(registers, args[2]))
            elif op == "NOT": registers[args[0]] = int(not bool(self.value(registers, args[1])))
            elif op == "BOOL_AND": registers[args[0]] = int(bool(self.value(registers, args[1])) and bool(self.value(registers, args[2])))
            elif op == "BOOL_OR": registers[args[0]] = int(bool(self.value(registers, args[1])) or bool(self.value(registers, args[2])))
            elif op == "BUILD_LIST": registers[args[0]] = [self.value(registers, item) for item in args[1]]
            elif op == "LOAD_INDEX": registers[args[0]] = self.value(registers, args[1])[self.value(registers, args[2])]
            elif op == "STORE_INDEX": self.value(registers, args[0])[self.value(registers, args[1])] = self.value(registers, args[2])
            elif op == "JUMP": pc = labels[args[0]]; continue
            elif op == "JUMP_IF_FALSE":
                if not bool(self.value(registers, args[0])): pc = labels[args[1]]; continue
            elif op == "CALL":
                values = [self.value(registers, item) for item in args[2]]
                registers[args[0]] = self.call(args[1], values, instruction)
            elif op == "RETURN": return self.value(registers, args[0]) if args[0] is not None else None
            elif op == "RESULT": self.result = self.value(registers, args[0])
            elif op == "RANGE_INIT":
                start, end = self.value(registers, args[1]), self.value(registers, args[2])
                step = -1 if start > end else 1
                registers[args[0]] = iter(range(start, end + step, step))
            elif op == "ITER_INIT": registers[args[0]] = iter(self.value(registers, args[1]))
            elif op == "ITER_NEXT":
                try: registers[args[0]] = next(registers[args[1]])
                except StopIteration: pc = labels[args[2]]; continue
            elif op == "IMPORT": self.execute_import(args[0], instruction)
            else: raise RuntimeError(f"Unknown IR opcode '{op}'.")
            pc += 1
        return None

    def call(self, name, arguments, instruction):
        if name in NATIVE_FUNCTIONS:
            return execute_native_function(name, arguments)
        if name not in self.program.functions:
            raise NameError(f"Undefined function '{name}'.")
        if "." in name:
            module_name, function_name = name.split(".", 1)
            exports = self.program.modules.get(module_name)
            caller = environment.current_frame
            internal_call = (
                caller is not None
                and caller.function_name.startswith(module_name + ".")
            )
            if exports is not None and function_name not in exports and not internal_call:
                raise NameError(
                    f"Function '{name}' is private and is not exported by module "
                    f"'{module_name}'."
                )
        function = self.program.functions[name]
        if len(arguments) != len(function.parameters):
            raise TypeError(f"Function {name} expects {len(function.parameters)} arguments; received {len(arguments)}.")
        parameters = dict(zip(function.parameters, arguments))
        environment.push_frame(name, parameters, return_address=instruction)
        try: return self.execute_instructions(function.instructions, {})
        finally: environment.pop_frame()

    def execute_import(self, path, instruction):
        requested = Path(path)
        source = instruction.location.source if instruction.location else "<source>"
        base = Path.cwd() if source.startswith("<") else Path(source).resolve().parent
        source_path = (requested if requested.is_absolute() else base / requested).resolve()
        if source_path in self.imported_sources: return
        if source_path in self.import_stack: raise RuntimeError(f"Circular import detected: {source_path}")
        from parser.parser import parser
        self.import_stack.append(source_path)
        try:
            ast = parser.parse_program(source_path.read_text(encoding="utf-8"), source_name=str(source_path))
            imported = ir_lowerer.lower(ast_optimizer.optimize(ast))
            self.program.functions.update(imported.functions)
            self.program.modules.update(imported.modules)
            self.modules.update(imported.modules)
            self.execute_instructions(imported.instructions, {})
            self.imported_sources.add(source_path)
        finally: self.import_stack.pop()
