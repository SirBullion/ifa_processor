# IFÁ Processor V4 — Canonical ISA

## Instructions

| Encoding | Mnemonic | Semantics |
|---|---|---|
| `0x01TT` | `BR_EQ` | Branch to TT when EQ=1 |
| `0x02TT` | `BR_GT` | Branch to TT when GT=1 |
| `0x03TT` | `BR_LT` | Branch to TT when LT=1 |
| `0x04TT` | `JMP` | Jump unconditionally to TT |
| `0x10II` | `LDAI` | Load immediate II into A |
| `0x20II` | `LDBI` | Load immediate II into B |
| `0x30II` | `LDADDR` | Load immediate II into ADDR |
| `0x8000` | `PAPO` | Native add, OP=0 |
| `0x8100` | `YO` | Native subtract, OP=1 |
| `0x8200` | `DAGBA` | Native multiply, OP=2 |
| `0x8300` | `PIN` | Native divide, OP=3 |
| `0x8400` | `KU` | Native modulo, OP=4 |
| `0x8500` | `GBE` | Native GBÉ operation, OP=5 |
| `0x8600` | `SEDA` | Native compare, OP=6 |
| `0x8700` | `JU` | Native greater-than predicate, OP=7 |
| `0x8800` | `KERE` | Native less-than predicate, OP=8 |
| `0xF000` | `NOP` | No operation |
| `0xF100` | `HALT` | Halt program execution |
| `0xF200` | `PRINTY` | Print relation-frame Y |
| `0xF300` | `PRINTRA` | Print relation-frame RA |
| `0xF400` | `PRINTRD` | Print relation-frame RD |
| `0xF500` | `PRINTR0` | Print relation-frame R0 |
| `0xF600` | `PRINTT` | Print relation-frame T |
| `0xF700` | `PRINTOP` | Print native OP |
| `0xF800` | `PRINTSTATUS` | Print packed latest-operation status |
| `0xF900` | `RPUSH` | Preserve the complete IFÁ relation frame in the active YÀRÁ relation stack |
| `0xFA00` | `RPOP` | Restore the most recently preserved IFÁ relation through ONÍLẸ̀ administrative import |
| `0xFBtt` | `CALL` | Preserve the relation and return continuation, then transfer execution to 8-bit target tt |
| `0xFC00` | `RET` | Restore the preserved relation and resume at its saved return continuation |

## Relation frame

```text
Ψ = {Y, RA, RD, R0, T}
```

## RMU key

```text
K = {OP, RA, RD, T}
```