"""Canonical Φ-P2/Φ-P8 mathematics and verified circuit builders."""

from python.v5.ifa_phi_p8 import (
    phi_p2,
    phi_p2_inverse,
    phi_p8,
    phi_p8_inverse,
)


def build_phi_p2_circuit():
    try:
        from quantum.verified_phi_p2 import build_phi_p2_gate
    except SystemExit as error:
        from quantum.measurement import QuantumDependencyError
        raise QuantumDependencyError("Qiskit is required to build Φ-P2.") from error
    return build_phi_p2_gate()


def build_phi_p8_circuit():
    try:
        from quantum.verified_phi_p8 import build_phi_p8_circuit as builder
    except SystemExit as error:
        from quantum.measurement import QuantumDependencyError
        raise QuantumDependencyError("Qiskit is required to build Φ-P8.") from error
    return builder()


__all__ = [
    "phi_p2", "phi_p2_inverse", "phi_p8", "phi_p8_inverse",
    "build_phi_p2_circuit", "build_phi_p8_circuit",
]
