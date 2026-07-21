# IFÁ V4.5 native ISA extension

V4.5 preserves every V4 16-bit instruction encoding. The V4 assembler and
all modules under `rtl/v4` remain the executable V4 implementation.

V4.5 assigns major opcode `0x4` to compiler data movement:

| Word | Mnemonic | Operation |
|---:|---|---|
| `4000` | `MOVY_A` | `A <- Y` |
| `4100` | `MOVY_B` | `B <- Y` |
| `4200` | `MOVADDR_A` | `Address <- A` |
| `4300` | `MOVADDR_B` | `Address <- B` |
| `4400` | `LOAD_A` | `A <- Memory[Address]` |
| `4500` | `LOAD_B` | `B <- Memory[Address]` |
| `4600` | `STORE_A` | `Memory[Address] <- A` |
| `4700` | `STORE_B` | `Memory[Address] <- B` |

Memory operations pass through the existing ONÍLẸ̀ guarded General Memory.
Its ownership and permission rules still apply. A denied program memory
operation faults the executor.

## V4.5 call convention

- A and B carry the first two scalar parameters.
- CALL preserves caller A, B, Address, flags, relation state and return PC.
- The callee may replace A, B and Address without changing its caller frame.
- RET restores caller B and Address and places the callee's final relation
  result in caller A.
- `MOVY_A` may be used before another CALL when a computed result is an
  argument. `MOVY_A` and `MOVY_B` also enable nested native arithmetic.

The V4.5 assembler is invoked separately:

```text
py tools/ifaasm_v45.py program.ifa45
```

This emits `program.hex` and `program.lst`. V4 programs continue to use
`tools/ifaasm_v4.py`.
