# ============================================================
# IFÁ Processor V4 — Python RMU Model
#
# WIDTH = 8
# FRAME = {Y, RA, RD, R0, T} = 40 bits
# KEY   = {RA, RD, T} = 24 bits
# DEPTH = 16
# HIT   = exact key match
# EVICT = FIFO
# ============================================================

from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict

WIDTH = 8
MASK = (1 << WIDTH) - 1
DEPTH = 16


@dataclass(frozen=True)
class RelationFrame:
    Y: int
    RA: int
    RD: int
    R0: int
    T: int

    def key(self) -> Tuple[int, int, int]:
        # KEY = {RA, RD, T}
        return (self.RA, self.RD, self.T)

    def hex(self) -> str:
        return (
            f"Y=0x{self.Y:02X} "
            f"RA=0x{self.RA:02X} "
            f"RD=0x{self.RD:02X} "
            f"R0=0x{self.R0:02X} "
            f"T=0x{self.T:02X}"
        )


def compute_frame(A: int, B: int) -> RelationFrame:
    A &= MASK
    B &= MASK

    Y = (A + B) & MASK
    RA = A & B
    RD = A ^ B
    R0 = (~(A | B)) & MASK

    # V4 starting transport model:
    # minimum relation distance placeholder = Hamming weight of disagreement
    T = RD.bit_count() & MASK

    return RelationFrame(Y=Y, RA=RA, RD=RD, R0=R0, T=T)


@dataclass
class RMUEntry:
    key: Tuple[int, int, int]
    frame: RelationFrame


class RelationMemoryUnit:
    def __init__(self, depth: int = DEPTH):
        self.depth = depth
        self.entries: List[RMUEntry] = []

        self.hits = 0
        self.misses = 0
        self.stores = 0
        self.evictions = 0

    def lookup(self, key: Tuple[int, int, int]) -> Optional[RelationFrame]:
        for entry in self.entries:
            if entry.key == key:
                self.hits += 1
                return entry.frame

        self.misses += 1
        return None

    def store(self, key: Tuple[int, int, int], frame: RelationFrame) -> None:
        # Update existing key if already present
        for entry in self.entries:
            if entry.key == key:
                entry.frame = frame
                return

        # FIFO eviction
        if len(self.entries) >= self.depth:
            self.entries.pop(0)
            self.evictions += 1

        self.entries.append(RMUEntry(key=key, frame=frame))
        self.stores += 1

    def access(self, A: int, B: int) -> Tuple[RelationFrame, bool]:
        computed = compute_frame(A, B)
        key = computed.key()

        cached = self.lookup(key)

        if cached is not None:
            return cached, True

        self.store(key, computed)
        return computed, False


    def clear(self) -> None:
        """Security flush: remove all stored relation frames."""
        self.entries.clear()

    def stats(self) -> Dict[str, float]:
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "stores": self.stores,
            "evictions": self.evictions,
            "entries": len(self.entries),
            "hit_rate": self.hits / total if total else 0.0,
        }

    def dump(self) -> None:
        print("\nRMU CONTENTS")
        print("=" * 80)

        for i, entry in enumerate(self.entries):
            RA, RD, T = entry.key
            print(
                f"[{i:02d}] "
                f"KEY={{RA=0x{RA:02X}, RD=0x{RD:02X}, T=0x{T:02X}}} "
                f"FRAME={{ {entry.frame.hex()} }}"
            )


def run_demo() -> None:
    workload = [
        (13, 6),
        (7, 8),
        (13, 6),   # hit
        (7, 8),    # hit
        (1, 2),
        (3, 4),
        (5, 6),
        (1, 2),    # hit
        (9, 10),
        (11, 12),
        (13, 14),
        (15, 0),
        (9, 10),   # hit
    ]

    rmu = RelationMemoryUnit(depth=DEPTH)

    print("IFÁ V4 RMU PYTHON MODEL")
    print("=" * 80)

    for cycle, (A, B) in enumerate(workload):
        frame, hit = rmu.access(A, B)
        key = frame.key()

        print(
            f"cycle={cycle:02d} "
            f"A=0x{A:02X} B=0x{B:02X} "
            f"{'HIT ' if hit else 'MISS'} "
            f"KEY=(RA=0x{key[0]:02X}, RD=0x{key[1]:02X}, T=0x{key[2]:02X}) "
            f"{frame.hex()}"
        )

    rmu.dump()

    print("\nSTATS")
    print("=" * 80)
    for k, v in rmu.stats().items():
        print(f"{k}: {v}")

    print("\nVERIFICATION")
    print("=" * 80)

    # Hit returns exact stored frame
    test = RelationMemoryUnit(depth=DEPTH)
    f1, h1 = test.access(13, 6)
    f2, h2 = test.access(13, 6)

    print("first access is miss:", h1 is False)
    print("second access is hit:", h2 is True)
    print("hit returns exact stored frame:", f1 == f2)

    # FIFO eviction
    fifo = RelationMemoryUnit(depth=4)
    for i in range(8):
        fifo.access(i, i + 1)

    print("FIFO eviction occurred:", fifo.evictions > 0)
    print("FIFO entries == depth:", len(fifo.entries) == 4)
    print("FIFO evictions:", fifo.evictions)


if __name__ == "__main__":
    run_demo()
