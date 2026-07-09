import subprocess
import sys
from pathlib import Path

tests = [
    "ifa_v4_rmu.py",
    "verify_ifa_v4_rmu.py",
    "bench_ifa_v4_rmu.py",
    "verify_v4_key_safety.py",
    "compare_v4_keys.py",
]

base = Path(__file__).parent

print("IFÁ V4 FULL PYTHON TEST RUN")
print("=" * 70)

for test in tests:
    path = base / test
    print(f"\nRUNNING: {test}")
    print("-" * 70)

    result = subprocess.run(
        [sys.executable, str(path)],
        text=True,
        capture_output=True
    )

    print(result.stdout)

    if result.stderr:
        print("STDERR:")
        print(result.stderr)

    if result.returncode != 0:
        print(f"FAILED: {test}")
        sys.exit(result.returncode)

print("\n" + "=" * 70)
print("ALL V4 PYTHON TESTS COMPLETED")
