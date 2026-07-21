# Exception System

`core/exceptions.py` defines the canonical hierarchy rooted at `IfaError`: RelationError, TransportError, MemoryError, QuantumDomainError, UnsupportedQuantumOperation, StackTransport, PermissionDenied, ExecutionError, and CompilerError.

Subsystems should raise the narrowest applicable exception and retain the original exception as their cause when translating boundaries. Shell diagnostics render source context without changing exception or parser interfaces.
