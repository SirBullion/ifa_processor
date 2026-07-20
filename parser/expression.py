import ast
import re

from language_v45.kernel import kernel

from parser.nodes import (
    LiteralNode,
    VariableNode,
    UnaryExpressionNode,
    BinaryExpressionNode,
    BooleanExpressionNode,
    CallNode,
    IndexNode,
    ListNode,
)


OPERATORS = kernel.operators
NUMBERS = kernel.numbers

COMPARISONS = {
    "==": ("SEDA", False),
    "!=": ("SEDA", True),
    ">": ("JU", False),
    "<": ("KERE", False),
    ">=": ("KERE", True),
    "<=": ("JU", True),
    "SEDA": ("SEDA", False),
    "JU": ("JU", False),
    "KERE": ("KERE", False),
    "KERÉ": ("KERE", False),
}


class ExpressionParser:

    def normalize(self, word):

        return word.strip().upper()

    # ---------------------------------------------

    def parse_operand(self, token):

        token = token.strip()

        if (
            len(token) >= 2
            and token[0] in ('"', "'")
            and token[-1] == token[0]
        ):
            return LiteralNode(ast.literal_eval(token))

        if re.fullmatch(r"[+-]?\d+", token):
            return LiteralNode(int(token))

        if re.fullmatch(
            r"[+-]?(?:\d+\.\d*|\d*\.\d+)(?:[eE][+-]?\d+)?",
            token,
        ):
            return LiteralNode(float(token))

        name = self.normalize(token)

        if name == "TRUE":
            return LiteralNode(True)

        if name == "FALSE":
            return LiteralNode(False)

        if name in NUMBERS:
            return LiteralNode(NUMBERS[name])

        return VariableNode(name)

    # ---------------------------------------------

    def parse_expression(self, tokens, position=0):

        if position >= len(tokens):
            raise ValueError("Expected an expression.")

        token = tokens[position]

        if token == "[":
            return self.parse_list(tokens, position)

        # Parentheses group an expression without changing its value.
        if token == "(":
            depth = 1
            closing_position = position + 1

            while closing_position < len(tokens) and depth:
                if tokens[closing_position] == "(":
                    depth += 1
                elif tokens[closing_position] == ")":
                    depth -= 1

                closing_position += 1

            if depth:
                raise ValueError("Expected closing parenthesis.")

            expression = self.parse(
                tokens[position + 1:closing_position - 1]
            )
            return self.parse_indexes(
                expression,
                tokens,
                closing_position,
            )

        if token == ")":
            raise ValueError("Unexpected closing parenthesis.")

        operator_name = self.normalize(token)

        if operator_name == "PE":
            expression, position = self.parse_call(tokens, position)
            return self.parse_indexes(expression, tokens, position)

        if operator_name == "NOT":
            operand, position = self.parse_expression(
                tokens,
                position + 1,
            )
            return UnaryExpressionNode(
                operator="NOT",
                operand=operand,
            ), position

        if operator_name in ("AND", "OR"):
            left, position = self.parse_expression(
                tokens,
                position + 1,
            )

            if (
                position >= len(tokens)
                or self.normalize(tokens[position]) != "ATI"
            ):
                raise ValueError(
                    f"Expected keyword ATI in {operator_name} expression."
                )

            right, position = self.parse_expression(
                tokens,
                position + 1,
            )
            return BooleanExpressionNode(
                operator=operator_name,
                left=left,
                right=right,
            ), position

        # IFÁ expressions use prefix operators:
        #     PAPO <expression> ATI <expression>
        # Parsing each operand recursively permits nesting on either side.
        if operator_name in OPERATORS:
            operator = OPERATORS[operator_name]

            if operator.get("args") != 2:
                raise ValueError(
                    f"IFÁ operator {operator_name} is not executable."
                )

            if position + 1 < len(tokens) and tokens[position + 1] == "(":
                depth = 1
                closing_position = position + 2

                while closing_position < len(tokens) and depth:
                    if tokens[closing_position] == "(":
                        depth += 1
                    elif tokens[closing_position] == ")":
                        depth -= 1

                    closing_position += 1

                if depth:
                    raise ValueError(
                        f"Expected closing parenthesis for {operator_name}."
                    )

                try:
                    expression = self.parse(
                        [operator_name]
                        + tokens[position + 2:closing_position - 1]
                    )
                except ValueError:
                    inner_tokens = tokens[
                        position + 2:closing_position - 1
                    ]
                    separator = self.find_top_level_ati(inner_tokens)

                    wrapper_is_complete = (
                        closing_position >= len(tokens)
                        or tokens[closing_position] in (")", "]", ",")
                    )

                    if separator is not None and wrapper_is_complete:
                        left = self.parse_wrapper_component(
                            inner_tokens[:separator]
                        )
                        right = self.parse(
                            inner_tokens[separator + 1:]
                        )
                        expression = BinaryExpressionNode(
                            operator_name=operator_name,
                            operator=operator,
                            left=left,
                            right=right,
                        )
                        return self.parse_indexes(
                            expression,
                            tokens,
                            closing_position,
                        )
                else:
                    return self.parse_indexes(
                        expression,
                        tokens,
                        closing_position,
                    )

            left, position = self.parse_expression(
                tokens,
                position + 1,
            )

            if (
                position >= len(tokens)
                or self.normalize(tokens[position]) != "ATI"
            ):
                raise ValueError(
                    f"Expected keyword ATI in {operator_name} expression."
                )

            right, position = self.parse_expression(
                tokens,
                position + 1,
            )

            return BinaryExpressionNode(
                operator_name=operator_name,
                operator=operator,
                left=left,
                right=right,
            ), position

        if position + 1 < len(tokens) and tokens[position + 1] == "(":
            expression, position = self.parse_named_call(
                tokens,
                position,
            )
            return self.parse_indexes(expression, tokens, position)

        expression = self.parse_operand(token)
        return self.parse_indexes(expression, tokens, position + 1)

    def find_top_level_ati(self, tokens):

        depth = 0

        for position, token in enumerate(tokens):
            if token in ("(", "["):
                depth += 1
            elif token in (")", "]"):
                depth -= 1
            elif depth == 0 and self.normalize(token) == "ATI":
                return position

        return None

    def parse_wrapper_component(self, tokens):

        if (
            len(tokens) >= 4
            and self.normalize(tokens[0]) in OPERATORS
            and tokens[1] == "("
            and tokens[-1] == ")"
        ):
            depth = 0
            closes_at_end = False

            for position, token in enumerate(tokens[1:], 1):
                if token == "(":
                    depth += 1
                elif token == ")":
                    depth -= 1

                    if depth == 0:
                        closes_at_end = position == len(tokens) - 1
                        break

            if closes_at_end:
                return self.parse(tokens[2:-1])

        return self.parse(tokens)

    # ---------------------------------------------

    def find_infix_comparison(self, tokens):

        depth = 0

        for position, token in enumerate(tokens):
            if token == "(":
                depth += 1
            elif token == ")":
                depth -= 1
            elif depth == 0 and self.normalize(token) in COMPARISONS:
                if token in ("==", "!=", ">", "<", ">=", "<="):
                    return position

                if position > 0:
                    return position

        return None

    def build_comparison(self, operator_token, left, right):

        relation_name, negate = COMPARISONS[
            self.normalize(operator_token)
        ]
        expression = BinaryExpressionNode(
            operator_name=relation_name,
            operator=OPERATORS[relation_name],
            left=left,
            right=right,
        )

        if negate:
            return UnaryExpressionNode(
                operator="NOT",
                operand=expression,
            )

        return expression

    # ---------------------------------------------

    def parse_call(self, tokens, position):

        position += 1

        if position >= len(tokens):
            raise ValueError("Expected a function name after PE.")

        return self.parse_named_call(tokens, position)

    def parse_named_call(self, tokens, position):

        name = self.normalize(tokens[position])
        position += 1

        if position >= len(tokens) or tokens[position] != "(":
            raise ValueError(
                f"Expected '(' after function name {name}."
            )

        position += 1
        arguments = []

        if position < len(tokens) and tokens[position] == ")":
            return CallNode(name=name, arguments=[]), position + 1

        while True:
            argument, position = self.parse_expression(tokens, position)
            arguments.append(argument)

            if position >= len(tokens):
                raise ValueError(
                    f"Expected ')' after arguments to {name}."
                )

            delimiter = tokens[position]

            if delimiter == ")":
                return CallNode(
                    name=name,
                    arguments=arguments,
                ), position + 1

            if delimiter != ",":
                raise ValueError(
                    f"Expected ',' or ')' in call to {name}."
                )

            position += 1

            if position >= len(tokens) or tokens[position] == ")":
                raise ValueError(
                    f"Expected an argument after ',' in call to {name}."
                )

    # ---------------------------------------------

    def parse_list(self, tokens, position):

        position += 1
        elements = []

        if position < len(tokens) and tokens[position] == "]":
            return ListNode(elements=[]), position + 1

        while True:
            element, position = self.parse_expression(tokens, position)
            elements.append(element)

            if position >= len(tokens):
                raise ValueError("Expected closing ']' for list.")

            if tokens[position] == "]":
                return self.parse_indexes(
                    ListNode(elements=elements),
                    tokens,
                    position + 1,
                )

            if tokens[position] != ",":
                raise ValueError("Expected ',' or ']' in list.")

            position += 1

            if position >= len(tokens) or tokens[position] == "]":
                raise ValueError("Expected a list element after ','.")

    def parse_indexes(self, expression, tokens, position):

        while position < len(tokens) and tokens[position] == "[":
            depth = 1
            closing_position = position + 1

            while closing_position < len(tokens) and depth:
                if tokens[closing_position] == "[":
                    depth += 1
                elif tokens[closing_position] == "]":
                    depth -= 1

                closing_position += 1

            if depth:
                raise ValueError("Expected closing ']' for index.")

            index = self.parse(
                tokens[position + 1:closing_position - 1]
            )
            expression = IndexNode(
                collection=expression,
                index=index,
            )
            position = closing_position

        return expression, position

    # ---------------------------------------------

    def parse(self, tokens):

        if not tokens:
            raise ValueError("Expected an expression.")

        comparison_position = self.find_infix_comparison(tokens)

        if comparison_position is not None:
            if comparison_position == 0 or comparison_position == len(tokens) - 1:
                raise ValueError("Comparison requires two expressions.")

            left = self.parse(tokens[:comparison_position])
            right = self.parse(tokens[comparison_position + 1:])
            return self.build_comparison(
                tokens[comparison_position],
                left,
                right,
            )

        expression, position = self.parse_expression(tokens)

        if position != len(tokens):
            raise ValueError(
                f"Unexpected token in expression: {tokens[position]}"
            )

        return expression


expression_parser = ExpressionParser()
