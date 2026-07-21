# Native Library

`stdlib/` provides one reusable facade over canonical implementations:

- `stdlib.math`: PAPO, YO, DAGBA, PIN, KU, GBE
- `stdlib.bit`: agreement, disagreement, absence
- `stdlib.relation`: relation frames and comparisons
- `stdlib.transport`: transport calculation
- `stdlib.native`: operation and native-function dispatch

Wrappers do not duplicate algorithms. Compiler-generated operations continue through Runtime; these Python modules are integration APIs for tools, tests, and backend code.
