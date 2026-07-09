#!/usr/bin/env bash
set -e

echo "=================================================="
echo "IFÁ V4 RTL TEST RUN"
echo "=================================================="

echo
echo "Running Relation Memory Controller TB..."
iverilog -g2012 \
  -o sim/v4/tb_ifa_relation_memory_controller.out \
  rtl/v4/ifa_relation_memory_controller.sv \
  tb/v4/tb_ifa_relation_memory_controller.sv
vvp sim/v4/tb_ifa_relation_memory_controller.out

echo
echo "Running V4 Core Wrapper TB..."
iverilog -g2012 \
  -o sim/v4/tb_ifa_v4_core.out \
  rtl/v4/ifa_relation_memory_controller.sv \
  rtl/v4/ifa_v4_core.sv \
  tb/v4/tb_ifa_v4_core.sv
vvp sim/v4/tb_ifa_v4_core.out

echo
echo "Running V4 Reuse Workload TB..."
iverilog -g2012 \
  -o sim/v4/tb_ifa_v4_reuse_workload.out \
  rtl/v4/ifa_relation_memory_controller.sv \
  rtl/v4/ifa_v4_core.sv \
  tb/v4/tb_ifa_v4_reuse_workload.sv
vvp sim/v4/tb_ifa_v4_reuse_workload.out

echo
echo "Running V4 End-to-End Core TB..."
iverilog -g2012 \
  -o sim/v4/tb_ifa_v4_end_to_end_core.out \
  rtl/v4/ifa_relation_memory_controller.sv \
  rtl/v4/ifa_v4_core.sv \
  rtl/v4/ifa_rpc_stub.sv \
  rtl/v4/ifa_v4_end_to_end_core.sv \
  tb/v4/tb_ifa_v4_end_to_end_core.sv
vvp sim/v4/tb_ifa_v4_end_to_end_core.out

echo "=================================================="
echo "ALL V4 RTL TESTS COMPLETED"
echo "=================================================="
