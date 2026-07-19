#!/usr/bin/env bash
set -euo pipefail
mkdir -p build/v5
iverilog -g2012 \
  -s tb_ifa_phi_p8_relation_ripple \
  -o build/v5/tb_phi_p8_relation_ripple.vvp \
  rtl/v5/ifa_phi_p2_relation_block.sv \
  rtl/v5/ifa_phi_p8_relation_ripple.sv \
  rtl/v5/tb_ifa_phi_p8_relation_ripple.sv
vvp build/v5/tb_phi_p8_relation_ripple.vvp \
  2>&1 | tee build/v5/tb_phi_p8_relation_ripple_output.txt
