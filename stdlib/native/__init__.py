"""Canonical native-operation and native-function dispatch wrappers."""

from core.operations import execute_operation, normalise_operation
from runtime.native_functions import execute_native_function


def operation(name, a, b):
    return execute_operation(normalise_operation(name), a, b)


def function(name, *arguments):
    return execute_native_function(name, list(arguments))


__all__ = ["operation", "function"]
