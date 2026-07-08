#!/bin/bash
set -e

BENCH=${1:-benchmarks/regression.ifa3}

echo "====================================="
echo " IFÁ vs CLASSICAL CPU"
echo "====================================="
echo "Benchmark: $BENCH"
echo

echo "[1] IFÁ run"
./ifarun "$BENCH"

echo
echo "[2] Classical CPU reference"
iverilog -g2012 rtl_v3/cpu_ref_v3.sv -o sim/cpu_ref_v3.out
vvp sim/cpu_ref_v3.out

echo
echo "Waveforms:"
echo "  IFÁ CPU       : sim/odu_v2_cpu.vcd"
echo "  Classical CPU : sim/cpu_ref_v3.vcd"
echo
echo "Open:"
echo "  gtkwave sim/odu_v2_cpu.vcd"
echo "  gtkwave sim/cpu_ref_v3.vcd"
