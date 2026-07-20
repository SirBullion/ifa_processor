from pathlib import Path

from interpreter.visitor import NodeVisitor
from interpreter.environment import environment

from parser.nodes import (
    ProgramNode,
    BlockNode,
    LiteralNode,
    VariableNode,
    UnaryExpressionNode,
    BinaryExpressionNode,
    BooleanExpressionNode,
    AssignmentNode,
    ExpressionStatementNode,
    FunctionNode,
    CallNode,
    ReturnNode,
    IfNode,
    WhileNode,
    BreakNode,
    ContinueNode,
    ListNode,
    IndexNode,
    IndexAssignmentNode,
    ForNode,
    ForeachNode,
    ImportNode,
    ModuleNode,
    ProgramNode,
)

from runtime.runtime import runtime
from runtime.execution_request import ExecutionRequest
from runtime.native_functions import (
    NATIVE_FUNCTIONS,
    execute_native_function,
)
from language_v45.kernel import kernel
from compiler.ast_optimizer import ast_optimizer
from compiler.ir import IRProgram, ir_lowerer
from compiler.ir import IRFunction
from interpreter.ir_executor import IRExecutor


class FunctionReturn(Exception):

    def __init__(self, value):

        super().__init__()
        self.value = value


class LoopBreak(Exception):

    pass


class LoopContinue(Exception):

    pass


class Interpreter(NodeVisitor):

    def __init__(self):

        self.functions = {}
        self.loop_depth = 0
        self.modules = {}
        self.imported_sources = set()
        self.import_stack = []

    def execute(self, program):

        if not isinstance(program, ProgramNode):
            program = ProgramNode(
                statements=[program],
                location=getattr(program, "location", None),
            )

        optimized = ast_optimizer.optimize(program)
        intermediate = ir_lowerer.lower(optimized)
        intermediate.functions = {
            **{
                name: function
                for name, function in self.functions.items()
                if isinstance(function, IRFunction)
            },
            **intermediate.functions,
        }
        executor = IRExecutor()
        result = executor.execute(intermediate)
        self.imported_sources.update(executor.imported_sources)
        self.modules.update(executor.modules)
        self.functions.update(intermediate.functions)
        return result

    # ===================================================
    # Programs and blocks
    # ===================================================

    def execute_statements(self, statements):

        result = None

        for statement in statements:
            result = self.visit(statement)

        return result

    def visit_ProgramNode(self, node):

        return self.execute_statements(node.statements)

    def visit_IRProgram(self, node):
        return IRExecutor().execute(node)

    def visit_BlockNode(self, node):

        return self.execute_statements(node.statements)

    # ===================================================
    # Literals
    # ===================================================

    def visit_LiteralNode(self, node):

        return node.value

    # ===================================================
    # Variables
    # ===================================================

    def visit_VariableNode(self, node):

        return environment.get(node.name)

    def visit_ListNode(self, node):

        return [self.visit(element) for element in node.elements]

    def visit_IndexNode(self, node):

        collection = self.visit(node.collection)
        index = self.visit(node.index)

        if not isinstance(index, int) or isinstance(index, bool):
            raise TypeError("List index must be an integer.")

        return collection[index]

    # ===================================================
    # Boolean expressions
    # ===================================================

    def visit_UnaryExpressionNode(self, node):

        if node.operator == "NOT":
            return int(not bool(self.visit(node.operand)))

        raise ValueError(f"Unknown unary operator '{node.operator}'.")

    def visit_BooleanExpressionNode(self, node):

        if node.operator == "AND":
            left = self.visit(node.left)
            return int(bool(left) and bool(self.visit(node.right)))

        if node.operator == "OR":
            left = self.visit(node.left)
            return int(bool(left) or bool(self.visit(node.right)))

        raise ValueError(f"Unknown boolean operator '{node.operator}'.")

    # ===================================================
    # Binary Expressions
    # ===================================================

    def visit_BinaryExpressionNode(self, node):

        left = self.visit(node.left)
        right = self.visit(node.right)

        request = ExecutionRequest(
            operator_name=node.operator_name,
            operator=node.operator,
            operand_a=left,
            operand_b=right,
        )

        response = runtime.execute(request)

        return response["result"]

    # ===================================================
    # Assignment
    # ===================================================

    def visit_AssignmentNode(self, node):

        value = self.visit(node.expression)

        environment.assign(
            node.variable,
            value,
        )

        return value

    def visit_IndexAssignmentNode(self, node):

        collection = self.visit(node.target.collection)
        index = self.visit(node.target.index)

        if not isinstance(collection, list):
            raise TypeError("Indexed assignment requires a list target.")

        if not isinstance(index, int) or isinstance(index, bool):
            raise TypeError("List index must be an integer.")

        value = self.visit(node.expression)
        collection[index] = value

        return value

    # ===================================================
    # Standalone expression
    # ===================================================

    def visit_ExpressionStatementNode(self, node):

        return self.visit(node.expression)

    # ===================================================
    # Control flow
    # ===================================================

    def visit_IfNode(self, node):

        if bool(self.visit(node.condition)):
            return self.visit(node.then_block)

        if node.else_block is not None:
            return self.visit(node.else_block)

        return None

    def visit_WhileNode(self, node):

        result = None
        self.loop_depth += 1

        try:
            while bool(self.visit(node.condition)):
                try:
                    result = self.visit(node.body)
                except LoopContinue:
                    continue
                except LoopBreak:
                    break
        finally:
            self.loop_depth -= 1

        return result

    def execute_loop_body(self, body):

        try:
            return self.visit(body), None
        except LoopContinue:
            return None, "continue"
        except LoopBreak:
            return None, "break"

    def execute_runtime_operation(self, operator_name, left, right):

        request = ExecutionRequest(
            operator_name=operator_name,
            operator=kernel.operators[operator_name],
            operand_a=left,
            operand_b=right,
        )
        return runtime.execute(request)["result"]

    def visit_ForNode(self, node):

        current = self.visit(node.start)
        end = self.visit(node.end)

        if not isinstance(current, int) or isinstance(current, bool):
            raise TypeError("FUN range start must be an integer.")

        if not isinstance(end, int) or isinstance(end, bool):
            raise TypeError("FUN range end must be an integer.")

        descending = bool(
            self.execute_runtime_operation("JU", current, end)
        )
        step = -1 if descending else 1
        result = None
        self.loop_depth += 1

        try:
            while True:
                past_end_operator = "KERE" if descending else "JU"

                if self.execute_runtime_operation(
                    past_end_operator,
                    current,
                    end,
                ):
                    break

                environment.assign(node.variable, current)
                iteration_result, action = self.execute_loop_body(node.body)

                if action == "break":
                    break

                if action is None:
                    result = iteration_result

                current = self.execute_runtime_operation(
                    "PAPO",
                    current,
                    step,
                )
        finally:
            self.loop_depth -= 1

        return result

    def visit_ForeachNode(self, node):

        iterable = self.visit(node.iterable)

        if not isinstance(iterable, (list, str)):
            raise TypeError("FUN NINU requires a list or string.")

        result = None
        self.loop_depth += 1

        try:
            for item in iterable:
                environment.assign(node.variable, item)
                iteration_result, action = self.execute_loop_body(node.body)

                if action == "break":
                    break

                if action is None:
                    result = iteration_result
        finally:
            self.loop_depth -= 1

        return result

    # ===================================================
    # Imports and modules
    # ===================================================

    def visit_ImportNode(self, node):

        requested = Path(node.path)

        if not requested.is_absolute():
            source = node.location.source if node.location else "<source>"

            if source.startswith("<"):
                base = Path.cwd()
            else:
                base = Path(source).resolve().parent

            requested = base / requested

        source_path = requested.resolve()

        if source_path in self.imported_sources:
            return None

        if source_path in self.import_stack:
            chain = " -> ".join(str(path) for path in self.import_stack)
            raise RuntimeError(
                f"Circular import detected: {chain} -> {source_path}"
            )

        if not source_path.is_file():
            raise FileNotFoundError(
                f"Imported source file not found: {source_path}"
            )

        from parser.parser import parser

        self.import_stack.append(source_path)

        try:
            source_text = source_path.read_text(encoding="utf-8")
            program = parser.parse_program(
                source_text,
                source_name=str(source_path),
            )
            result = self.execute(program)
            self.imported_sources.add(source_path)
            return result
        finally:
            self.import_stack.pop()

    def visit_ModuleNode(self, node):

        exports = {}

        for statement in node.body.statements:
            result = self.visit(statement)

            if isinstance(statement, FunctionNode):
                qualified_name = f"{node.name.upper()}.{statement.name.upper()}"
                self.functions[qualified_name] = statement
                exports[statement.name.upper()] = statement

        self.modules[node.name.upper()] = exports

        return node

    def visit_BreakNode(self, node):

        if self.loop_depth == 0:
            raise RuntimeError("BREAK can only be used inside a loop.")

        raise LoopBreak()

    def visit_ContinueNode(self, node):

        if self.loop_depth == 0:
            raise RuntimeError("CONTINUE can only be used inside a loop.")

        raise LoopContinue()

    # ===================================================
    # Functions
    # ===================================================

    def visit_FunctionNode(self, node):

        self.functions[node.name.upper()] = node

        return node

    def visit_CallNode(self, node):

        name = node.name.upper()

        if name in NATIVE_FUNCTIONS:
            arguments = [
                self.visit(argument)
                for argument in node.arguments
            ]
            return execute_native_function(name, arguments)

        if name not in self.functions:
            raise NameError(f"Undefined function '{name}'.")

        function = self.functions[name]

        if len(node.arguments) != len(function.parameters):
            raise TypeError(
                f"Function {name} expects {len(function.parameters)} "
                f"arguments; received {len(node.arguments)}."
            )

        argument_values = [
            self.visit(argument)
            for argument in node.arguments
        ]
        parameters = dict(zip(function.parameters, argument_values))

        environment.push_frame(
            function_name=name,
            parameters=parameters,
            return_address=node,
        )

        caller_loop_depth = self.loop_depth
        self.loop_depth = 0

        try:
            try:
                return self.visit(function.body)
            except FunctionReturn as returned:
                return returned.value
        finally:
            self.loop_depth = caller_loop_depth
            environment.pop_frame()

    def visit_ReturnNode(self, node):

        if environment.current_frame is None:
            raise RuntimeError("RETURN can only be used inside a function.")

        value = None

        if node.expression is not None:
            value = self.visit(node.expression)

        raise FunctionReturn(value)

    # ===================================================
    # Interpreter state
    # ===================================================

    def reset(self):

        self.functions.clear()
        self.loop_depth = 0
        self.modules.clear()
        self.imported_sources.clear()
        self.import_stack.clear()
        environment.reset()


interpreter = Interpreter()
