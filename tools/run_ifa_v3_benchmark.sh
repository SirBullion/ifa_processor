#!/bin/bash
set -e

echo "Ń ṢE IFÁ V3 BENCHMARK..."
./ifarun programs_v3/ifa_v3_benchmark.ifa3

echo
echo "ÀṢEYỌRÍ."
echo "Waveform: sim/odu_v2_cpu.vcd"
echo "Open with:"
echo "  gtkwave sim/odu_v2_cpu.vcd"
