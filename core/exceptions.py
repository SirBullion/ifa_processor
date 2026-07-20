"""Canonical exception hierarchy for the IFÁ V4.5 software stack."""


class IfaError(Exception):
    """Base class for canonical IFÁ failures."""


class RelationError(IfaError):
    pass


class TransportError(IfaError):
    pass


class MemoryError(IfaError):
    pass


class QuantumDomainError(IfaError, ValueError):
    pass


class UnsupportedQuantumOperation(IfaError, RuntimeError):
    pass


class StackTransport(TransportError):
    pass


class PermissionDenied(IfaError, PermissionError):
    pass


class ExecutionError(IfaError, RuntimeError):
    pass


class CompilerError(IfaError, RuntimeError):
    pass
