# ============================================================
# IFÁ V4 RMU Verification
#
# Verifies:
# 1. Exact hit rule
# 2. Hit returns stored full frame
# 3. FIFO eviction
# 4. Repeated workload produces reuse
# ============================================================

from ifa_v4_rmu import RelationMemoryUnit, compute_frame, DEPTH


def verify_exact_hit():
    rmu = RelationMemoryUnit(depth=DEPTH)

    A, B = 13, 6

    frame1, hit1 = rmu.access(A, B)
    frame2, hit2 = rmu.access(A, B)

    assert hit1 is False
    assert hit2 is True
    assert frame1 == frame2

    print("PASS: exact hit returns stored full frame")


def verify_fifo():
    depth = 4
    rmu = RelationMemoryUnit(depth=depth)

    for i in range(8):
        rmu.access(i, i + 1)

    assert len(rmu.entries) == depth
    assert rmu.evictions > 0

    print("PASS: FIFO eviction works")


def verify_reuse_workload():
    rmu = RelationMemoryUnit(depth=DEPTH)

    workload = [
        (13, 6),
        (7, 8),
        (13, 6),
        (7, 8),
        (1, 2),
        (1, 2),
        (9, 10),
        (9, 10),
    ]

    hits = 0
    misses = 0

    for A, B in workload:
        _, hit = rmu.access(A, B)
        if hit:
            hits += 1
        else:
            misses += 1

    assert hits == 4
    assert misses == 4

    print("PASS: repeated relations produce reuse")


def verify_key_width_logic():
    for A in range(256):
        for B in range(256):
            frame = compute_frame(A, B)
            RA, RD, T = frame.key()

            assert 0 <= RA <= 255
            assert 0 <= RD <= 255
            assert 0 <= T <= 255

    print("PASS: WIDTH=8 key fields stay 8-bit")


def main():
    print("IFÁ V4 RMU VERIFICATION")
    print("=" * 60)

    verify_exact_hit()
    verify_fifo()
    verify_reuse_workload()
    verify_key_width_logic()

    print("=" * 60)
    print("ALL V4 RMU PYTHON TESTS PASSED")


if __name__ == "__main__":
    main()
