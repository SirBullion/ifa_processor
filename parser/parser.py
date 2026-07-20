from dataclasses import fields

from parser.tokenizer import tokenizer
from parser.statement import statement_parser
from parser.expression import expression_parser
from parser.nodes import (
    BlockNode,
    FunctionNode,
    IfNode,
    ProgramNode,
    WhileNode,
    ForNode,
    ForeachNode,
    ImportNode,
    ModuleNode,
    Node,
    SourceLocation,
)


class IfaSyntaxError(SyntaxError, ValueError):

    pass


class Parser:

    def __init__(self):

        self.source_name = "<source>"
        self.error_line = 1

    def normalize(self, word):

        return word.strip().upper()

    def attach_location(self, node, location):

        if not isinstance(node, Node):
            return node

        if node.location is None:
            node.location = location

        for node_field in fields(node):
            if node_field.name == "location":
                continue

            value = getattr(node, node_field.name)

            if isinstance(value, Node):
                self.attach_location(value, location)
            elif isinstance(value, list):
                for item in value:
                    self.attach_location(item, location)

        return node

    def delimiter_balance(self, tokens):

        parentheses = 0
        brackets = 0

        for token in tokens:
            if token == "(":
                parentheses += 1
            elif token == ")":
                parentheses -= 1
            elif token == "[":
                brackets += 1
            elif token == "]":
                brackets -= 1

            if parentheses < 0 or brackets < 0:
                raise ValueError("Unexpected closing delimiter.")

        return parentheses, brackets

    def logical_line_complete(self, tokens):

        if not tokens:
            return False

        parentheses, brackets = self.delimiter_balance(tokens)

        if parentheses or brackets:
            return False

        keyword = self.normalize(tokens[0])

        if keyword in ("PARI", "TABI", "ISE", "MODULE", "GBA"):
            return True

        if keyword == "RETURN" and len(tokens) == 1:
            return False

        try:
            if keyword in ("BI", "NIGBATI"):
                expression_parser.parse(tokens[1:])
            elif keyword == "FUN":
                return "SI" in [
                    self.normalize(token) for token in tokens
                ] or (
                    len(tokens) > 3
                    and self.normalize(tokens[2]) == "NINU"
                )
            else:
                statement_parser.parse(tokens)
        except (ValueError, IndexError):
            return False

        return True

    def build_logical_lines(self, text):

        physical_lines = [
            (line_number, line.strip())
            for line_number, line in enumerate(text.splitlines(), 1)
            if line.strip()
        ]
        logical_lines = []
        buffer = []
        start_line = None

        comparison_continuations = {
            "==",
            "!=",
            ">",
            "<",
            ">=",
            "<=",
            "SEDA",
            "JU",
            "KERE",
            "KERÉ",
        }

        for physical_position, (line_number, line) in enumerate(
            physical_lines
        ):
            tokens = tokenizer.tokenize(line)
            keyword = self.normalize(tokens[0]) if tokens else ""

            if (
                buffer
                and keyword in ("PARI", "TABI")
                and self.delimiter_balance(buffer) == (0, 0)
            ):
                logical_lines.append((start_line, " ".join(buffer)))
                buffer = []
                start_line = None

            if start_line is None:
                start_line = line_number

            buffer.extend(tokens)

            next_token = None

            if physical_position + 1 < len(physical_lines):
                next_line = physical_lines[physical_position + 1][1]
                next_tokens = tokenizer.tokenize(next_line)

                if next_tokens:
                    next_token = self.normalize(next_tokens[0])

            continues_with_comparison = (
                next_token in comparison_continuations
            )

            if (
                self.logical_line_complete(buffer)
                and not continues_with_comparison
            ):
                logical_lines.append((start_line, " ".join(buffer)))
                buffer = []
                start_line = None

        if buffer:
            logical_lines.append((start_line, " ".join(buffer)))

        return logical_lines

    # -------------------------------------------------

    def parse_function_header(self, tokens):

        if len(tokens) < 4:
            raise ValueError(
                "Expected: ISE <NAME>(<PARAMETERS>)"
            )

        name = self.normalize(tokens[1])

        if tokens[2] != "(" or tokens[-1] != ")":
            raise ValueError(
                f"Invalid declaration for function {name}."
            )

        parameters = []
        position = 3

        if position == len(tokens) - 1:
            return name, parameters

        while position < len(tokens) - 1:
            parameter = tokens[position]

            if parameter in (",", "(", ")", "="):
                raise ValueError(
                    f"Expected a parameter name in function {name}."
                )

            parameters.append(self.normalize(parameter))
            position += 1

            if position == len(tokens) - 1:
                break

            if tokens[position] != ",":
                raise ValueError(
                    f"Expected ',' between parameters of {name}."
                )

            position += 1

            if position == len(tokens) - 1:
                raise ValueError(
                    f"Expected a parameter after ',' in function {name}."
                )

        if len(parameters) != len(set(parameters)):
            raise ValueError(
                f"Function {name} has duplicate parameters."
            )

        return name, parameters

    # -------------------------------------------------

    def parse_block(self, lines, position=0, terminators=None):

        statements = []
        terminators = set() if terminators is None else set(terminators)

        while position < len(lines):
            line_number, line = lines[position]
            self.error_line = line_number
            location = SourceLocation(
                source=self.source_name,
                line=line_number,
            )
            tokens = tokenizer.tokenize(line)
            keyword = self.normalize(tokens[0])

            if keyword in ("PARI", "TABI"):
                if len(tokens) != 1:
                    raise ValueError(
                        f"{keyword} must appear on its own line."
                    )

                if keyword not in terminators:
                    raise ValueError(f"Unexpected {keyword}.")

                return (
                    BlockNode(statements=statements),
                    position + 1,
                    keyword,
                )

            if keyword == "ISE":
                name, parameters = self.parse_function_header(tokens)
                body, position, terminator = self.parse_block(
                    lines,
                    position + 1,
                    terminators={"PARI"},
                )
                statements.append(
                    self.attach_location(FunctionNode(
                        name=name,
                        parameters=parameters,
                        body=body,
                    ), location)
                )
                continue

            if keyword == "MODULE":
                if len(tokens) != 2:
                    raise ValueError("Expected MODULE <NAME>.")

                body, position, terminator = self.parse_block(
                    lines,
                    position + 1,
                    terminators={"PARI"},
                )
                statements.append(
                    self.attach_location(
                        ModuleNode(
                            name=self.normalize(tokens[1]),
                            body=body,
                        ),
                        location,
                    )
                )
                continue

            if keyword == "GBA":
                if len(tokens) != 2:
                    raise ValueError("Expected GBA <SOURCE_FILE>.")

                path = tokens[1]

                if (
                    len(path) >= 2
                    and path[0] in ('"', "'")
                    and path[-1] == path[0]
                ):
                    path = path[1:-1]

                statements.append(
                    ImportNode(path=path, location=location)
                )
                position += 1
                continue

            if keyword == "BI":
                if len(tokens) == 1:
                    raise ValueError("BI requires a condition.")

                condition = expression_parser.parse(tokens[1:])
                then_block, position, terminator = self.parse_block(
                    lines,
                    position + 1,
                    terminators={"TABI", "PARI"},
                )
                else_block = None

                if terminator == "TABI":
                    else_block, position, terminator = self.parse_block(
                        lines,
                        position,
                        terminators={"PARI"},
                    )

                statements.append(
                    self.attach_location(IfNode(
                        condition=condition,
                        then_block=then_block,
                        else_block=else_block,
                    ), location)
                )
                continue

            if keyword == "NIGBATI":
                if len(tokens) == 1:
                    raise ValueError("NIGBATI requires a condition.")

                condition = expression_parser.parse(tokens[1:])
                body, position, terminator = self.parse_block(
                    lines,
                    position + 1,
                    terminators={"PARI"},
                )
                statements.append(
                    self.attach_location(
                        WhileNode(condition=condition, body=body),
                        location,
                    )
                )
                continue

            if keyword == "FUN":
                if len(tokens) < 4:
                    raise ValueError(
                        "Expected FUN <VARIABLE> LATI <START> SI <END> "
                        "or FUN <VARIABLE> NINU <ITERABLE>."
                    )

                variable = self.normalize(tokens[1])
                mode = self.normalize(tokens[2])

                if mode == "LATI":
                    si_positions = [
                        index
                        for index in range(3, len(tokens))
                        if self.normalize(tokens[index]) == "SI"
                    ]

                    if len(si_positions) != 1:
                        raise ValueError(
                            "FOR range requires exactly one SI separator."
                        )

                    separator = si_positions[0]
                    start = expression_parser.parse(tokens[3:separator])
                    end = expression_parser.parse(tokens[separator + 1:])
                    body, position, terminator = self.parse_block(
                        lines,
                        position + 1,
                        terminators={"PARI"},
                    )
                    statements.append(
                        self.attach_location(ForNode(
                            variable=variable,
                            start=start,
                            end=end,
                            body=body,
                        ), location)
                    )
                    continue

                if mode == "NINU":
                    iterable = expression_parser.parse(tokens[3:])
                    body, position, terminator = self.parse_block(
                        lines,
                        position + 1,
                        terminators={"PARI"},
                    )
                    statements.append(
                        self.attach_location(ForeachNode(
                            variable=variable,
                            iterable=iterable,
                            body=body,
                        ), location)
                    )
                    continue

                raise ValueError(
                    "FUN requires LATI for a range or NINU for iteration."
                )

            statements.append(
                self.attach_location(
                    statement_parser.parse(tokens),
                    location,
                )
            )
            position += 1

        if terminators:
            expected = " or ".join(sorted(terminators))
            raise ValueError(f"Expected {expected} to close block.")

        return BlockNode(statements=statements), position, None

    def parse_program(self, text, source_name="<source>"):

        #
        # Stage 1
        #

        self.source_name = source_name
        self.error_line = 1
        try:
            lines = self.build_logical_lines(text)
        except ValueError as error:
            raise IfaSyntaxError(
                f"{self.source_name}:{self.error_line}: {error}"
            ) from error

        if not lines:
            raise IfaSyntaxError(
                f"{self.source_name}:1: Empty command."
            )

        #
        # Stage 2
        #

        try:
            block, position, terminator = self.parse_block(lines)
        except SyntaxError:
            raise
        except (ValueError, IndexError) as error:
            raise IfaSyntaxError(
                f"{self.source_name}:{self.error_line}: {error}"
            ) from error

        if position != len(lines):
            raise ValueError("Unable to parse complete program.")

        return ProgramNode(
            statements=block.statements,
            location=SourceLocation(
                source=self.source_name,
                line=lines[0][0],
            ),
        )

    # -------------------------------------------------

    def parse(self, text, source_name="<source>"):

        program = self.parse_program(text, source_name=source_name)

        if len(program.statements) == 1:
            ast = program.statements[0]
        else:
            ast = program

        #
        # Stage 3
        #

        return ast


parser = Parser()
