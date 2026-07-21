# Backend Architecture

`runtime/backend_manager.py` selects a backend named `python`, `rtl`, or `quantum`. Every backend implements the existing `execute(request)` contract and returns the logical result expected by Runtime. `ExecutionRequest` is the stable boundary: compilers and language features do not depend on backend implementation details.

The Python backend is the logical reference. The RTL backend targets the IFÁ processor and native instruction flow. The quantum backend maps the same native operation names into verified relation-frame circuits or reversible native oracles. Adding a backend must not add syntax, change AST nodes, or bypass Runtime.
