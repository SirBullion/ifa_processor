"""Reusable adapters for the verified IFÁ quantum relation-frame circuit."""

from python.v5.ifa_relation_model import RelationFrame, relation_frame


def build_relation_frame_circuit():
    try:
        from quantum.verified_relation import build_relation_frame_circuit
    except SystemExit as error:
        from quantum.measurement import QuantumDependencyError
        raise QuantumDependencyError(
            "Qiskit is required to build the quantum Relation Frame."
        ) from error
    return build_relation_frame_circuit()


def relation_components(a, b, width=8):
    """Return the existing canonical relation model for backend inspection."""
    return relation_frame(a, b, width)


__all__ = [
    "RelationFrame", "relation_frame", "relation_components",
    "build_relation_frame_circuit",
]
