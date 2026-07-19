#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/.."

echo "========================================================================"
echo "IFÁ PROCESSOR V4.5 RELATION RUNTIME VERIFICATION"
echo "========================================================================"

python3 -m py_compile \
    compiler/phi_p8_adapter.py \
    compiler/relation_canonicalizer.py \
    compiler/relation_deduplicator.py \
    compiler/relation_reference.py \
    compiler/relation_graph.py \
    runtime/relation_frame.py \
    runtime/frame_builder.py \
    runtime/relation_memory_unit.py \
    runtime/relation_executor.py \
    tests/test_relation_runtime_v45.py

python3 -m unittest \
    tests.test_relation_runtime_v45 \
    -v
