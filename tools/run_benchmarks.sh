#!/bin/bash
set -e

echo "====================================="
echo " IFÁ Processor Benchmark Suite"
echo "====================================="

for f in benchmarks/*.ifa3
do
    echo
    echo "Running: $f"
    ./ifarun "$f"
done

echo
echo "====================================="
echo "Benchmark Suite Complete"
echo "====================================="
echo
echo "Waveform:"
echo "  sim/odu_v2_cpu.vcd"
echo
echo "Open:"
echo "  gtkwave sim/odu_v2_cpu.vcd"
