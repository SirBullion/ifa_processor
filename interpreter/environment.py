from dataclasses import dataclass, field


@dataclass
class CallFrame:

    function_name: str
    parameters: dict = field(default_factory=dict)
    return_address: object | None = None
    parent: "CallFrame | None" = None
    variables: dict = field(default_factory=dict)

    def __post_init__(self):

        self.parameters = {
            name.upper(): value
            for name, value in self.parameters.items()
        }
        self.variables.update(self.parameters)


class Environment:

    def __init__(self):

        self.variables = {}
        self.call_stack = []

    # ---------------------------------------

    @property
    def current_frame(self):

        if not self.call_stack:
            return None

        return self.call_stack[-1]

    # ---------------------------------------

    def push_frame(
        self,
        function_name,
        parameters,
        return_address=None,
    ):

        frame = CallFrame(
            function_name=function_name.upper(),
            parameters=parameters,
            return_address=return_address,
            parent=self.current_frame,
        )
        self.call_stack.append(frame)

        return frame

    # ---------------------------------------

    def pop_frame(self):

        if not self.call_stack:
            raise RuntimeError("Cannot pop the global execution frame.")

        return self.call_stack.pop()

    # ---------------------------------------

    def define(self, name, value):

        name = name.upper()

        if self.current_frame is None:
            self.variables[name] = value
        else:
            self.current_frame.variables[name] = value

    # ---------------------------------------

    def assign(self, name, value):

        self.define(name, value)

    # ---------------------------------------

    def get(self, name):

        name = name.upper()

        frame = self.current_frame

        if frame is not None and name in frame.variables:
            return frame.variables[name]

        if name not in self.variables:
            raise NameError(
                f"Undefined variable '{name}'."
            )

        return self.variables[name]

    # ---------------------------------------

    def reset(self):

        self.variables.clear()
        self.call_stack.clear()


environment = Environment()
