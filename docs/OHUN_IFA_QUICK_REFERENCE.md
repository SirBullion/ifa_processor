# OHÙN IFÁ V1.0 — Quick Reference Card

**Canonical implementation:** IFÁ Processor V4.5  
**Source extension:** `.ifa` · **Case:** keywords, identifiers, and function names are case-insensitive  
**Pipeline:** Source → Tokenizer → Parser → AST → Optimizer → IR → Interpreter → ExecutionRequest → Runtime → BackendManager → Backend

---

## 1. Language overview

OHÙN IFÁ is a dynamically typed, expression-oriented language for the IFÁ native relation operations. A file is one program containing ordered statements. Programs support mutable variables and lists, functions, recursion, modules, conditionals, and loops. Native arithmetic and relations execute through the selected Python, RTL, or quantum backend.

Blank lines are ignored. Newlines may occur anywhere inside an expression; no continuation marker or semicolon is required. The tokenizer supports quoted strings with escapes. The V4.5 parser does **not** define source-comment syntax.

## 2. Core syntax and keywords

| Purpose | Syntax / keywords |
|---|---|
| assignment | `JE KI name = expression` |
| indexed assignment | `list[index] = expression` |
| function | `ISE`, `RETURN`, `PARI`; optional call marker `PE` |
| conditional | `BI`, `TABI`, `PARI` |
| while | `NIGBATI`, `PARI` |
| range / iteration | `FUN`, `LATI`, `SI`, `NINU`, `PARI` |
| loop transfer | `BREAK`, `CONTINUE` |
| module | `MODULE`, `GBA`, `EXPORT`, `PARI` |
| expression separator | `ATI` |
| logical | `NOT`, `AND`, `OR` |
| literals | `TRUE`, `FALSE` |

Block terminators `PARI` and `TABI` must appear alone on their logical line.

## 3. Operators

All native binary operations use prefix form:

```text
OPERATOR left ATI right
```

| Family | Operator | Meaning | Example |
|---|---|---|---|
| arithmetic | `PAPO` | addition | `PAPO A ATI B` |
| arithmetic | `YO` | subtraction | `YO A ATI B` |
| arithmetic | `DAGBA` | multiplication | `DAGBA A ATI B` |
| arithmetic | `PIN` | division | `PIN A ATI B` |
| arithmetic | `KU` | modulo/remainder | `KU A ATI B` |
| arithmetic | `GBE` | exponentiation | `GBE A ATI B` |
| relation | `SEDA` | equal | `SEDA A ATI B` |
| relation | `JU` | greater than | `JU A ATI B` |
| relation | `KERE`, `KERÉ` | less than | `KERE A ATI B` |
| logical | `NOT` | logical negation | `NOT condition` |
| logical | `AND` | logical conjunction | `AND A ATI B` |
| logical | `OR` | logical disjunction | `OR A ATI B` |

Symbolic comparisons are also accepted: `==`, `!=`, `>`, `<`, `>=`, `<=`.

```ifa
BI PAPO A ATI 1 >= DAGBA B ATI 2
    PRINT("TRUE")
PARI
```

Relations return integer `1` or `0`. Logical operations use truthiness and return `1` or `0`.

### Relation and transport channels

Every native operation creates the canonical relation information below. These are runtime/backend channels—not standalone OHÙN IFÁ source operators.

| Channel | Definition / role |
|---|---|
| `RA` | agreement: `A AND B` at the bit-relation level |
| `RD` | disagreement: `A XOR B` |
| `R0` | absence: `NOT (A OR B)` within the active width |
| `Y` | width-projected native result |
| `T` | transport/state when a result leaves the active relation window |
| `EQ`, `GT`, `LT` | relation-result channels |

## 4. Values, variables, and arrays

Supported runtime values include integers, floats, strings, booleans, lists, and the null result returned by functions without a value.

```ifa
JE KI COUNT = 10
JE KI TOTAL = PAPO COUNT ATI 5
JE KI ITEMS = [1, 2, 3]

PRINT(ITEMS[0])
ITEMS[1] = 99
JE KI NESTED = [[1, 2], [3, 4]]
PRINT(NESTED[1][0])
```

Lists are mutable and zero-indexed. Index and list expressions may span lines.

Yorùbá number-word literals implemented by V4.5 cover one through ten: `OKAN`, `MEJI`, `META`, `MERIN`, `MARUN`, `MEFA`, `MEJE`, `MEJO`, `MESAN`, `MEWA`, including the encoded diacritic variants present in `language_v45/spec/numbers.py`.

## 5. Functions and calling convention

```ifa
ISE ADD(X, Y)
    RETURN PAPO X ATI Y
PARI

JE KI RESULT = ADD(5, 7)
JE KI ALSO = PE ADD(5, 7)
```

- Parameters are positional and argument count must match exactly.
- `PE` is an optional call marker; `NAME(...)` is the normal call form.
- Arguments are evaluated before the call.
- Every call creates a frame holding parameters, locals, a return address, and a parent-frame link.
- Assignment inside a function creates/updates a local binding.
- Lookup checks the current frame, then globals. Caller-local variables are not dynamically inherited.
- Globals remain readable unless shadowed by a local.
- `RETURN expression` returns immediately; falling off the end returns no value.
- Direct and mutual recursion use independent frames. Function overloading is not defined.

## 6. Control flow

```ifa
BI X > 5
    PRINT(X)
TABI
    PRINT(0)
PARI

NIGBATI I < 10
    JE KI I = PAPO I ATI 1
PARI

FUN I LATI 1 SI 10
    PRINT(I)
PARI

FUN ITEM NINU ITEMS
    PRINT(ITEM)
PARI
```

`FUN … LATI … SI …` is inclusive and automatically counts down when the start is greater than the end. `BREAK` exits the nearest loop; `CONTINUE` begins its next iteration. Both are invalid outside a loop. Control structures may be nested.

## 7. Native operations and standard library

| Function | Arguments | Result |
|---|---:|---|
| `PRINT(...)` | 0–1000 | prints values; no value |
| `INPUT()` / `INPUT(prompt)` | 0–1 | input string |
| `LEN(value)` | 1 | length |
| `TYPE(value)` | 1 | `NULL`, `BOOLEAN`, `INTEGER`, `FLOAT`, `STRING`, or `LIST` |
| `INT(value)` | 1 | integer conversion |
| `FLOAT(value)` | 1 | floating-point conversion |
| `STRING(value)` | 1 | string conversion |

The reusable Python integration library mirrors canonical implementations in `stdlib.math`, `stdlib.bit`, `stdlib.relation`, `stdlib.transport`, and `stdlib.native`. It does not add additional OHÙN IFÁ source syntax.

## 8. Modules and imports

Library file:

```ifa
MODULE MATH
ISE DOUBLE(X)
    RETURN DAGBA X ATI 2
PARI
EXPORT("DOUBLE")
PARI
```

Consumer:

```ifa
GBA "math.ifa"
PRINT(MATH.DOUBLE(6))
```

`GBA path` accepts a quoted or single-token path, resolves relative paths from the importing file, and imports each resolved file once. Circular imports are errors. `MODULE name … PARI` qualifies its functions as `NAME.FUNCTION`. One-argument `EXPORT("FUNCTION")` declarations restrict external access; without any `EXPORT`, all declared module functions are exported for compatibility. Module-private functions remain callable inside their module.

## 9. Shell, compiler, and backends

Start the shell:

```text
py tools/ohunifa_v45.py
py tools/ohunifa_v45.py --backend python|rtl|quantum
```

| Shell command | Action |
|---|---|
| `PASTE` | begin whole-program input |
| `OTAN` | execute buffered program; `END` is an alias |
| `RUN filename.ifa` | parse and execute an entire file |
| `COMPILE filename.ifa` | write `build/name.ir` and `build/name.sv` |
| `BACKEND` | show active and available backends |
| `BACKEND python|rtl|quantum` | select backend |
| `STATUS` | show V4.5 shell status |
| `YARA GBOBO` | toggle AST/result diagnostic display |
| `IPO [FRAME|RMU|PHI]` | inspection command; currently reports not connected |
| `HELP` | list/help for commands |
| `EXIT`, `QUIT` | leave the shell |

Single-line expressions remain valid directly at `OHUNIFA>`.

### Compiler directives

OHÙN IFÁ source has no preprocessor/directive syntax. The compiler emits `.main`, `.function NAME(parameters)`, and `.end` in textual IR; these are compiler output, not source statements. `COMPILE` runs the existing optimizer and IR/RTL generators. Raw V4.5 ISA assembly is a separate input format handled by `tools/ifaasm_v45.py`.

## 10. Errors and diagnostics

There is no source-level `TRY`/`CATCH` construct. Failures propagate to the shell, which reports filename, line, column, offending token, and expected token when discoverable. Common errors include undefined variables/functions, argument-count mismatch, invalid indexes, missing block terminators, invalid loop transfer, circular imports, private module access, division/modulo by zero, and unsupported backend domains.

Canonical software exceptions include `RelationError`, `TransportError`, `MemoryError`, `QuantumDomainError`, `UnsupportedQuantumOperation`, `StackTransport`, `PermissionDenied`, `ExecutionError`, and `CompilerError`.

## 11. Operator precedence and grouping

1. Literals, variables, lists, calls, and parenthesized expressions
2. Postfix list indexing: `A[index]`
3. Prefix expressions: native arithmetic/relation operations, `NOT`, `AND`, `OR`
4. Top-level infix comparisons: `== != > < >= <=` and infix `SEDA JU KERE/KERÉ`

Prefix operands are parsed recursively, so their structure determines grouping. Parentheses may make grouping explicit. There are no infix `+`, `-`, `*`, `/`, `%`, or exponent symbols.

```ifa
JE KI X = PAPO 10 ATI DAGBA 2 ATI 3
```

The expression above groups as `10 + (2 × 3)`. V4.5 defines no comment marker.

## 12. Grammar summary

```text
program       := statement+
statement     := assignment | index_assignment | expression | function
               | return | if | while | for | foreach | break | continue
               | import | module
assignment    := JE KI name = expression
index_assign  := expression [ expression ] = expression
function      := ISE name ( parameters? ) block PARI
return        := RETURN expression?
if            := BI expression block (TABI block)? PARI
while         := NIGBATI expression block PARI
for           := FUN name LATI expression SI expression block PARI
foreach       := FUN name NINU expression block PARI
import        := GBA path
module        := MODULE name block PARI
export        := EXPORT ( name-or-string )
expression    := literal | name | list | index | call | grouped
               | operator expression ATI expression
               | NOT expression | comparison
call          := PE? qualified-name ( arguments? )
list          := [ (expression (, expression)*)? ]
comparison    := expression comparator expression
```

### Reserved words

```text
JE KI ATI ISE PE RETURN PARI BI TABI NIGBATI BREAK CONTINUE
FUN LATI SI NINU GBA MODULE EXPORT TRUE FALSE NOT AND OR
PAPO YO DAGBA PIN KU GBE SEDA JU KERE KERÉ
```

`SOPO`, `IYOKU`, `ILOPOMO`, and `AFIKUNMO` exist as reserved, non-executable operator entries. `PASTE`, `OTAN`, `END`, `RUN`, `COMPILE`, `BACKEND`, `STATUS`, `YARA`, `GBOBO`, `IPO`, `HELP`, `EXIT`, and `QUIT` are shell commands rather than program keywords.

---

## 13. Complete compact example

```ifa
ISE FACT(N)
    BI N <= 1
        RETURN 1
    PARI
    RETURN DAGBA N ATI FACT(YO N ATI 1)
PARI

JE KI VALUES = [3, 4, 5]
FUN ITEM NINU VALUES
    PRINT(ITEM, FACT(ITEM))
PARI
```

**Backend independence:** changing the selected backend does not change source syntax, AST structure, function semantics, or the Runtime/ExecutionRequest contract.
