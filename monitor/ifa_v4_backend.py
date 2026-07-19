#!/usr/bin/env python3

from __future__ import annotations

import queue
import re
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRIDGE = PROJECT_ROOT / "sim/v4/ifa_v4_os_bridge.out"


OP_SYMBOLS = {
    "+": "PAPO",
    "-": "YO",
    "*": "DAGBA",
    "/": "PIN",
    "%": "KU",
    "^": "GBE",
    "==": "SEDA",
    ">": "JU",
    "<": "KERE",
}


OP_ALIASES = {
    "PAPO": "PAPO",
    "PÀPỌ̀": "PAPO",

    "YO": "YO",
    "YỌ": "YO",

    "DAGBA": "DAGBA",
    "DÁGBA": "DAGBA",

    "PIN": "PIN",
    "PÍN": "PIN",

    "KU": "KU",
    "KÙ": "KU",

    "GBE": "GBE",
    "GBÉ": "GBE",

    "SEDA": "SEDA",
    "ṢẸ̀DÁ": "SEDA",

    "JU": "JU",
    "JÙ": "JU",

    "KERE": "KERE",
    "KERÉ": "KERE",
}


EXEC_RE = re.compile(
    r"EXEC ID=(?P<yara>\d+) "
    r"OP=(?P<op>[0-9a-fA-F]+) "
    r"HIT=(?P<hit>\d+) "
    r"MISS=(?P<miss>\d+) "
    r"Y=(?P<y>[0-9a-fA-F]{2}) "
    r"RA=(?P<ra>[0-9a-fA-F]{2}) "
    r"RD=(?P<rd>[0-9a-fA-F]{2}) "
    r"R0=(?P<r0>[0-9a-fA-F]{2}) "
    r"T=(?P<t>[0-9a-fA-F]{2}) "
    r"VALID=(?P<valid>\d+) "
    r"EXC=(?P<exc>\d+) "
    r"EXC_CODE=(?P<exc_code>[0-9a-fA-F]+) "
    r"STATE=(?P<state>\d+) "
    r"STATE_CODE=(?P<state_code>[0-9a-fA-F]+) "
    r"EQ=(?P<eq>\d+) "
    r"GT=(?P<gt>\d+) "
    r"LT=(?P<lt>\d+)"
)


@dataclass
class RelationResult:
    operation: str
    a: int
    b: int

    op: int
    y: int
    ra: int
    rd: int
    r0: int
    t: int

    hit: int
    miss: int

    valid: int
    exception: int
    exception_code: int

    state: int
    state_code: int

    eq: int
    gt: int
    lt: int

    @property
    def decimal(self) -> float | None:
        if self.operation in {"PIN", "KU"} and self.b != 0:
            return self.a / self.b

        return None


class V4Backend:
    def __init__(self) -> None:
        if not BRIDGE.exists():
            raise FileNotFoundError(
                f"V4 bridge not found: {BRIDGE}\n"
                "Run make test-v4 first."
            )

        self.process = subprocess.Popen(
            [
                "vvp",
                str(BRIDGE),
                "+INTERACTIVE",
            ],
            cwd=PROJECT_ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        if self.process.stdin is None or self.process.stdout is None:
            raise RuntimeError("Could not open V4 bridge pipes.")

        self.queue: queue.Queue[str] = queue.Queue()

        self.reader = threading.Thread(
            target=self._reader,
            daemon=True,
        )
        self.reader.start()

        self.last_result: RelationResult | None = None

        # Consume READY.
        self._collect()

        # Prepare the ordinary hidden execution YÀRÁ.
        self.command("BABALAWO ON", display=False)
        self.command("CREATE 0", display=False)
        self.command("SELECT 0", display=False)
        self.command("BABALAWO OFF", display=False)

    def _reader(self) -> None:
        assert self.process.stdout is not None

        for line in self.process.stdout:
            self.queue.put(line.rstrip("\n"))

    def _collect(
        self,
        first_timeout: float = 1.5,
        idle_timeout: float = 0.12,
    ) -> list[str]:
        lines: list[str] = []

        try:
            lines.append(
                self.queue.get(timeout=first_timeout)
            )
        except queue.Empty:
            return lines

        while True:
            try:
                lines.append(
                    self.queue.get(timeout=idle_timeout)
                )
            except queue.Empty:
                break

        return lines

    def command(
        self,
        command: str,
        *,
        display: bool = False,
    ) -> list[str]:
        if self.process.poll() is not None:
            raise RuntimeError("V4 bridge has stopped.")

        assert self.process.stdin is not None

        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

        lines = self._collect()

        if display:
            for line in lines:
                print(line)

        return lines

    def grant(
        self,
        source: int,
        destination: int,
        *,
        display: bool = False,
    ) -> list[str]:
        """Grant directional YÀRÁ frame-delegation permission."""
        return self.command(
            f"GRANT {source} {destination}",
            display=display,
        )

    def revoke(
        self,
        source: int,
        destination: int,
        *,
        display: bool = False,
    ) -> list[str]:
        """Revoke directional YÀRÁ frame-delegation permission."""
        return self.command(
            f"REVOKE {source} {destination}",
            display=display,
        )

    def share(
        self,
        source: int,
        destination: int,
        *,
        display: bool = False,
    ) -> list[str]:
        """Delegate the source YÀRÁ's latest relation frame."""
        return self.command(
            f"SHARE {source} {destination}",
            display=display,
        )

    def execute(
        self,
        operation: str,
        a: int,
        b: int,
    ) -> RelationResult:
        canonical = OP_ALIASES.get(
            operation.upper(),
            operation.upper(),
        )

        lines = self.command(
            f"EXEC {canonical} {a:02x} {b:02x}"
        )

        for line in lines:
            match = EXEC_RE.fullmatch(line.strip())

            if match is None:
                continue

            values = match.groupdict()

            result = RelationResult(
                operation=canonical,
                a=a,
                b=b,

                op=int(values["op"], 16),
                y=int(values["y"], 16),
                ra=int(values["ra"], 16),
                rd=int(values["rd"], 16),
                r0=int(values["r0"], 16),
                t=int(values["t"], 16),

                hit=int(values["hit"]),
                miss=int(values["miss"]),

                valid=int(values["valid"]),
                exception=int(values["exc"]),
                exception_code=int(
                    values["exc_code"],
                    16,
                ),

                state=int(values["state"]),
                state_code=int(
                    values["state_code"],
                    16,
                ),

                eq=int(values["eq"]),
                gt=int(values["gt"]),
                lt=int(values["lt"]),
            )

            self.last_result = result
            return result

        error_lines = [
            line
            for line in lines
            if (
                line.startswith("ERROR")
                or line.startswith("DENY")
            )
        ]

        if error_lines:
            raise RuntimeError("\n".join(error_lines))

        raise RuntimeError(
            "No V4 native result was returned."
        )

    def close(self) -> None:
        if self.process.poll() is not None:
            return

        try:
            self.command("QUIT")
        except Exception:
            pass

        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.terminate()
