# IFÁ v4.5 EDA and Open-Source Verification Methods

This guide preserves the methods used to verify IFÁ v4.5 from native relation
mathematics through RMU reuse and synthesis.

The GUI and terminal use the [IFÁ Tonal Interface Contract](IFA_TONAL_INTERFACE.md): `KỌ WỌLÉ >` for input, `Ó WỌLÉ` for receipt, `Ó LÈ WỌLÉ — ÀṢẸ` for security permission, `Ó LÈ WỌLÉ — ÀTÚNṢE` for execution correction at 75% or higher, and `KÒ WỌLÉ` for rejection.

## Desktop launcher

Start the graphical project interface from the repository root:

```bash
python3 tools/ifa_v45_launcher.py
```

On this workstation it is also installed as a user command, so it can be started from the home directory or any terminal location with:

```bash
oduifa
```

The command is a symbolic link in `~/.local/bin`, which is already on the user PATH. It continues to use the launcher saved in this repository.

Check its open-source dependencies without opening a window:

```bash
python3 tools/ifa_v45_launcher.py --check
```

The launcher embeds the OHÙN shell and IFÁ monitor in its keyboard-enabled console. Enter sends a command, Backspace/Delete edit it, and Up/Down recall history. Build, test, synthesis, auditing, GTKWave, and documentation remain in the same interface.

Select any `.ifa45` source or `.hex` image with **Browse**, then choose **Run + Audit + Wave**. The interface assembles source when necessary, builds the RTL bridge, executes the program, reports cycles and RMU hits/misses, saves the audit log and waveform under `build/v45/audits/`, and opens GTKWave.

The same audit is available without the GUI:

```bash
python3 tools/ifa_v45_audit.py program.ifa45 --open-wave
```

## What each test proves

| Method | What it proves | RMU hit/miss evidence |
|---|---|---|
| Native RAU test | IFÁ operations and relation-frame channels are correct | No; it has no RMU |
| Full v4.5 Hanoi simulation | Recursive execution and repeated relation reuse | Yes |
| GTKWave | Cycle-by-cycle requests, responses, hits and misses | Yes |
| Yosys synthesis | Kernel, RMU, PEs, context and memory logic are synthesizable | Hardware structures, not runtime counts |
| FPGA execution | The synthesized design operates in physical hardware | Yes, after counters are exposed to UART/registers |

## 1. EDA Playground: quick native IFÁ test

Use the prepared files:

- `build/eda_playground_v45/design.sv`
- `build/eda_playground_v45/testbench.sv`
- `build/eda_playground_v45/expected_output.txt`

In EDA Playground:

1. Select **SystemVerilog/Verilog**.
2. Select **Icarus Verilog** or another SystemVerilog simulator.
3. Put `design.sv` in the Design pane.
4. Put `testbench.sv` in the Testbench pane.
5. Set the top module to `tb_ifa_native_rau_v45` if the simulator asks for it.
6. Run and compare the console with `expected_output.txt`.

The final output should include:

```text
PASS: ALL NATIVE IFÁ MATHEMATICAL FUNCTIONS VERIFIED
PASS: RA, RD AND R0 ARE UNIVERSAL
PASS: EXTENDED POWER IS AN IFÁ STATE, NOT OVERFLOW
```

This compact test verifies the native relation arithmetic only. It must not be
used as evidence of RMU hit/miss reuse because it contains no relation memory.

## 2. Local open-source v4.5 build

Required programs are Icarus Verilog, GTKWave, Yosys, Verilator, GNU Make and
Python 3. On Debian or Ubuntu they are normally available through the system
package manager:

```bash
sudo apt install iverilog gtkwave yosys verilator make python3
```

From the repository root, compile the complete v4.5 simulation bridge:

```bash
make v45-build
```

Run the focused language, ISA and quantum regression tests:

```bash
python3 -m unittest \
  tests.test_v45_native_isa \
  tests.test_quantum_backend
```

Expected result: 19 tests pass and the optional Qiskit-dependent test may be
skipped when Qiskit is not installed.

## 3. Assemble any Hanoi depth from 5 through 10

Example for level 10:

```bash
python3 tools/ifaasm_v45.py \
  programs_v4/hanoi_recursive_10_v45.ifa45 \
  programs_v4/hanoi_recursive_10_v45
```

This produces the `.hex` instruction image and `.lst` assembly listing.

## 4. Run Hanoi and measure RMU reuse

The bridge accepts lifecycle, context, instruction-load and execution commands.
This command runs level 10 and prints the final profile:

```bash
{
  printf 'BABALAWO ON\nCREATE 0\nSELECT 0\n'
  printf 'CONTEXT 00 0000 00 00 00 00 00\n'
  awk '{printf "LOAD %02x %s\n", NR-1, $1}' \
    programs_v4/hanoi_recursive_10_v45.hex
  printf 'RUN\nQUIT\n'
} | vvp sim/v45/ifa_v45_os_bridge.out +INTERACTIVE \
  | awk '/^PRINT/{fields++} /^OK RUN|^FAULT/{print} \
         END{printf "MOVES=%d\n", fields/3}'
```

The `OK RUN` line contains:

- `CYCLES`: complete processor execution cycles;
- `RMU_HITS`: logical relation lookups served by stored frames;
- `RMU_MISSES`: relation lookups requiring computation/storage.

The hit rate is:

```text
RMU_HITS / (RMU_HITS + RMU_MISSES)
```

Verified level-10 result:

```text
MOVES=1023
CYCLES=121809
RMU_HITS=4020
RMU_MISSES=74
HIT_RATE=98.19%
```

The complete N=5 through N=10 results are saved in
`analysis/hanoi_ifa_v45_profile.md`.

## 5. Generate and inspect a GTKWave trace

Add the `VCD` plus-argument to the same simulation:

```text
+VCD=sim/v45/hanoi_10_full_processor.vcd
```

Convert the large VCD into the smaller FST format and open it:

```bash
vcd2fst \
  sim/v45/hanoi_10_full_processor.vcd \
  sim/v45/hanoi_10_full_processor.fst

gtkwave sim/v45/hanoi_10_full_processor.fst
```

Useful signals include:

```text
executor_execute_valid
executor_execute_op
operation_valid
rmu_hit
rmu_miss
out_y
out_ra
out_rd
out_r0
out_t
active_pc
active_sp
```

Each logical native instruction should create one `rmu_hit` or `rmu_miss`
pulse. `operation_valid` marks the returned native relation result.

## 6. Verilator lint

Check synthesizable SystemVerilog structure and portability:

```bash
make v45-lint
```

Lint is a structural check; it does not replace simulation or synthesis.

## 7. Yosys synthesis

Synthesize the v4.5 kernel:

```bash
make v45-synth
```

The resulting generic hardware netlist is:

```text
build/v45/ifa_onile_kernel_v45.json
```

Inspect its hierarchy and resources:

```bash
yosys -Q -p \
  'read_json build/v45/ifa_onile_kernel_v45.json; \
   hierarchy -top ifa_onile_kernel_v45; stat'
```

The current synthesis includes the kernel, RMUs, PEs, Φ-P8 blocks, YÀRÁ
contexts, stack memory, supervisor and memory guard. The simulation bridge owns
the program executor, so an integrated synthesizable top is still required to
run the recursive program on an FPGA.

## 8. Full EDA Playground RMU simulation

For the complete RMU experiment, add the source files listed in `V45_RTL` in
the repository `Makefile`, plus `tb/v45/tb_ifa_v45_os_bridge.sv`. Use
`tb_ifa_v45_os_bridge` as the simulation top and SystemVerilog-2012 mode.

The bridge also needs a command file containing:

1. `BABALAWO ON`;
2. `CREATE 0` and `SELECT 0`;
3. the initial `CONTEXT` command;
4. one `LOAD address instruction` line per hexadecimal instruction;
5. `RUN` and `QUIT`.

Run with the simulator equivalent of:

```text
+CMD_FILE=<uploaded-command-file>
```

If the online service cannot supply runtime files or plus-arguments, use the
local Icarus method. It exercises the same SystemVerilog RTL without those web
interface limitations.

## 9. What is still required for physical hardware

Yosys proves that the design can become a hardware netlist. Physical validation
additionally requires:

1. a named FPGA board and pin/clock constraint file;
2. an integrated executor-plus-kernel top module;
3. instruction ROM initialization or a loader interface;
4. UART, memory-mapped registers, or logic-analyzer probes for RMU counters;
5. the board vendor or open-source place-and-route and bitstream tools;
6. an on-board run confirming the expected moves and hit/miss totals.

Keep the three claims separate: RTL simulation proves behavior, Yosys proves
synthesizability, and an FPGA run proves operation in physical hardware.
