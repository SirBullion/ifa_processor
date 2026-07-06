#!/usr/bin/env bash
set -e

PROGRAMS=(
  "programs_v2/relation_algorithm_1_store_recall.ifa"
  "programs_v2/relation_algorithm_2_feedback_reuse.ifa"
  "programs_v2/relation_algorithm_3_two_memory_slots.ifa"
  "programs_v2/relation_algorithm_4_feedback_chain.ifa"
)

echo "================================================================================"
echo "IFÁ ODU V2 — PHASE 1 RELATION ALGORITHMS"
echo "================================================================================"

for prog in "${PROGRAMS[@]}"; do
    name=$(basename "$prog" .ifa)

    echo ""
    echo "--------------------------------------------------------------------------------"
    echo "PROGRAM: $name"
    echo "--------------------------------------------------------------------------------"

    python3 tools/ifaasm_odu_v2.py "$prog" > /tmp/ifaasm_odu_v2.log

    iverilog -g2012 \
    rtl_v2/ifa_relation_state_memory.sv \
    rtl_v2/ifa_relation_feedback_unit.sv \
    rtl_v2/ifa_odu_v2_core.sv \
    rtl_v2/ifa_odu_v2_cpu.sv \
    tb_v2/tb_odu_v2_cpu.sv \
    -o sim/tb_odu_v2_cpu.out

    vvp sim/tb_odu_v2_cpu.out | tee "analysis/${name}_trace.txt"

    echo "Saved trace: analysis/${name}_trace.txt"
done

echo ""
echo "================================================================================"
echo "PHASE 1 COMPLETE"
echo "================================================================================"
