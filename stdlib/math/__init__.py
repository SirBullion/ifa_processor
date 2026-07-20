"""Mathematical wrappers around canonical IFÁ native operations."""

from core.operations import execute_operation


def papo(a, b): return execute_operation("PAPO", a, b)
def yo(a, b): return execute_operation("YO", a, b)
def dagba(a, b): return execute_operation("DAGBA", a, b)
def pin(a, b): return execute_operation("PIN", a, b)
def ku(a, b): return execute_operation("KU", a, b)
def gbe(a, b): return execute_operation("GBE", a, b)


__all__ = ["papo", "yo", "dagba", "pin", "ku", "gbe"]
