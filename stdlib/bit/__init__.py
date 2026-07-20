"""Universal IFÁ bit-relation channels."""


def agreement(a, b): return a & b
def disagreement(a, b): return a ^ b
def absence(a, b, width=8): return (~(a | b)) & ((1 << width) - 1)


__all__ = ["agreement", "disagreement", "absence"]
