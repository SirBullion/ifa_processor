"""Relation-frame and comparison wrappers."""

from core.operations import execute_operation
from runtime.frame_builder import build_relation_frame


def seda(a, b): return execute_operation("SEDA", a, b)
def ju(a, b): return execute_operation("JU", a, b)
def kere(a, b): return execute_operation("KERE", a, b)


__all__ = ["build_relation_frame", "seda", "ju", "kere"]
