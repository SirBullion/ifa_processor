# IFÁ V3 Grammar

## Program

```text
PROGRAM := STATEMENT*
YO 5 ATI 2
STATEMENT
cat > language_v45/spec/grammar.md <<'EOF'
# IFÁ V3 Grammar

## Program

PROGRAM := STATEMENT*

---

## Statement

STATEMENT :=
    BERE
  | DURO
  | TE ODU
  | BINARY_EXPR

---

## Binary Expression

BINARY_EXPR := OPERATOR VALUE ATI VALUE

Examples

PAPO 2 ATI 1
YO 5 ATI 2
SEDA 0xA5 ATI 0x11

---

## Operators

PAPO
YO
SOPO
PIN
IYOKU
ILOPOMO
AFIKUNMO

SEDA
FARAPO
YATO
YI
GBE

---

## Values

VALUE :=
    INTEGER
  | HEX
  | NUMBER_WORD
  | REGISTER

---

## Registers

REGISTER :=
    A
  | B
  | ADO
  | ADO1
  | ADO2

---

## Number Words

OKAN
MEJI
META
MERIN
MARUN
MEFA
MEJE
MEJO
MESAN
MEWA

---

Example Program

BERE

PAPO META ATI MEJI

TE ODU

DURO

