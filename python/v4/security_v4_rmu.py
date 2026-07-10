from ifa_v4_rmu import RelationMemoryUnit, compute_frame, DEPTH

def security_test():
    rmu = RelationMemoryUnit(depth=DEPTH)

    false_hits = 0
    leakage_score = 0

    # 1. Same input should hit on second access
    f1, h1 = rmu.access(0x0D, 0x06)
    f2, h2 = rmu.access(0x0D, 0x06)

    assert h1 is False
    assert h2 is True
    assert f1 == f2

    # 2. Different inputs should never return wrong frame
    for A in range(256):
        for B in range(256):
            expected = compute_frame(A, B)
            got, hit = rmu.access(A, B)

            if hit and got != expected:
                false_hits += 1
                leakage_score += 1

    print("V4 RMU SECURITY TEST")
    print("=" * 60)
    print("false_hits:", false_hits)
    print("leakage_score:", leakage_score)
    print("hits:", rmu.hits)
    print("misses:", rmu.misses)
    print("stores:", rmu.stores)
    print("evictions:", rmu.evictions)

    assert false_hits == 0
    assert leakage_score == 0

    print("PASS: no unsafe relation-frame leakage detected")

if __name__ == "__main__":
    security_test()
