#!/usr/bin/env python3

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from language_v45.kernel import kernel

print()
print("========================================")
print("      IFÁ PROCESSOR V4.5 MVP")
print("========================================")
print("Native RMU Computation Engine")
print("Type HELP for commands")
print()

kernel.run()
