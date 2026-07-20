from parser.nodes import (
    AssignmentNode,
    ExpressionStatementNode,
    ReturnNode,
    BreakNode,
    ContinueNode,
    IndexAssignmentNode,
    IndexNode,
)

from parser.expression import expression_parser


class StatementParser:

    def normalize(self, word):

        return word.strip().upper()

    # -------------------------------------------------

    def parse(self, tokens):

        if len(tokens) == 1 and self.normalize(tokens[0]) == "BREAK":
            return BreakNode()

        if len(tokens) == 1 and self.normalize(tokens[0]) == "CONTINUE":
            return ContinueNode()

        if "=" in tokens:
            equals_position = tokens.index("=")

            if equals_position > 0 and self.normalize(tokens[0]) != "JE":
                target = expression_parser.parse(tokens[:equals_position])

                if not isinstance(target, IndexNode):
                    raise ValueError(
                        "Direct assignment requires an indexed list target."
                    )

                expression = expression_parser.parse(
                    tokens[equals_position + 1:]
                )
                return IndexAssignmentNode(
                    target=target,
                    expression=expression,
                )

        if tokens and self.normalize(tokens[0]) == "RETURN":

            expression = None

            if len(tokens) > 1:
                expression = expression_parser.parse(tokens[1:])

            return ReturnNode(expression=expression)

        #
        # Assignment
        #
        # JE KI A = 5
        # JE KI C = PAPO A ATI B
        #

        if (
            len(tokens) >= 5
            and self.normalize(tokens[0]) == "JE"
            and self.normalize(tokens[1]) == "KI"
            and tokens[3] == "="
        ):

            variable = tokens[2]

            expression = expression_parser.parse(
                tokens[4:]
            )

            return AssignmentNode(
                variable=variable,
                expression=expression,
            )

        #
        # Expression statement
        #
        # PAPO A ATI B
        #

        expression = expression_parser.parse(tokens)

        return ExpressionStatementNode(
            expression=expression
        )


statement_parser = StatementParser()
