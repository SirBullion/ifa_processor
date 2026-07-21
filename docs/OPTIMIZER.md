# Optimizer

The AST optimizer runs at the existing compiler hook. It performs constant folding and propagation, algebraic identities, conservative local common-subexpression elimination, constant-condition removal, and unreachable-statement elimination after RETURN, BREAK, or CONTINUE.

Calls are never treated as common subexpressions. Control-flow boundaries invalidate known values. Loop bodies do not inherit substitutable loop-entry constants because those variables may change each iteration. Observable global assignments are retained; this deliberately conservative dead-code policy preserves interactive and module semantics.
