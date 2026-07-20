from dataclasses import fields, replace

from core.operations import execute_operation
from parser.nodes import (
    AssignmentNode, BinaryExpressionNode, BlockNode, BooleanExpressionNode,
    BreakNode, CallNode, ContinueNode, IfNode, IndexNode, ListNode,
    LiteralNode, Node, ProgramNode, ReturnNode, UnaryExpressionNode,
    VariableNode, WhileNode, ForNode, ForeachNode, FunctionNode,
    IndexAssignmentNode,
)


class ASTOptimizer:
    """Semantics-preserving optimization at the existing AST optimizer hook."""

    def optimize(self, node):
        if not isinstance(node, Node):
            return node

        if isinstance(node, (ProgramNode, BlockNode)):
            return self._optimize_sequence(node)

        updates = {}
        for node_field in fields(node):
            if node_field.name == "location":
                continue
            value = getattr(node, node_field.name)
            if isinstance(value, Node):
                updates[node_field.name] = self.optimize(value)
            elif isinstance(value, list):
                updates[node_field.name] = [
                    self.optimize(item) if isinstance(item, Node) else item
                    for item in value
                ]

        optimized = replace(node, **updates) if updates else node
        return self._simplify_expression(optimized)

    def _optimize_sequence(self, node):
        constants = {}
        expressions = {}
        output = []

        for original in node.statements:
            # Do not push sequence constants through a loop body: variables
            # known at loop entry may be reassigned on every iteration.  For
            # an IF the condition is evaluated at the current sequence point,
            # but each branch is optimized as its own sequence.
            if isinstance(original, (WhileNode, ForNode, ForeachNode, FunctionNode)):
                substituted = original
            elif isinstance(original, IfNode):
                substituted = replace(
                    original,
                    condition=self._substitute(original.condition, constants),
                )
            else:
                substituted = self._substitute(original, constants)
            statement = self.optimize(substituted)

            # Constant-condition unreachable branch elimination.
            if isinstance(statement, IfNode) and isinstance(statement.condition, LiteralNode):
                selected = statement.then_block if bool(statement.condition.value) else statement.else_block
                if selected is not None:
                    output.extend(selected.statements)
                constants.clear(); expressions.clear()
                continue

            if (
                isinstance(statement, WhileNode)
                and isinstance(statement.condition, LiteralNode)
                and not bool(statement.condition.value)
            ):
                constants.clear(); expressions.clear()
                continue

            if isinstance(statement, AssignmentNode):
                name = statement.variable.upper()
                key = self._expression_key(statement.expression)
                if key is not None and key in expressions:
                    statement = replace(
                        statement,
                        expression=VariableNode(
                            name=expressions[key], location=statement.expression.location
                        ),
                    )

                # Any assignment may invalidate expressions containing the
                # assigned name. Clearing is conservative and safe.
                expressions.clear()
                if isinstance(statement.expression, LiteralNode):
                    constants[name] = statement.expression
                else:
                    constants.pop(name, None)
                    key = self._expression_key(statement.expression)
                    if key is not None:
                        expressions[key] = name
            elif isinstance(statement, (IfNode, WhileNode, ForNode, ForeachNode,
                                        FunctionNode, IndexAssignmentNode)):
                constants.clear(); expressions.clear()

            output.append(statement)

            # Dead/unreachable code following an unconditional transfer.
            if isinstance(statement, (ReturnNode, BreakNode, ContinueNode)):
                break

        return replace(node, statements=output)

    def _substitute(self, node, constants):
        if isinstance(node, VariableNode):
            literal = constants.get(node.name.upper())
            return replace(literal, location=node.location) if literal else node
        if not isinstance(node, Node):
            return node

        updates = {}
        for node_field in fields(node):
            if node_field.name == "location":
                continue
            value = getattr(node, node_field.name)
            if isinstance(value, Node):
                updates[node_field.name] = self._substitute(value, constants)
            elif isinstance(value, list):
                updates[node_field.name] = [
                    self._substitute(item, constants) if isinstance(item, Node) else item
                    for item in value
                ]
        return replace(node, **updates) if updates else node

    def _simplify_expression(self, node):
        if isinstance(node, BinaryExpressionNode):
            if isinstance(node.left, LiteralNode) and isinstance(node.right, LiteralNode):
                try:
                    value = execute_operation(
                        node.operator_name, node.left.value, node.right.value
                    )
                except (TypeError, ValueError, ArithmeticError):
                    return node
                return LiteralNode(value=value, location=node.location)

            zero_left = isinstance(node.left, LiteralNode) and node.left.value == 0
            zero_right = isinstance(node.right, LiteralNode) and node.right.value == 0
            one_left = isinstance(node.left, LiteralNode) and node.left.value == 1
            one_right = isinstance(node.right, LiteralNode) and node.right.value == 1
            op = node.operator_name
            if op == "PAPO" and zero_left: return node.right
            if op in ("PAPO", "YO") and zero_right: return node.left
            if op == "DAGBA" and one_left: return node.right
            if op in ("DAGBA", "PIN", "GBE") and one_right: return node.left

        if isinstance(node, UnaryExpressionNode):
            if node.operator == "NOT" and isinstance(node.operand, LiteralNode):
                return LiteralNode(value=int(not bool(node.operand.value)), location=node.location)

        if isinstance(node, BooleanExpressionNode):
            if isinstance(node.left, LiteralNode) and isinstance(node.right, LiteralNode):
                if node.operator == "AND":
                    value = int(bool(node.left.value) and bool(node.right.value))
                elif node.operator == "OR":
                    value = int(bool(node.left.value) or bool(node.right.value))
                else:
                    return node
                return LiteralNode(value=value, location=node.location)
        return node

    def _expression_key(self, node):
        """Hash pure expressions for conservative local CSE."""
        if isinstance(node, CallNode):
            return None
        if isinstance(node, LiteralNode):
            return ("literal", repr(node.value))
        if isinstance(node, VariableNode):
            return ("variable", node.name.upper())
        if isinstance(node, (BinaryExpressionNode, BooleanExpressionNode)):
            left = self._expression_key(node.left)
            right = self._expression_key(node.right)
            if left is None or right is None: return None
            operator = getattr(node, "operator_name", getattr(node, "operator", None))
            return (node.__class__.__name__, operator, left, right)
        if isinstance(node, UnaryExpressionNode):
            operand = self._expression_key(node.operand)
            return None if operand is None else ("unary", node.operator, operand)
        if isinstance(node, ListNode):
            items = tuple(self._expression_key(item) for item in node.elements)
            return None if any(item is None for item in items) else ("list", items)
        if isinstance(node, IndexNode):
            collection = self._expression_key(node.collection)
            index = self._expression_key(node.index)
            return None if collection is None or index is None else ("index", collection, index)
        return None


ast_optimizer = ASTOptimizer()
