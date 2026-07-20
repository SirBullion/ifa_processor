from dataclasses import dataclass, field


# ============================================================
# Base Node
# ============================================================

@dataclass
class Node:

    location: "SourceLocation | None" = field(
        default=None,
        kw_only=True,
    )


@dataclass(frozen=True)
class SourceLocation:

    source: str

    line: int

    column: int = 1


# ============================================================
# Program
# ============================================================

@dataclass
class ProgramNode(Node):

    statements: list = field(default_factory=list)


@dataclass
class BlockNode(Node):

    statements: list = field(default_factory=list)


# ============================================================
# Expressions
# ============================================================

@dataclass
class LiteralNode(Node):

    value: object


@dataclass
class VariableNode(Node):

    name: str


@dataclass
class UnaryExpressionNode(Node):

    operator: str

    operand: Node


@dataclass
class BinaryExpressionNode(Node):

    operator_name: str

    operator: object

    left: Node

    right: Node


@dataclass
class BooleanExpressionNode(Node):

    operator: str

    left: Node

    right: Node


@dataclass
class ListNode(Node):

    elements: list = field(default_factory=list)


@dataclass
class IndexNode(Node):

    collection: Node

    index: Node


# ============================================================
# Statements
# ============================================================

@dataclass
class AssignmentNode(Node):

    variable: str

    expression: Node


@dataclass
class IndexAssignmentNode(Node):

    target: IndexNode

    expression: Node


@dataclass
class ExpressionStatementNode(Node):

    expression: Node


@dataclass
class IfNode(Node):

    condition: Node

    then_block: BlockNode

    else_block: BlockNode | None = None


@dataclass
class WhileNode(Node):

    condition: Node

    body: BlockNode


@dataclass
class ForNode(Node):

    variable: str

    start: Node

    end: Node

    body: BlockNode


@dataclass
class ForeachNode(Node):

    variable: str

    iterable: Node

    body: BlockNode


@dataclass
class FunctionNode(Node):

    name: str

    parameters: list

    body: BlockNode


@dataclass
class CallNode(Node):

    name: str

    arguments: list


@dataclass
class ReturnNode(Node):

    expression: Node | None = None


@dataclass
class BreakNode(Node):

    pass


@dataclass
class ContinueNode(Node):

    pass


@dataclass
class ImportNode(Node):

    path: str


@dataclass
class ModuleNode(Node):

    name: str

    body: BlockNode
