from ifa_v4_rmu import compute_frame, DEPTH

class TTLRMU:
    def __init__(self, depth=DEPTH, ttl=3):
        self.depth = depth
        self.ttl = ttl
        self.entries = []
        self.time = 0
        self.hits = 0
        self.misses = 0
        self.expired = 0

    def make_key(self, frame):
        return (frame.RA, frame.RD, frame.T)

    def access(self, A, B):
        self.time += 1
        frame = compute_frame(A, B)
        key = self.make_key(frame)

        # Remove expired entries
        alive = []
        for entry in self.entries:
            age = self.time - entry["time"]
            if age <= self.ttl:
                alive.append(entry)
            else:
                self.expired += 1
        self.entries = alive

        # Lookup
        for entry in self.entries:
            if entry["key"] == key:
                self.hits += 1
                entry["time"] = self.time
                return entry["frame"], True

        # Miss + store
        self.misses += 1

        if len(self.entries) >= self.depth:
            self.entries.pop(0)

        self.entries.append({
            "key": key,
            "frame": frame,
            "time": self.time,
        })

        return frame, False


def main():
    rmu = TTLRMU(depth=DEPTH, ttl=3)

    A = 0x0D
    B = 0x06

    # First access: MISS
    f1, h1 = rmu.access(A, B)

    # Immediate second access: HIT
    f2, h2 = rmu.access(A, B)

    # Advance time using other accesses
    rmu.access(0x01, 0x02)
    rmu.access(0x03, 0x04)
    rmu.access(0x05, 0x06)
    rmu.access(0x07, 0x08)

    # Original relation should now be expired, so MISS
    f3, h3 = rmu.access(A, B)

    assert h1 is False
    assert h2 is True
    assert h3 is False
    assert f1 == f2 == f3

    print("V4 RMU TTL / EXPIRY SECURITY TEST")
    print("=" * 60)
    print("first access miss:", h1 is False)
    print("second access hit before expiry:", h2 is True)
    print("after TTL expiry miss:", h3 is False)
    print("expired entries:", rmu.expired)
    print("hits:", rmu.hits)
    print("misses:", rmu.misses)
    print("PASS: expired relation frames are not reused")

if __name__ == "__main__":
    main()
