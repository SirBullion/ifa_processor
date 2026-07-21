# IFÁ V4.5 Compiler Architecture

The canonical pipeline is Source → Tokenizer → Parser → AST → Optimizer → IR Generator → IR Executor → ExecutionRequest → Runtime → BackendManager → Backend. Syntax and AST nodes are backend-independent. Arithmetic IR instructions are converted to `ExecutionRequest` objects; the executor never performs native arithmetic itself.

`compiler/ast_optimizer.py` performs conservative, semantics-preserving AST optimization. `compiler/ir_generator.py` lowers programs, functions, frames, branches, loops, arrays, modules, and calls into the permanent IFÁ IR. `interpreter/ir_executor.py` owns program control flow and stack frames. Runtime and backend selection remain below this layer.

Compilation errors must preserve source locations. The shell formats failures with `compiler/diagnostics.py` without changing parser contracts.
