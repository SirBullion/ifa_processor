"""Reusable access to verified IFÁ quantum arithmetic circuits."""

from quantum.gates import compiled_alu, verified_alu_module


def build_full_adder():
    try:
        from quantum.verified_full_adder import build_quantum_full_adder
    except SystemExit as error:
        from quantum.measurement import QuantumDependencyError
        raise QuantumDependencyError(
            "Qiskit is required to build the quantum full adder."
        ) from error
    return build_quantum_full_adder()


def build_integrated_alu():
    return verified_alu_module().build_integrated_ifa_alu()


def build_compiled_alu():
    return compiled_alu()


def build_dual_carry_ripple():
    try:
        from quantum.verified_ripple import build_dual_carry_ripple
    except SystemExit as error:
        from quantum.measurement import QuantumDependencyError
        raise QuantumDependencyError(
            "Qiskit is required to build the dual-carry ripple circuit."
        ) from error
    return build_dual_carry_ripple()


__all__ = [
    "build_full_adder", "build_integrated_alu", "build_compiled_alu",
    "build_dual_carry_ripple",
]
