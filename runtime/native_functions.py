import builtins


class NativeFunction:

    def __init__(self, name, function, minimum, maximum=None):

        self.name = name
        self.function = function
        self.minimum = minimum
        self.maximum = minimum if maximum is None else maximum

    def execute(self, arguments):

        count = len(arguments)

        if count < self.minimum or count > self.maximum:
            if self.minimum == self.maximum:
                expected = str(self.minimum)
            else:
                expected = f"{self.minimum} to {self.maximum}"

            raise TypeError(
                f"Native function {self.name} expects {expected} "
                f"arguments; received {count}."
            )

        return self.function(*arguments)


def native_print(*values):

    print(*values)
    return None


def native_input(*arguments):

    prompt = "" if not arguments else str(arguments[0])
    return builtins.input(prompt)


def native_type(value):

    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "BOOLEAN"
    if isinstance(value, int):
        return "INTEGER"
    if isinstance(value, float):
        return "FLOAT"
    if isinstance(value, str):
        return "STRING"
    if isinstance(value, list):
        return "LIST"

    return type(value).__name__.upper()


NATIVE_FUNCTIONS = {
    "PRINT": NativeFunction("PRINT", native_print, 0, 1000),
    "INPUT": NativeFunction("INPUT", native_input, 0, 1),
    "LEN": NativeFunction("LEN", len, 1),
    "TYPE": NativeFunction("TYPE", native_type, 1),
    "INT": NativeFunction("INT", int, 1),
    "FLOAT": NativeFunction("FLOAT", float, 1),
    "STRING": NativeFunction("STRING", str, 1),
    # EXPORT is consumed as module metadata by the existing IR lowerer.
    # Keeping a no-op native form preserves compatibility with the legacy
    # direct AST visitor.
    "EXPORT": NativeFunction("EXPORT", lambda name: str(name).upper(), 1),
}


def execute_native_function(name, arguments):

    normalized = name.strip().upper()

    if normalized not in NATIVE_FUNCTIONS:
        raise NameError(f"Undefined native function '{normalized}'.")

    return NATIVE_FUNCTIONS[normalized].execute(arguments)
