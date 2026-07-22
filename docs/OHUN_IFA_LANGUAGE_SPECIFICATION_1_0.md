# OHÙN IFÁ Language Specification 1.0

> Interface tones: `KỌ WỌLÉ >` requests input, `Ó WỌLÉ` confirms receipt, `Ó LÈ WỌLÉ — ÀṢẸ` marks security permission, `Ó LÈ WỌLÉ — ÀTÚNṢE` marks an execution correction accepted at 75% or higher, and `KÒ WỌLÉ` marks rejection. See [IFÁ Tonal Interface Contract](IFA_TONAL_INTERFACE.md).

## 1. Conformance and execution

An implementation conforms when it accepts this syntax, preserves the defined values and scopes, and routes native operations through `ExecutionRequest` and Runtime. Source is compiled independently of the selected Python, RTL, or quantum backend.

## 2. Lexical grammar

Source is Unicode text. Keywords and identifiers are case-insensitive; strings preserve case. An identifier begins with a letter or underscore and continues with letters, digits, or underscores. Literals are integers, floating-point numbers, quoted strings, booleans, and lists. `#` begins a line comment. Spaces, tabs, blank lines, and newlines inside expressions are whitespace. Parentheses group expressions; brackets construct and index lists; commas separate arguments and elements.

## 3. Program grammar

The following EBNF is descriptive:

```text
program       = { statement } ;
assignment    = "JE" "KI" target "=" expression | target "=" expression ;
function      = "ISE" identifier "(" [parameters] ")" block "PARI" ;
return        = "RETURN" [expression] ;
if            = "BI" expression block ["TABI" block] "PARI" ;
while         = "NIGBATI" expression block "PARI" ;
for           = "FUN" identifier "LATI" expression "SI" expression block "PARI" ;
foreach       = "FUN" identifier "NINU" expression block "PARI" ;
import        = "GBA" string ;
module        = "MODULE" identifier ;
export        = "EXPORT" "(" string { "," string } ")" ;
call          = ["PE"] identifier "(" [arguments] ")" ;
```

BREAK exits the nearest loop and CONTINUE starts its next iteration. A source file is one ordered Program AST. The interactive shell accepts single statements, `PASTE`…`END` blocks, and `RUN filename`.

## 4. Expressions and precedence

Primary expressions (literals, variables, calls, lists, indexing, and parenthesized expressions) bind most tightly. Prefix native arithmetic consumes its required operands: PAPO (add), YO (subtract), DAGBA (multiply), PIN (divide), KU (remainder), and GBE (power). Relations are SEDA/`==`, `!=`, JU/`>`, KERE/`<`, `>=`, and `<=`. Unary NOT binds before boolean AND, which binds before OR. Parentheses override these rules. An expression may span arbitrary lines.

## 5. Values, variables, and arrays

Assignments bind dynamically typed values. Lists are ordered, mutable, zero-indexed collections; an indexed assignment changes the selected element. Out-of-range and invalid operations are execution errors. Built-ins include PRINT, INPUT, LEN, TYPE, INT, FLOAT, and STRING.

## 6. Functions and recursion

A function declaration binds one name and fixed parameter list; overloading is not defined. Calls evaluate arguments before creating a frame. Each frame has parameters, locals, a return address, and a parent link. Lookup searches the current frame and its parents, then globals; local bindings shadow outer bindings. RETURN immediately leaves the current call and supplies its value. Direct and mutual recursion use independent frames, so locals never leak between calls.

## 7. Control flow

BI executes its first block when its condition is truthy and otherwise executes TABI when present. NIGBATI repeats while its condition is truthy. `FUN I LATI a SI b` iterates the inclusive integer range from a through b. `FUN ITEM NINU collection` visits each element in order. Nested control structures are permitted.

## 8. Modules

GBA resolves and imports a complete source file once. MODULE declares its namespace. Without EXPORT, legacy modules export all functions. One or more `EXPORT("name")` declarations restrict unqualified external access; module-private functions remain available to code in the same module.

## 9. Native operations and relations

Native arithmetic is backend-independent and is never computed by the parser or shell. Relation results follow the canonical IFÁ relation frame and transport rules. Backend-specific representations, including Φ-P8 and RTL registers, must decode to the same logical language result.

## 10. Standard library and errors

The standard library groups math, bit, native, transport, and relation wrappers without redefining operations. Canonical failures derive from `IfaError` and include relation, transport, memory, quantum-domain, unsupported-quantum-operation, stack-transport, permission, execution, and compiler errors. Diagnostics should include filename, line, column, offending token, expected token, and an explanation when that information is available.
