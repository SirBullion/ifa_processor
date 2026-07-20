"""Operation mapping for comparisons already verified by the quantum ALU."""

QUANTUM_OPERATION_CODES = {
    "PAPO": 0b000,
    "YO": 0b001,
    "SEDA": 0b010,
    "JU": 0b011,
    "KERE": 0b100,
}

ORACLE_OPERATIONS = frozenset({"DAGBA", "PIN", "KU", "GBE"})
SUPPORTED_OPERATIONS = frozenset(QUANTUM_OPERATION_CODES) | ORACLE_OPERATIONS
UNSUPPORTED_NATIVE_OPERATIONS = frozenset()
