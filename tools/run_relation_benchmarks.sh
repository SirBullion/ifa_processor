#!/usr/bin/env bash
set -e

PROGRAMS=(
  "benchmarks/bench_compute_direct.ifa"
  "benchmarks/bench_compute_agree.ifa"
  "benchmarks/bench_compute_flip.ifa"
  "benchmarks/bench_compute_disagree.ifa"
  "benchmarks/bench_direct_printodu.ifa"
  "benchmarks/bench_relation_agree_printodu.ifa"
  "benchmarks/bench_relation_flip_printodu.ifa"
  "benchmarks/bench_relation_disagree_printodu.ifa"
)

echo "================================================================================"
echo "IFÁ RELATION-SPACE BENCHMARKS"
echo "================================================================================"
printf "%-42s %10s %10s %s\n" "program" "cycles" "final" "status"
echo "--------------------------------------------------------------------------------"

for prog in "${PROGRAMS[@]}"; do
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

    out=$(vvp sim/tb_cpu_rom_top.out)

    cycles=$(echo "$out" | grep "CYCLES" | awk '{print $3}')
    final=$(echo "$out" | grep "FINAL OUTPUT" | awk '{print $4}')
    if echo "$out" | grep -q "PASS"; then
        status="PASS"
    else
        status="FAIL"
    fi

    printf "%-42s %10s %10s %s\n" "$prog" "$cycles" "$final" "$status"
done

echo "================================================================================"
