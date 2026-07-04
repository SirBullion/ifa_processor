#!/usr/bin/env bash
set -e

PROGRAMS=(
  "benchmarks/bench_add.ifa"
  "benchmarks/bench_p8.ifa"
  "benchmarks/bench_correct.ifa"
  "benchmarks/bench_yoruba.ifa"
)

echo "============================================================"
echo "IFÁ CPU BENCHMARK SUITE"
echo "============================================================"

for prog in "${PROGRAMS[@]}"; do
    echo ""
    echo "------------------------------------------------------------"
    echo "Running: $prog"
    echo "------------------------------------------------------------"

    cp "$prog" demo.ifa

    python3 tools/ifaasm.py demo.ifa > /tmp/ifaasm.log

    iverilog -g2012 \
    rtl/ifa_p2.sv \
    rtl/ifa_p4.sv \
    rtl/ifa_p8.sv \
    rtl/ifa_p2_inv.sv \
    rtl/ifa_p4_inv.sv \
    rtl/ifa_p8_inv.sv \
    rtl/ifa_t8.sv \
    rtl/ifa_rom.sv \
    rtl/ifa_cpu_core.sv \
    rtl/ifa_cpu_rom_top.sv \
    tb/tb_cpu_rom_top.sv \
    -o sim/tb_cpu_rom_top.out

    vvp sim/tb_cpu_rom_top.out | grep -E "CYCLES|FINAL OUTPUT|EXPECTED|OUTPUT BUFFER HEX|PASS|FAIL"
done

echo ""
echo "============================================================"
echo "BENCHMARK SUITE COMPLETE"
echo "============================================================"
