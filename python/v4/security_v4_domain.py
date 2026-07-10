from ifa_v4_rmu import RelationMemoryUnit, compute_frame, DEPTH

class DomainRMU(RelationMemoryUnit):
    def make_domain_key(self, domain, frame):
        # Security-domain key extension:
        # KEY = {DOMAIN, RA, RD, T}
        return (domain, frame.RA, frame.RD, frame.T)

    def access_domain(self, domain, A, B):
        frame = compute_frame(A, B)
        key = self.make_domain_key(domain, frame)

        cached = self.lookup(key)
        if cached is not None:
            return cached, True

        self.store(key, frame)
        return frame, False


def main():
    rmu = DomainRMU(depth=DEPTH)

    A = 0x0D
    B = 0x06

    # Domain 0 first access: MISS
    f0a, h0a = rmu.access_domain(0, A, B)

    # Domain 0 second access: HIT
    f0b, h0b = rmu.access_domain(0, A, B)

    # Same A,B in Domain 1 must MISS
    f1a, h1a = rmu.access_domain(1, A, B)

    # Domain 1 second access: HIT
    f1b, h1b = rmu.access_domain(1, A, B)

    assert h0a is False
    assert h0b is True
    assert h1a is False
    assert h1b is True

    assert f0a == f0b
    assert f1a == f1b
    assert f0a == f1a

    print("V4 RMU DOMAIN SECURITY TEST")
    print("=" * 60)
    print("domain 0 first access miss:", h0a is False)
    print("domain 0 second access hit:", h0b is True)
    print("domain 1 first access miss:", h1a is False)
    print("domain 1 second access hit:", h1b is True)
    print("cross-domain false hit:", h1a is True)
    print("entries:", len(rmu.entries))
    print("PASS: same relation cannot be reused across security domains")

if __name__ == "__main__":
    main()
