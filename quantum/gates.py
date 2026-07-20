"""Adapters to the verified reversible gate compiler from the V5 research."""

from functools import lru_cache


def verified_alu_module():
    """Load the verified Qiskit ALU lazily so other backends need no Qiskit."""
    try:
        from quantum import verified_alu as module
    except SystemExit as error:
        from quantum.measurement import QuantumDependencyError
        raise QuantumDependencyError(
            "The IFÁ quantum backend requires Qiskit. Install it with "
            "'python3 -m pip install qiskit'."
        ) from error
    return module


@lru_cache(maxsize=1)
def compiled_alu():
    module = verified_alu_module()
    layout = module.build_integrated_ifa_alu()
    return module, layout, module.compile_circuit(layout.circuit)


def apply_basis_circuit(operations, state):
    return verified_alu_module().apply_basis_circuit(operations, state)
