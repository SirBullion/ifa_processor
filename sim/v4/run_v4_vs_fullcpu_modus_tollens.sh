#!/usr/bin/env bash
set -e

mkdir -p sim/v4 programs

echo "=================================================="
echo "CPU REF V3 vs IFÁ V4 MODUS TOLLENS"
echo "=================================================="

cat > programs/modus_tollens_ref.hex <<'EOF'
1001
2000
5000
7006
1000
F000
1001
F000
EOF

cp programs/modus_tollens_ref.hex odu_v2_program.hex

iverilog -g2012 \
  -o sim/cpu_ref_modus_tollens.out \
  rtl_v3/cpu_ref_v3.sv

echo
echo "Running CPU Ref V3..."
vvp sim/cpu_ref_modus_tollens.out

echo
echo "Running IFÁ V4..."
iverilog -g2012 \
  -o sim/v4/tb_ifa_v4_modus_tollens.out \
  rtl/v4/ifa_relation_memory_controller.sv \
  rtl/v4/ifa_v4_core.sv \
  rtl/v4/ifa_rpc_stub.sv \
  rtl/v4/ifa_v4_end_to_end_core.sv \
  tb/v4/tb_ifa_v4_modus_tollens.sv

vvp sim/v4/tb_ifa_v4_modus_tollens.out

echo
echo "=================================================="
echo "EXPECTED COMPARISON"
echo "CPU Ref V3 : full instruction program, 6 cycles"
echo "IFÁ V4     : relation-frame path, expected 2 cycles"
echo "=================================================="
