from ifa_v4_rmu import RelationMemoryUnit, DEPTH

def main():
    rmu = RelationMemoryUnit(depth=DEPTH)

    # First access: MISS + store
    f1, h1 = rmu.access(0x0D, 0x06)

    # Second access: HIT
    f2, h2 = rmu.access(0x0D, 0x06)

    assert h1 is False
    assert h2 is True
    assert f1 == f2

    # Security flush
    rmu.clear()

    # After clear, same input must MISS again
    f3, h3 = rmu.access(0x0D, 0x06)

    assert h3 is False
    assert f3 == f1

    print("V4 RMU CLEAR SECURITY TEST")
    print("=" * 60)
    print("first access miss:", h1 is False)
    print("second access hit:", h2 is True)
    print("after clear miss:", h3 is False)
    print("entries after reload:", len(rmu.entries))
    print("PASS: RMU clear prevents stale relation-frame reuse")

if __name__ == "__main__":
    main()
