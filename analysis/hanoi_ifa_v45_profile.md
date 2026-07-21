# IFÁ v4.5 Hanoi Relation Profile

This profile runs the same 38-instruction recursive Hanoi program on the full
IFÁ v4.5 RTL processor. `RMU hits + RMU misses` is the number of logical native
relation accesses; handshake cycles are not counted as additional accesses.

| Levels | Moves | Cycles | RMU hits | RMU misses | Accesses | Hit rate |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | 31 | 3,761 | 114 | 12 | 126 | 90.48% |
| 6 | 63 | 7,569 | 240 | 14 | 254 | 94.49% |
| 7 | 127 | 15,185 | 494 | 16 | 510 | 96.86% |
| 8 | 255 | 30,417 | 1,004 | 18 | 1,022 | 98.24% |
| 9 | 511 | 60,881 | 2,009 | 37 | 2,046 | 98.19% |
| 10 | 1,023 | 121,809 | 4,020 | 74 | 4,094 | 98.19% |

## Interpretation

- Moves are exactly `2^N - 1` for every depth.
- Relation accesses are exactly `2^(N+2) - 2` for every depth.
- The RMU hit rate rises above 98% from N=8 onward, demonstrating repeated
  relation-frame reuse.
- The 16-entry RMU holds all distinct Hanoi relation keys through N=7. From
  N=8 onward the working set exceeds its capacity, so eviction misses appear.
- Cycle counts cover the complete processor path, including instruction fetch,
  context commits, recursion-stack traffic, call/return handling, and three
  printed fields per move. They are not the latency of the RMU itself.

## Reproduce

Build the v4.5 bridge:

```bash
make v45-build
```

The assembled sources and images are named:

```text
programs_v4/hanoi_recursive_5_v45.{ifa45,hex,lst}
programs_v4/hanoi_recursive_6_v45.{ifa45,hex,lst}
programs_v4/hanoi_recursive_7_v45.{ifa45,hex,lst}
programs_v4/hanoi_recursive_8_v45.{ifa45,hex,lst}
programs_v4/hanoi_recursive_9_v45.{ifa45,hex,lst}
programs_v4/hanoi_recursive_10_v45.{ifa45,hex,lst}
```
