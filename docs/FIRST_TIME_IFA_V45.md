# IFÁ v4.5 — First-Time User Guide

Read this file first when opening the project for the first time.

## Àmì ohùn in the interface

| Text | Meaning |
|---|---|
| `KỌ WỌLÉ >` | Enter or write input here. |
| `Ó WỌLÉ` | The interface received the input. |
| `Ó LÈ WỌLÉ — ÀṢẸ` | Security permission was granted. |
| `Ó LÈ WỌLÉ — ÀTÚNṢE` | Execution corrected a recognizable input (75% or higher). |
| `KÒ WỌLÉ` | The request did not enter or was rejected. |

The tonal marks distinguish these system states. See `docs/IFA_TONAL_INTERFACE.md` for the complete contract.

## Start the graphical interface

From any terminal location, including your home directory:

```bash
oduifa
```

The input field is labelled:

```text
KỌ WỌLÉ
```

Click **OHÙN shell** or **IFÁ monitor**, type into `KỌ WỌLÉ`, and press Enter.
Backspace/Delete edit the input; Up/Down recall earlier commands.

Useful first inputs:

```text
HELP
SUGGESTIONS
SERVICES
SUM FIST 7 PTIME
```

The last example is corrected to `SUM THE FIRST 7 PRIME NUMBERS` and returns `58`. `ÀṢẸ` belongs to security; `ÀTÚNṢE` belongs to execution, so the two meanings do not interfere.

The IFÁ monitor displays `Press ENTER to enter IFÁ OS...` during startup. Press
Enter once, then enter `HELP` or `SUGGESTIONS` at `KỌ WỌLÉ >`.

## Start the OHÙN terminal without the GUI

```bash
cd /home/sirbullion/ifa_processor1
python3 tools/ohunifa_v45.py --backend python
```

Other available backends are `rtl` and `quantum`:

```bash
python3 tools/ohunifa_v45.py --backend quantum
```

At the prompt:

```text
KỌ WỌLÉ >
```

enter an expression, service, `RUN <file>`, `HELP`, or `SUGGESTIONS`.

## Audit a hardware program

In the GUI, select an `.ifa45` source or `.hex` image with **Browse**, then
click **Run + Audit + Wave**. The audit prints:

```text
CYCLES
RMU_HITS
RMU_MISSES
RMU_ACCESSES
RMU_HIT_RATE
PRINT_EVENTS
AUDIT_LOG
WAVEFORM
```

GTKWave opens automatically. Logs and waveforms are saved under:

```text
build/v45/audits/
```

The equivalent terminal command is:

```bash
python3 tools/ifa_v45_audit.py programs_v4/hanoi_recursive_5_v45.ifa45 --open-wave
```

## Program file types

- `.ifa`: high-level OHÙN IFÁ source, run in the OHÙN shell.
- `.ifa45`: v4.5 processor assembly, accepted by the RTL audit.
- `.hex`: assembled v4.5 instruction image, accepted by the RTL audit.
- `.lst`: human-readable assembly listing.
- `.fst` or `.vcd`: GTKWave hardware trace.

## More documentation

- `docs/OHUN_IFA_LANGUAGE_SPECIFICATION_1_0.md`
- `docs/OHUN_IFA_QUICK_REFERENCE.md`
- `docs/IFA_PROCESSOR_ARCHITECTURE.md`
- `docs/IFA_V45_EDA_OPEN_SOURCE_METHODS.md`
