#!/usr/bin/env bash
set -e

ITEMS=(
  "raw_chain_baseline benchmarks_v2/raw_chain_baseline.ifa"
  "recursive_feedback_chain benchmarks_v2/recursive_feedback_chain.ifa"
)

CSV="analysis/recursive_vs_raw_benchmark.csv"
TXT="analysis/recursive_vs_raw_benchmark.txt"

echo "name,program,cycles,final_y,final_ra,final_rd,final_r0,final_t" > "$CSV"

echo "================================================================================" | tee "$TXT"
echo "IFÁ ODU V2 — RAW CHAIN vs RECURSIVE FEEDBACK" | tee -a "$TXT"
echo "================================================================================" | tee -a "$TXT"
printf "%-30s %8s %10s %10s %10s %10s %10s\n" "name" "cycles" "final_y" "final_ra" "final_rd" "final_r0" "final_t" | tee -a "$TXT"
echo "--------------------------------------------------------------------------------" | tee -a "$TXT"

for item in "${ITEMS[@]}"; do
    name=$(echo "$item" | awk '{print $1}')
    prog=$(echo "$item" | awk '{print $2}')

    python3 tools/ifaasm_odu_v2.py "$prog" > /tmp/ifaasm_odu_v2.log

    iverilog -g2012 \
    rtl_v2/ifa_relation_state_memory.sv \
    rtl_v2/ifa_relation_feedback_unit.sv \
    rtl_v2/ifa_odu_v2_core.sv \
    rtl_v2/ifa_odu_v2_cpu.sv \
    tb_v2/tb_odu_v2_cpu.sv \
    -o sim/tb_odu_v2_cpu.out

    trace=$(vvp sim/tb_odu_v2_cpu.out)

    echo "$trace" > "analysis/${name}_full_trace.txt"

    cycles=$(echo "$trace" | grep "ODU V2 CPU halted after" | awk '{print $6}')
    final_line=$(echo "$trace" | grep -E "^[[:space:]]*[0-9]+ " | tail -1)

    final_y=$(echo "$final_line"  | awk '{print $8}')
    final_ra=$(echo "$final_line" | awk '{print $9}')
    final_rd=$(echo "$final_line" | awk '{print $10}')
    final_r0=$(echo "$final_line" | awk '{print $11}')
    final_t=$(echo "$final_line"  | awk '{print $12}')

    printf "%-30s %8s %10s %10s %10s %10s %10s\n" "$name" "$cycles" "$final_y" "$final_ra" "$final_rd" "$final_r0" "$final_t" | tee -a "$TXT"
    echo "$name,$prog,$cycles,$final_y,$final_ra,$final_rd,$final_r0,$final_t" >> "$CSV"
done

echo "================================================================================" | tee -a "$TXT"
echo "Saved: $TXT" | tee -a "$TXT"
echo "Saved: $CSV" | tee -a "$TXT"
