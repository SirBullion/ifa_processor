"""Native, non-security IFÁ services for the V4.5 language shell."""
from __future__ import annotations

import random
import re
import unicodedata

from dataclasses import replace

from runtime.frame_builder import build_relation_frame
from runtime.relation_memory_unit import RelationMemoryUnit

PRINTODU_NAMES = (
    "ÒGBÈ", "ÒGÚNDÁ", "ÌRETẸ̀", "ÌRÒSÙN", "ÒTÚRÁ", "ÒṢÉ", "ÒDÍ", "ÒBÀRÀ",
    "ÒSÁ", "ÌWÒRÌ", "ÒFÚN", "ÌKÁ", "ÒWÓNRÍN", "ÒTÚRÚPỌ̀N", "ÒKÀNRÀN", "ÒYÈKÚ",
)
DAIFA_ODU = (
    ("ÒGBÈ", "light, openness, clarity, emergence"),
    ("ÒYÈKÚ", "depth, concealment, endings, ancestral shadow"),
    ("ÌWÒRÌ", "reflection, inner seeing, transformation"),
    ("ÒDÍ", "boundary, enclosure, protection, resistance"),
    ("ÌRÒSÙN", "lineage, earth, blood, foundation"),
    ("ÒWÓNRÍN", "movement, instability, turning point"),
    ("ÒBÀRÀ", "speech, exchange, manifestation"),
    ("ÒKÀNRÀN", "fire, conflict, intensity, correction"),
    ("ÒGÚNDÁ", "cutting, force, iron, breakthrough"),
    ("ÒSÁ", "wind, change, dispersal, sudden shift"),
    ("ÌKÁ", "constraint, danger, entanglement"),
    ("ÒTÚRÚPỌ̀N", "inheritance, burden, continuity"),
    ("ÒTÚRÁ", "elevation, clarity, spiritual opening"),
    ("ÌRẸ̀TẸ̀", "pressure, endurance, refinement"),
    ("ÒṢÉ", "sweetness, renewal, cleansing, blessing"),
    ("ÒFÚN", "completion, whiteness, fullness, closure"),
)
TEIFA_NAMES = {f"{value:04b}": name for value, name in enumerate(PRINTODU_NAMES)}


def normalize_name(value):
    value = unicodedata.normalize("NFKD", value.strip().upper())
    return "".join(c for c in value if not unicodedata.combining(c) and c.isalnum())


TEIFA_ALIASES = {normalize_name(name): bits for bits, name in TEIFA_NAMES.items()}
TEIFA_ALIASES.update(dict(zip(
    ("OGBE", "OGUNDA", "IRETE", "IROSUN", "OTURA", "OSE", "ODI", "OBARA",
     "OSA", "IWORI", "OFUN", "IKA", "OWONRIN", "OTURUPON", "OKANRAN", "OYEKU"),
    TEIFA_NAMES,
)))


class IfaServicesV45:
    """Stateful V4.5 services with no dependency on the V4 monitor."""

    def __init__(self, random_source=None):
        self.random = random_source or random.SystemRandom()
        self.rmu = RelationMemoryUnit()
        self.reset()

    def reset(self):
        self.rmu.clear()
        self.last_frame = self.last_backend_execution = None
        self.last_channels = None
        self.last_opele = self.last_teifa = None
        self.relation_number = 0

    def record_execution(self, request, result, backend_execution=None):
        self.last_backend_execution = backend_execution
        self.last_channels = (
            self._service_channels(backend_execution, None)
            if self._is_quantum_relation(backend_execution) else None
        )
        try:
            self.relation_number += 1
            if self._is_relation_frame(backend_execution):
                backend_execution.validate()
                self.last_frame = backend_execution
            elif self._is_quantum_relation(backend_execution):
                self.last_frame = self._frame_from_quantum(
                    f"R{self.relation_number}", backend_execution,
                )
            else:
                self.last_frame = build_relation_frame(
                    f"R{self.relation_number}", request.operator_name,
                    request.operand_a, request.operand_b, result,
                )
            if self.last_channels is None:
                self.last_channels = self._service_channels(backend_execution, self.last_frame)
            stored_frame = replace(
                self.last_frame,
                relation_id=f"R{self.relation_number}",
            )
            self.rmu.store(stored_frame, ())
        except (TypeError, ValueError):
            self.last_frame = None

    @staticmethod
    def _service_channels(record, frame):
        if record is not None and all(hasattr(record, name) for name in ("y", "ra", "rd", "r0", "t")):
            return {name: int(getattr(record, name)) & 0xFF for name in ("y", "ra", "rd", "r0", "t")}
        return {
            "y": frame.Y, "ra": frame.RA, "rd": frame.RD,
            "r0": frame.R0, "t": frame.T,
        }

    @staticmethod
    def _is_relation_frame(record):
        return record is not None and all(
            hasattr(record, field) for field in ("Y", "RA", "RD", "R0", "T", "validate")
        )

    @staticmethod
    def _is_quantum_relation(record):
        return record is not None and all(
            hasattr(record, field) for field in
            ("operation", "operand_a", "operand_b", "logical_result", "y", "ra", "rd", "r0", "t")
        )

    @staticmethod
    def _frame_from_quantum(relation_id, record):
        frame = build_relation_frame(
            relation_id, record.operation, record.operand_a,
            record.operand_b, record.logical_result,
        )
        expected = (frame.Y, frame.RA, frame.RD, frame.R0)
        actual = (record.y, record.ra, record.rd, record.r0)
        if actual != expected:
            raise ValueError("Quantum relation channels disagree with the canonical V4.5 frame.")
        return frame

    @staticmethod
    def odu_name(value):
        return PRINTODU_NAMES[value & 0x0F]

    @classmethod
    def print_field(cls, label, value):
        value &= 0xFF
        print(f"{label:<8}= 0x{value:02X}  {cls.odu_name(value >> 4)} {cls.odu_name(value)}")

    def daifa(self):
        print("═══════════════════════════════════════")
        print("        DÁ IFÁ — THE SIXTEEN OJÚ ODÙ")
        print("═══════════════════════════════════════")
        for value, (name, meaning) in enumerate(DAIFA_ODU):
            print(f"0x{value:02X}  {name:<12}  — {meaning}")
        print("═══════════════════════════════════════")

    def printodu(self, all_fields=False):
        if self.last_channels is None:
            print("KÒ SÍ ÀBÁJÁDE.")
            return
        print("\nÀBÁJÁDE\n--------")
        fields = [("OYÈLÁ", self.last_channels["y"])]
        if all_fields:
            fields += [("FARAPỌ̀", self.last_channels["ra"]), ("YÀTỌ̀", self.last_channels["rd"]),
                       ("ÌPÌLẸ̀", self.last_channels["r0"]), ("GBÉ", self.last_channels["t"])]
        for label, value in fields:
            self.print_field(label, value)

    @staticmethod
    def marks(bits):
        return tuple("I" if bit == "0" else "II" for bit in bits)

    def render_opele(self, right, left):
        right_bits, left_bits = f"{right:04b}", f"{left:04b}"
        print("\n                         ÈṢÙ\n                          ●")
        print("\n                     ÒPẸ̀LẸ̀\n\n              Ọ̀TÚN            ÒSÌ\n")
        for a, b in zip(self.marks(right_bits), self.marks(left_bits)):
            print(f"                {a:<16}{b}")
        print(f"\nODÙ    : {self.odu_name(right)} {self.odu_name(left)}")
        print(f"ÀMÌ    : {right_bits} {left_bits}\nÀTỌ́KA : {right}:{left}\n")

    def opele(self, repeat=False):
        if repeat and self.last_opele is None:
            print("KÒ SÍ ÒPẸ̀LẸ̀ TÍ A TI DÁ.")
            return
        if not repeat:
            self.last_opele = (self.random.randrange(16), self.random.randrange(16))
        self.render_opele(*self.last_opele)

    @staticmethod
    def resolve_teifa(token):
        token = token.strip().replace("_", "")
        return token if re.fullmatch(r"[01]{4}", token) else TEIFA_ALIASES.get(normalize_name(token))

    def render_teifa(self, values):
        if len(values) == 1:
            bits = values[0]
            print("\nTẸ IFÁ\n------\n")
            for mark in self.marks(bits):
                print(f"             {mark}")
            print(f"\nODÙ : {TEIFA_NAMES[bits]}\nÀMÌ : {bits}\n")
            return
        right, left = values
        print("\nTẸ IFÁ\n------\n\n          Ọ̀TÚN          ÒSÌ\n")
        for a, b in zip(self.marks(right), self.marks(left)):
            print(f"            {a:<14}{b}")
        name = f"{TEIFA_NAMES[right]} MÉJÌ" if right == left else f"{TEIFA_NAMES[right]} {TEIFA_NAMES[left]}"
        print(f"\nODÙ : {name}\nÀMÌ : {right} {left}")
        print(f"Ọ̀TÚN: {TEIFA_NAMES[right]} ({right})\nÒSÌ : {TEIFA_NAMES[left]} ({left})\n")

    def teifa(self, arguments):
        if len(arguments) == 1 and normalize_name(arguments[0]) in {"LAST", "AGAIN"}:
            if self.last_teifa is None:
                print("KÒ SÍ ODÙ TẸ IFÁ TÍ A TI FI SÍLẸ̀.")
                return
            self.render_teifa(self.last_teifa)
            return
        if len(arguments) == 1 and re.fullmatch(r"[01]{8}", arguments[0]):
            values = (arguments[0][:4], arguments[0][4:])
        elif len(arguments) == 1:
            values = (self.resolve_teifa(arguments[0]),)
        elif len(arguments) == 2:
            right = self.resolve_teifa(arguments[0])
            left = right if normalize_name(arguments[1]) == "MEJI" else self.resolve_teifa(arguments[1])
            values = (right, left)
        else:
            print("Lo: TEIFA <ODÙ> [ODÙ|MEJI] | TEIFA <8 bits> | TEIFA LAST")
            return
        if any(value is None for value in values):
            print("KÒ MỌ ODÙ.")
            return
        self.last_teifa = values
        self.render_teifa(values)

    def handle(self, line):
        words = line.strip().split()
        if not words:
            return False
        command = normalize_name(words[0])
        if command == "DAIFA":
            self.daifa(); return True
        if command == "PRINTODU":
            self.printodu(); return True
        if command == "PRINTODUALL":
            self.printodu(all_fields=True); return True
        if command == "OPELE":
            repeat = len(words) == 2 and normalize_name(words[1]) in {"LAST", "AGAIN"}
            if len(words) > 2 or (len(words) == 2 and not repeat):
                print("Lo: OPELE | OPELE LAST"); return True
            self.opele(repeat=repeat); return True
        if command == "TEIFA" or (command == "TE" and len(words) >= 2 and normalize_name(words[1]) == "IFA"):
            self.teifa(words[2:] if command == "TE" else words[1:]); return True
        return False


ifa_services_v45 = IfaServicesV45()
