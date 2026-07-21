# Quantum Backend

The V4.5 quantum backend reuses the established Φ-P2, Φ-P8, relation-frame, agreement, disagreement, absence, full-adder, and ripple constructions in `quantum/`. `backends/quantum/backend.py` accepts the unchanged `ExecutionRequest` interface.

PAPO, YO, SEDA, JU, and KERE use the verified Qiskit ALU path when Qiskit is installed. DAGBA, PIN, KU, and GBE use exact reversible XOR-target oracles: `(A,B,Y,T)` maps to `(A,B,Y xor fY(A,B),T xor fT(A,B))`. Applying an oracle twice restores the input, so the mapping is a permutation and therefore unitary. PIN exposes quotient in Y and remainder in T; KU exposes remainder in Y and quotient in T; wide arithmetic uses the established Y/T low/high transport convention.

Measurement decoding returns the same logical value as the Python backend while retaining Φ-P8 and relation-register data in the backend's `last_execution` record. Unsupported domains raise canonical quantum exceptions.
