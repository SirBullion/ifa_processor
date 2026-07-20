from compiler.ir import IRFunction, IRInstruction, IRProgram
from parser.nodes import (
    AssignmentNode, BinaryExpressionNode, BlockNode, BooleanExpressionNode,
    BreakNode, CallNode, ContinueNode, ExpressionStatementNode, ForNode,
    ForeachNode, FunctionNode, IfNode, ImportNode, IndexAssignmentNode,
    IndexNode, ListNode, LiteralNode, ModuleNode, ProgramNode, ReturnNode,
    UnaryExpressionNode, VariableNode, WhileNode,
)


OPCODES = {
    "PAPO": "ADD", "YO": "SUB", "DAGBA": "MUL", "PIN": "DIV",
    "KU": "MOD", "GBE": "POW", "SEDA": "CMP_EQ", "JU": "CMP_GT",
    "KERE": "CMP_LT",
}


class IRGenerator:
    def __init__(self):
        self.program = IRProgram()
        self.instructions = self.program.instructions
        self.register_number = 0
        self.label_number = 0
        self.loop_stack = []
        self.module_name = None
        self.module_exports = None
        self.module_functions = None

    def register(self):
        self.register_number += 1
        return f"r{self.register_number}"

    def label(self, prefix="label"):
        self.label_number += 1
        return f"label_{prefix}_{self.label_number}"

    def emit(self, opcode, *operands, node=None):
        instruction = IRInstruction(opcode, tuple(operands), getattr(node, "location", None))
        self.instructions.append(instruction)
        return instruction

    def generate(self, program):
        self.program.location = program.location
        self.program.source_statements = list(program.statements)
        self.statement(program)
        self.emit("HALT")
        return self.program

    def statement(self, node):
        if isinstance(node, (ProgramNode, BlockNode)):
            for statement in node.statements:
                self.statement(statement)
            return
        if isinstance(node, FunctionNode):
            self.function(node)
            return
        if isinstance(node, ModuleNode):
            previous = self.module_name
            previous_exports = self.module_exports
            previous_functions = self.module_functions
            self.module_name = node.name.upper()
            declared_functions = {
                statement.name.upper()
                for statement in node.body.statements
                if isinstance(statement, FunctionNode)
            }
            explicit_exports = set()
            for statement in node.body.statements:
                if (
                    isinstance(statement, ExpressionStatementNode)
                    and isinstance(statement.expression, CallNode)
                    and statement.expression.name.upper() == "EXPORT"
                ):
                    if len(statement.expression.arguments) != 1:
                        raise ValueError("EXPORT requires exactly one function name.")
                    argument = statement.expression.arguments[0]
                    if isinstance(argument, LiteralNode) and isinstance(argument.value, str):
                        explicit_exports.add(argument.value.upper())
                    elif isinstance(argument, VariableNode):
                        explicit_exports.add(argument.name.upper())
                    else:
                        raise ValueError("EXPORT expects a function name or string.")
            unknown = explicit_exports - declared_functions
            if unknown:
                raise ValueError(
                    "MODULE exports undefined function(s): " + ", ".join(sorted(unknown))
                )
            self.module_exports = explicit_exports or declared_functions
            self.module_functions = declared_functions
            self.statement(node.body)
            self.program.modules[node.name.upper()] = sorted(self.module_exports)
            self.module_name = previous
            self.module_exports = previous_exports
            self.module_functions = previous_functions
            return
        if isinstance(node, ImportNode):
            self.emit("IMPORT", node.path, node=node)
            return
        if (
            isinstance(node, ExpressionStatementNode)
            and isinstance(node.expression, CallNode)
            and node.expression.name.upper() == "EXPORT"
            and self.module_name
        ):
            return
        if isinstance(node, AssignmentNode):
            value = self.expression(node.expression)
            self.emit("STORE", node.variable.upper(), value, node=node)
            self.emit("RESULT", value, node=node)
            return
        if isinstance(node, IndexAssignmentNode):
            collection = self.expression(node.target.collection)
            index = self.expression(node.target.index)
            value = self.expression(node.expression)
            self.emit("STORE_INDEX", collection, index, value, node=node)
            self.emit("RESULT", value, node=node)
            return
        if isinstance(node, ExpressionStatementNode):
            value = self.expression(node.expression)
            self.emit("RESULT", value, node=node)
            return
        if isinstance(node, ReturnNode):
            value = self.expression(node.expression) if node.expression else None
            self.emit("RETURN", value, node=node)
            return
        if isinstance(node, IfNode):
            else_label, end_label = self.label("else"), self.label("endif")
            condition = self.expression(node.condition)
            self.emit("JUMP_IF_FALSE", condition, else_label, node=node)
            self.statement(node.then_block)
            self.emit("JUMP", end_label, node=node)
            self.emit("LABEL", else_label, node=node)
            if node.else_block:
                self.statement(node.else_block)
            self.emit("LABEL", end_label, node=node)
            return
        if isinstance(node, WhileNode):
            start, end = self.label("while"), self.label("endwhile")
            self.emit("LABEL", start, node=node)
            condition = self.expression(node.condition)
            self.emit("JUMP_IF_FALSE", condition, end, node=node)
            self.loop_stack.append((start, end))
            self.statement(node.body)
            self.loop_stack.pop()
            self.emit("JUMP", start, node=node)
            self.emit("LABEL", end, node=node)
            return
        if isinstance(node, ForNode):
            iterator, item = self.register(), self.register()
            start_value, end_value = self.expression(node.start), self.expression(node.end)
            start, end = self.label("for"), self.label("endfor")
            self.emit("RANGE_INIT", iterator, start_value, end_value, node=node)
            self.emit("LABEL", start, node=node)
            self.emit("ITER_NEXT", item, iterator, end, node=node)
            self.emit("STORE", node.variable.upper(), item, node=node)
            self.loop_stack.append((start, end)); self.statement(node.body); self.loop_stack.pop()
            self.emit("JUMP", start, node=node); self.emit("LABEL", end, node=node)
            return
        if isinstance(node, ForeachNode):
            iterator, item = self.register(), self.register()
            iterable = self.expression(node.iterable)
            start, end = self.label("foreach"), self.label("endforeach")
            self.emit("ITER_INIT", iterator, iterable, node=node); self.emit("LABEL", start, node=node)
            self.emit("ITER_NEXT", item, iterator, end, node=node); self.emit("STORE", node.variable.upper(), item, node=node)
            self.loop_stack.append((start, end)); self.statement(node.body); self.loop_stack.pop()
            self.emit("JUMP", start, node=node); self.emit("LABEL", end, node=node)
            return
        if isinstance(node, BreakNode):
            self.emit("JUMP", self.loop_stack[-1][1], node=node); return
        if isinstance(node, ContinueNode):
            self.emit("JUMP", self.loop_stack[-1][0], node=node); return
        raise TypeError(f"Cannot lower {node.__class__.__name__} to IR.")

    def function(self, node):
        name = node.name.upper()
        qualified = f"{self.module_name}.{name}" if self.module_name else name
        outer = self.instructions
        instructions = []
        self.instructions = instructions
        self.statement(node.body)
        if not instructions or instructions[-1].opcode != "RETURN":
            self.emit("RETURN", None, node=node)
        function = IRFunction(qualified, [p.upper() for p in node.parameters], instructions)
        self.program.functions[qualified] = function
        if self.module_name and name in self.module_exports:
            self.program.functions.setdefault(name, function)
        self.instructions = outer

    def expression(self, node):
        if isinstance(node, LiteralNode):
            dest = self.register(); self.emit("LOAD_CONST", dest, node.value, node=node); return dest
        if isinstance(node, VariableNode):
            dest = self.register(); self.emit("LOAD", dest, node.name.upper(), node=node); return dest
        if isinstance(node, BinaryExpressionNode):
            left, right, dest = self.expression(node.left), self.expression(node.right), self.register()
            self.emit(OPCODES[node.operator_name], dest, left, right, node=node); return dest
        if isinstance(node, UnaryExpressionNode):
            operand, dest = self.expression(node.operand), self.register(); self.emit("NOT", dest, operand, node=node); return dest
        if isinstance(node, BooleanExpressionNode):
            left, right, dest = self.expression(node.left), self.expression(node.right), self.register()
            self.emit("BOOL_" + node.operator, dest, left, right, node=node); return dest
        if isinstance(node, CallNode):
            arguments = tuple(self.expression(arg) for arg in node.arguments); dest = self.register()
            name = node.name.upper()
            if self.module_name and name in self.module_functions:
                name = f"{self.module_name}.{name}"
            self.emit("CALL", dest, name, arguments, node=node); return dest
        if isinstance(node, ListNode):
            values = tuple(self.expression(item) for item in node.elements); dest = self.register()
            self.emit("BUILD_LIST", dest, values, node=node); return dest
        if isinstance(node, IndexNode):
            collection, index, dest = self.expression(node.collection), self.expression(node.index), self.register()
            self.emit("LOAD_INDEX", dest, collection, index, node=node); return dest
        raise TypeError(f"Cannot lower expression {node.__class__.__name__}.")
