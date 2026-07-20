"""Access to the existing verified ripple/transport reference operation."""

from quantum.gates import verified_alu_module


def ripple_reference(a, b, carry_initial):
    return verified_alu_module().ripple_reference(a, b, carry_initial)


def apply_sparse_state(operations, amplitudes):
    return verified_alu_module().apply_sparse_state(operations, amplitudes)


__all__ = ["ripple_reference", "apply_sparse_state"]
