#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RMUEntry:
    operation: str
    y: int
    ra: int
    rd: int
    r0: int
    t: int

    first_a: int
    first_b: int

    executions: int = 0
    hits: int = 0
    misses: int = 0

    valid: int = 1
    exception: int = 0
    exception_code: int = 0
    state: int = 0
    state_code: int = 0

    eq: int = 0
    gt: int = 0
    lt: int = 0


@dataclass
class YaraRMU:
    entries: dict[tuple[Any, ...], RMUEntry] = field(
        default_factory=dict
    )

    executions: int = 0
    hits: int = 0
    misses: int = 0

    last_key: tuple[Any, ...] | None = None


class RMUView:
    """
    Human-facing mirror of V4 relation-memory activity.

    The hardware remains authoritative. This class records the HIT/MISS
    and complete relation frame returned by the V4 bridge so Babaláwo
    mode can inspect relation reuse per YÀRÁ.
    """

    def __init__(self) -> None:
        self.yaras: dict[int, YaraRMU] = {}

    def _get_yara(
        self,
        yara_id: int,
    ) -> YaraRMU:
        if yara_id not in self.yaras:
            self.yaras[yara_id] = YaraRMU()

        return self.yaras[yara_id]

    @staticmethod
    def relation_key(
        result,
    ) -> tuple[Any, ...]:
        """
        Canonical V4 RMU key:

            K = {OP, RA, RD, T}
        """

        return (
            str(result.operation),
            int(result.ra) & 0xFF,
            int(result.rd) & 0xFF,
            int(result.t) & 0xFF,
        )

    def record(
        self,
        yara_id: int,
        result,
    ) -> None:
        yara = self._get_yara(yara_id)
        key = self.relation_key(result)

        yara.executions += 1
        yara.hits += int(bool(result.hit))
        yara.misses += int(bool(result.miss))
        yara.last_key = key

        entry = yara.entries.get(key)

        if entry is None:
            entry = RMUEntry(
                operation=str(result.operation),

                y=int(result.y) & 0xFF,
                ra=int(result.ra) & 0xFF,
                rd=int(result.rd) & 0xFF,
                r0=int(result.r0) & 0xFF,
                t=int(result.t) & 0xFF,

                first_a=int(result.a) & 0xFF,
                first_b=int(result.b) & 0xFF,
            )

            yara.entries[key] = entry

        entry.executions += 1
        entry.hits += int(bool(result.hit))
        entry.misses += int(bool(result.miss))

        entry.y = int(result.y) & 0xFF
        entry.r0 = int(result.r0) & 0xFF

        entry.valid = int(result.valid)
        entry.exception = int(result.exception)
        entry.exception_code = int(result.exception_code)

        entry.state = int(result.state)
        entry.state_code = int(result.state_code)

        entry.eq = int(result.eq)
        entry.gt = int(result.gt)
        entry.lt = int(result.lt)

    def clear(
        self,
        yara_id: int | None = None,
    ) -> None:
        if yara_id is None:
            self.yaras.clear()
            return

        self.yaras.pop(yara_id, None)

    def show_stats(
        self,
        yara_id: int,
        yara_name: str,
    ) -> None:
        yara = self.yaras.get(yara_id)

        print()
        print("RELATION MEMORY UNIT")
        print("--------------------")
        print(f"YÀRÁ       : {yara_name}")
        print(f"Context ID : {yara_id}")

        if yara is None:
            print("Entries    : 0")
            print("Executions : 0")
            print("Hits       : 0")
            print("Misses     : 0")
            print("Reuse rate : 0.00%")
            print()
            return

        reuse_rate = (
            100.0 * yara.hits / yara.executions
            if yara.executions
            else 0.0
        )

        print(f"Entries    : {len(yara.entries)}")
        print(f"Executions : {yara.executions}")
        print(f"Hits       : {yara.hits}")
        print(f"Misses     : {yara.misses}")
        print(f"Reuse rate : {reuse_rate:.2f}%")
        print()

    def show_last(
        self,
        yara_id: int,
        yara_name: str,
    ) -> None:
        yara = self.yaras.get(yara_id)

        if (
            yara is None
            or yara.last_key is None
            or yara.last_key not in yara.entries
        ):
            print("KÒ SÍ ÌBÁṢẸ̀PỌ̀ NÍ RMU YÀRÁ YÌÍ.")
            return

        entry = yara.entries[yara.last_key]

        print()
        print("LATEST RMU RELATION")
        print("-------------------")
        print(f"YÀRÁ       : {yara_name}")
        print(f"Context ID : {yara_id}")
        print()
        print(f"Operation  : {entry.operation}")
        print(
            f"First input: "
            f"A=0x{entry.first_a:02X} "
            f"B=0x{entry.first_b:02X}"
        )
        print()
        print(f"Y          : 0x{entry.y:02X}")
        print(f"Agreement  : 0x{entry.ra:02X}")
        print(f"Disagree   : 0x{entry.rd:02X}")
        print(f"Base       : 0x{entry.r0:02X}")
        print(f"Transport  : 0x{entry.t:02X}")
        print()
        print(f"Executions : {entry.executions}")
        print(f"Hits       : {entry.hits}")
        print(f"Misses     : {entry.misses}")
        print()
        print(
            f"VALID={entry.valid} "
            f"EXC={entry.exception} "
            f"STATE={entry.state}"
        )
        print(
            f"EQ={entry.eq} "
            f"GT={entry.gt} "
            f"LT={entry.lt}"
        )
        print()

    def show_entries(
        self,
        yara_id: int,
        yara_name: str,
    ) -> None:
        yara = self.yaras.get(yara_id)

        print()
        print("RMU RELATION TABLE")
        print("------------------")
        print(f"YÀRÁ       : {yara_name}")
        print(f"Context ID : {yara_id}")
        print()

        if yara is None or not yara.entries:
            print("No preserved relations.")
            print()
            return

        print(
            "No. OP      Y  RA RD R0 T  "
            "RUN HIT MISS"
        )
        print(
            "--- ------- -- -- -- -- -- "
            "--- --- ----"
        )

        ordered = sorted(
            yara.entries.values(),
            key=lambda entry: (
                entry.operation,
                entry.ra,
                entry.rd,
                entry.t,
            ),
        )

        for index, entry in enumerate(
            ordered,
            start=1,
        ):
            print(
                f"{index:>3} "
                f"{entry.operation:<7} "
                f"{entry.y:02X} "
                f"{entry.ra:02X} "
                f"{entry.rd:02X} "
                f"{entry.r0:02X} "
                f"{entry.t:02X} "
                f"{entry.executions:>3} "
                f"{entry.hits:>3} "
                f"{entry.misses:>4}"
            )

        print()
