#!/usr/bin/env python3

from __future__ import annotations

import copy
import io
import unicodedata
import random
import re
import sys

from contextlib import redirect_stdout
from pathlib import Path


#======================================================================
# Project import bootstrap
#======================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


#======================================================================
# IFÁ imports
#======================================================================

import monitor.ifa_monitor as v3

from language_v3.kernel import kernel
from monitor.ifa_v4_backend import (
    OP_ALIASES,
    OP_SYMBOLS,
    V4Backend,
)
from monitor.ifa_rmu_view import RMUView


#======================================================================
# Preserve the exact working V3 interface
#======================================================================

ORIGINAL_EXECUTE = v3.execute
V4 = V4Backend()
RMU_VIEW = RMUView()


#======================================================================
# OHÙN IFÁ 3.0 identity
#======================================================================

v3.BANNER = (
    v3.BANNER
    .replace(
        "Version      : 2.0",
        "Version      : 3.0",
    )
    .replace(
        "Architecture : ODU V2",
        "Architecture : ODU V3",
    )
)

v3.BANNER = v3.BANNER.replace(
    "Core         : Relation Processor Core (RPC)",
    "Core         : Relation Processor Core (RPC)\n"
    "Processor    : IFÁ Processor V4",
)


#======================================================================
# Normal result formatting
#======================================================================

def format_decimal(value: float) -> str:
    return (
        f"{value:.12f}"
        .rstrip("0")
        .rstrip(".")
    )


def print_clean_result(result) -> None:
    """
    Display a clean normal-computer result.

    The complete relation frame remains available in Babaláwo mode.
    """

    if result.exception:
        print(
            f"ÀṢÌṢE IFÁ "
            f"(EXC_CODE=0x{result.exception_code:X})"
        )
        return

    operation = result.operation

    if operation == "PAPO":
        print(
            f"{result.a} + {result.b} "
            f"= {result.y}"
        )
        return

    if operation == "YO":
        signed_result = (
            result.y - 256
            if result.y >= 128
            else result.y
        )

        print(
            f"{result.a} - {result.b} "
            f"= {signed_result}"
        )
        return

    if operation == "DAGBA":
        print(
            f"{result.a} × {result.b} "
            f"= {result.a * result.b}"
        )
        return

    if operation == "PIN":
        if result.b == 0:
            print("Division by zero.")
            return

        decimal_result = result.a / result.b

        print(
            f"{result.a} / {result.b} "
            f"= {format_decimal(decimal_result)}"
        )

        print(
            f"Exact: "
            f"{result.y} remainder {result.t}"
        )
        return

    if operation == "KU":
        if result.b == 0:
            print("Modulo by zero.")
            return

        print(
            f"{result.a} % {result.b} "
            f"= {result.y}"
        )

        print(
            f"Quotient: {result.t}"
        )
        return

    if operation == "GBE":
        print(
            f"{result.a} ^ {result.b} "
            f"= {result.a ** result.b}"
        )

        if result.state:
            print(
                "STATE: POWER RELATION EXTENDED "
                f"(0x{result.state_code:X})"
            )

        return

    if operation == "SEDA":
        print(
            f"{result.a} == {result.b} "
            f"= {'TRUE' if result.eq else 'FALSE'}"
        )
        return

    if operation == "JU":
        print(
            f"{result.a} > {result.b} "
            f"= {'TRUE' if result.gt else 'FALSE'}"
        )
        return

    if operation == "KERE":
        print(
            f"{result.a} < {result.b} "
            f"= {'TRUE' if result.lt else 'FALSE'}"
        )
        return

    print(result.y)


#======================================================================
# Babaláwo programmer output
#======================================================================

def print_programmer_result(result) -> None:
    print()
    print("IFÁ PROCESSOR V4 RELATION")
    print("-------------------------")

    print(f"OP       : {result.operation}")
    print(f"A        : 0x{result.a:02X}")
    print(f"B        : 0x{result.b:02X}")

    print(f"Y        : 0x{result.y:02X}")
    print(f"FARAPỌ̀  : 0x{result.ra:02X}")
    print(f"YÀTỌ̀    : 0x{result.rd:02X}")
    print(f"ÌPÌLẸ̀   : 0x{result.r0:02X}")
    print(f"GBÉ      : 0x{result.t:02X}")

    print(
        f"RMU      : "
        f"{'HIT' if result.hit else 'MISS'}"
    )

    print(f"VALID    : {result.valid}")

    print(
        f"EXC      : {result.exception} "
        f"CODE=0x{result.exception_code:X}"
    )

    print(
        f"STATE    : {result.state} "
        f"CODE=0x{result.state_code:X}"
    )

    print(
        f"COMPARE  : "
        f"EQ={result.eq} "
        f"GT={result.gt} "
        f"LT={result.lt}"
    )

    print()


#======================================================================
# V4 native execution
#======================================================================

def execute_native(
    operation: str,
    a: int,
    b: int,
) -> None:
    try:
        result = V4.execute(
            operation,
            a,
            b,
        )
    except Exception as error:
        print(f"ÀṢÌṢE: {error}")
        return

    # In the general shell, ordinary execution belongs to the
    # default OGBE context. Inside an explicit YÀRÁ, use its real ID.
    yara_id = (
        int(v3.ACTIVE_YARA)
        if v3.ACTIVE_YARA is not None
        else 0
    )

    RMU_VIEW.record(
        yara_id,
        result,
    )

    if v3.BABALAWO_MODE:
        print_programmer_result(result)
    else:
        print_clean_result(result)


#======================================================================
# Exact V3 PRINTODU mapping and display
#======================================================================

# This is the exact nibble order used by rtl/ifa_odu_printer.sv.
# Do not replace it with the OJU_ODU educational listing.
V3_PRINTODU_NAMES = (
    "ÒGBÈ",       # 0
    "ÒGÚNDÁ",     # 1
    "ÌRETẸ̀",      # 2
    "ÌRÒSÙN",     # 3
    "ÒTÚRÁ",      # 4
    "ÒṢÉ",        # 5
    "ÒDÍ",        # 6
    "ÒBÀRÀ",      # 7
    "ÒSÁ",        # 8
    "ÌWÒRÌ",      # 9
    "ÒFÚN",       # A
    "ÌKÁ",        # B
    "ÒWÓNRÍN",    # C
    "ÒTÚRÚPỌ̀N",  # D
    "ÒKÀNRÀN",    # E
    "ÒYÈKÚ",      # F
)


def oju_odu_name(value: int) -> str:
    """
    Return one exact V3 PRINTODU nibble name.
    """

    return V3_PRINTODU_NAMES[value & 0x0F]


def odu_pair_name(value: int) -> str:
    """
    V3 PRINTODU treats one byte as two Odù nibbles:

        high nibble, then low nibble
    """

    byte_value = value & 0xFF

    high = (byte_value >> 4) & 0x0F
    low = byte_value & 0x0F

    return (
        f"{oju_odu_name(high)} "
        f"{oju_odu_name(low)}"
    )


def print_odu_field(
    label: str,
    value: int,
) -> None:
    """
    Match the V3 PRINTODU representation:

        BYTE  HIGH-NIBBLE-NAME LOW-NIBBLE-NAME
    """

    byte_value = value & 0xFF

    print(
        f"{label:<8}= "
        f"0x{byte_value:02X}  "
        f"{odu_pair_name(byte_value)}"
    )


def printodu() -> None:
    result = V4.last_result

    if result is None:
        print("KÒ SÍ ÀBÁJÁDE.")
        return

    print()
    print("ÀBÁJÁDE")
    print("--------")

    print_odu_field(
        "OYÈLÁ",
        result.y,
    )


def printoduall() -> None:
    result = V4.last_result

    if result is None:
        print("KÒ SÍ ÀBÁJÁDE.")
        return

    print()
    print("ÀBÁJÁDE")
    print("--------")

    print_odu_field(
        "OYÈLÁ",
        result.y,
    )

    print_odu_field(
        "FARAPỌ̀",
        result.ra,
    )

    print_odu_field(
        "YÀTỌ̀",
        result.rd,
    )

    print_odu_field(
        "ÌPÌLẸ̀",
        result.r0,
    )

    print_odu_field(
        "GBÉ",
        result.t,
    )


#======================================================================
# Operand parsing
#======================================================================

def resolve_value(token: str) -> int:
    cleaned = token.strip()
    upper = cleaned.upper()

    if upper in kernel.numbers:
        return int(
            kernel.numbers[upper]
        )

    return int(
        v3.parse_value(cleaned)
    )


#======================================================================
# Symbolic arithmetic
#======================================================================

def try_symbolic_expression(
    command: str,
) -> bool:
    match = re.fullmatch(
        r"\s*"
        r"(0[xX][0-9a-fA-F]+|\d+)"
        r"\s*"
        r"(==|[+\-*/%^<>])"
        r"\s*"
        r"(0[xX][0-9a-fA-F]+|\d+)"
        r"\s*",
        command,
    )

    if match is None:
        return False

    left_text, symbol, right_text = (
        match.groups()
    )

    try:
        left = resolve_value(
            left_text
        )

        right = resolve_value(
            right_text
        )

    except Exception as error:
        print(
            f"Unknown IFÁ value: {error}"
        )
        return True

    execute_native(
        OP_SYMBOLS[symbol],
        left,
        right,
    )

    return True


#======================================================================
# Native Yorùbá operation form
#======================================================================

def try_native_words(
    command: str,
) -> bool:
    parts = command.strip().split()

    if len(parts) != 4:
        return False

    operation_word = parts[0].upper()
    relation_word = parts[2].upper()

    operation = OP_ALIASES.get(
        operation_word
    )

    if operation is None:
        return False

    if relation_word not in {
        "ATI",
        "ÀTI",
    }:
        print(
            "Lo ATI láàárín "
            "àwọn iye méjì."
        )
        return True

    try:
        a = resolve_value(
            parts[1]
        )

        b = resolve_value(
            parts[3]
        )

    except Exception:
        print("Unknown IFÁ value.")
        return True

    execute_native(
        operation,
        a,
        b,
    )

    return True


#======================================================================
# ÒPẸ̀LẸ̀ — complete casting service
#======================================================================

LAST_OPELE_CAST: tuple[int, int] | None = None


def odu_lines(
    value: int,
) -> tuple[str, str, str, str]:
    """
    Convert one four-bit Odù side into four vertical marks.

    Existing V3 bit convention:
        0 -> I
        1 -> II
    """

    nibble = value & 0x0F

    return tuple(
        "II"
        if ((nibble >> shift) & 1)
        else "I"
        for shift in (3, 2, 1, 0)
    )


def render_opele(
    right_value: int,
    left_value: int,
) -> None:
    """
    Display one complete ÒPẸ̀LẸ̀ cast.

    ÈṢÙ is fixed at the top centre.
    Both four-line sides are generated at once.
    """

    right_lines = odu_lines(
        right_value
    )

    left_lines = odu_lines(
        left_value
    )

    right_name = oju_odu_name(
        right_value
    )

    left_name = oju_odu_name(
        left_value
    )

    print()
    print("                         ÈṢÙ")
    print("                          ●")
    print()
    print("                     ÒPẸ̀LẸ̀")
    print()
    print("              Ọ̀TÚN            ÒSÌ")
    print()

    for right_mark, left_mark in zip(
        right_lines,
        left_lines,
    ):
        print(
            f"                "
            f"{right_mark:<16}"
            f"{left_mark}"
        )

    print()
    print(
        f"ODÙ    : "
        f"{right_name} {left_name}"
    )

    print(
        f"ÀMÌ    : "
        f"{right_value & 0x0F:04b} "
        f"{left_value & 0x0F:04b}"
    )

    print(
        f"ÀTỌ́KA : "
        f"{right_value & 0x0F}:"
        f"{left_value & 0x0F}"
    )

    print()


def opele() -> None:
    """
    Produce one complete ÒPẸ̀LẸ̀ cast.

    One command generates both four-line sides.
    """

    global LAST_OPELE_CAST

    right_value = random.randrange(16)
    left_value = random.randrange(16)

    LAST_OPELE_CAST = (
        right_value,
        left_value,
    )

    render_opele(
        right_value,
        left_value,
    )


def print_last_opele() -> None:
    """
    Display the most recent ÒPẸ̀LẸ̀ cast again.
    """

    if LAST_OPELE_CAST is None:
        print(
            "KÒ SÍ ÒPẸ̀LẸ̀ TÍ A TI DÁ."
        )
        return

    right_value, left_value = (
        LAST_OPELE_CAST
    )

    render_opele(
        right_value,
        left_value,
    )



#======================================================================
# TẸ IFÁ — Odù name and binary understanding service
#======================================================================

# Exact V3 PRINTODU mapping:
#
#     0000 = ÒGBÈ
#     1111 = ÒYÈKÚ
#
# TẸ IFÁ accepts either representation:
#
#     TEIFA 0000
#     TEIFA OGBE
#     TEIFA 0000 1111
#     TEIFA OGBE OYEKU
TEIFA_BIT_ODU_NAMES = {
    "0000": "ÒGBÈ",
    "0001": "ÒGÚNDÁ",
    "0010": "ÌRETẸ̀",
    "0011": "ÌRÒSÙN",
    "0100": "ÒTÚRÁ",
    "0101": "ÒṢÉ",
    "0110": "ÒDÍ",
    "0111": "ÒBÀRÀ",
    "1000": "ÒSÁ",
    "1001": "ÌWÒRÌ",
    "1010": "ÒFÚN",
    "1011": "ÌKÁ",
    "1100": "ÒWÓNRÍN",
    "1101": "ÒTÚRÚPỌ̀N",
    "1110": "ÒKÀNRÀN",
    "1111": "ÒYÈKÚ",
}


LAST_TEIFA_BITS: tuple[str, ...] | None = None


def normalize_teifa_token(
    value: str,
) -> str:
    """
    Remove Yorùbá accents for command and Odù-name matching.

    Examples:

        ÒGBÈ    -> OGBE
        ÒYÈKÚ   -> OYEKU
        ÌRÒSÙN  -> IROSUN
        TẸ      -> TE
        IFÁ     -> IFA
    """

    decomposed = unicodedata.normalize(
        "NFKD",
        value.strip().upper(),
    )

    return "".join(
        character
        for character in decomposed
        if (
            not unicodedata.combining(character)
            and character.isalnum()
        )
    )


# Reverse the exact binary-to-name table.
TEIFA_ODU_NAME_TO_BITS = {
    normalize_teifa_token(name): bits
    for bits, name in TEIFA_BIT_ODU_NAMES.items()
}


# Additional accepted unaccented/common spellings.
TEIFA_ODU_ALIASES = {
    "OGBE": "0000",
    "OGUNDA": "0001",
    "IRETE": "0010",
    "IROSUN": "0011",
    "OTURA": "0100",
    "OSE": "0101",
    "ODI": "0110",
    "OBARA": "0111",
    "OSA": "1000",
    "IWORI": "1001",
    "OFUN": "1010",
    "IKA": "1011",
    "OWONRIN": "1100",
    "OTURUPON": "1101",
    "OKANRAN": "1110",
    "OYEKU": "1111",
}


def resolve_teifa_value(
    value: str,
) -> str | None:
    """
    Resolve either an Odù name or one four-bit pattern.

    Examples:

        0000       -> 0000
        ÒGBÈ       -> 0000
        OGBE       -> 0000
        1111       -> 1111
        ÒYÈKÚ      -> 1111
    """

    cleaned = value.strip().replace(
        "_",
        "",
    )

    if re.fullmatch(
        r"[01]{4}",
        cleaned,
    ):
        return cleaned

    normalized = normalize_teifa_token(
        cleaned
    )

    if normalized in TEIFA_ODU_ALIASES:
        return TEIFA_ODU_ALIASES[
            normalized
        ]

    return TEIFA_ODU_NAME_TO_BITS.get(
        normalized
    )


def teifa_marks(
    bits: str,
) -> tuple[str, str, str, str]:
    """
    Convert one four-bit Odù into traditional marks.

        0 -> I
        1 -> II
    """

    return tuple(
        "I" if bit == "0" else "II"
        for bit in bits
    )


def render_single_teifa(
    bits: str,
) -> None:
    name = TEIFA_BIT_ODU_NAMES[
        bits
    ]

    marks = teifa_marks(
        bits
    )

    print()
    print("TẸ IFÁ")
    print("------")
    print()

    for mark in marks:
        print(
            f"             {mark}"
        )

    print()
    print(f"ODÙ : {name}")
    print(f"ÀMÌ : {bits}")
    print()


def render_pair_teifa(
    right_bits: str,
    left_bits: str,
) -> None:
    right_name = TEIFA_BIT_ODU_NAMES[
        right_bits
    ]

    left_name = TEIFA_BIT_ODU_NAMES[
        left_bits
    ]

    right_marks = teifa_marks(
        right_bits
    )

    left_marks = teifa_marks(
        left_bits
    )

    print()
    print("TẸ IFÁ")
    print("------")
    print()
    print("          Ọ̀TÚN          ÒSÌ")
    print()

    for right_mark, left_mark in zip(
        right_marks,
        left_marks,
    ):
        print(
            f"            "
            f"{right_mark:<14}"
            f"{left_mark}"
        )

    print()

    if right_bits == left_bits:
        print(
            f"ODÙ : {right_name} MÉJÌ"
        )
    else:
        print(
            f"ODÙ : "
            f"{right_name} {left_name}"
        )

    print(
        f"ÀMÌ : "
        f"{right_bits} {left_bits}"
    )

    print(
        f"Ọ̀TÚN: "
        f"{right_name} ({right_bits})"
    )

    print(
        f"ÒSÌ : "
        f"{left_name} ({left_bits})"
    )

    print()


def teifa_from_input(
    arguments: list[str],
) -> None:
    """
    Accepted forms:

        TEIFA 0000
        TEIFA OGBE

        TEIFA 1111
        TEIFA OYEKU

        TEIFA 0000 1111
        TEIFA OGBE OYEKU

        TEIFA 00001111
    """

    global LAST_TEIFA_BITS

    if len(arguments) == 1:
        compact = arguments[0].replace(
            "_",
            "",
        )

        # Compact eight-bit pair.
        if re.fullmatch(
            r"[01]{8}",
            compact,
        ):
            right_bits = compact[:4]
            left_bits = compact[4:]

            LAST_TEIFA_BITS = (
                right_bits,
                left_bits,
            )

            render_pair_teifa(
                right_bits,
                left_bits,
            )
            return

        # One four-bit pattern or one Odù name.
        resolved = resolve_teifa_value(
            arguments[0]
        )

        if resolved is not None:
            LAST_TEIFA_BITS = (
                resolved,
            )

            render_single_teifa(
                resolved
            )
            return

        print(
            f"KÒ MỌ ODÙ: "
            f"{arguments[0]}"
        )
        return

    if len(arguments) == 2:
        right_bits = resolve_teifa_value(
            arguments[0]
        )

        if right_bits is None:
            print(
                f"KÒ MỌ ODÙ: "
                f"{arguments[0]}"
            )
            return

        second_token = normalize_teifa_token(
            arguments[1]
        )

        # MÉJÌ means the same Odù appears on both sides.
        #
        # Examples:
        #
        #     TEIFA OYEKU MEJI
        #     TEIFA IROSUN MÉJÌ
        #     TẸ IFÁ ÒGBÈ MÉJÌ
        if second_token == "MEJI":
            left_bits = right_bits
        else:
            left_bits = resolve_teifa_value(
                arguments[1]
            )

            if left_bits is None:
                print(
                    f"KÒ MỌ ODÙ: "
                    f"{arguments[1]}"
                )
                return

        LAST_TEIFA_BITS = (
            right_bits,
            left_bits,
        )

        render_pair_teifa(
            right_bits,
            left_bits,
        )
        return

    print("Lo:")
    print("  TEIFA 0000")
    print("  TEIFA OGBE")
    print("  TEIFA 0000 1111")
    print("  TEIFA OGBE OYEKU")
    print("  TEIFA OYEKU MEJI")
    print("  TEIFA 00001111")


def print_last_teifa() -> None:
    if LAST_TEIFA_BITS is None:
        print(
            "KÒ SÍ ODÙ TẸ IFÁ "
            "TÍ A TI FI SÍLẸ̀."
        )
        return

    if len(LAST_TEIFA_BITS) == 1:
        render_single_teifa(
            LAST_TEIFA_BITS[0]
        )
        return

    render_pair_teifa(
        LAST_TEIFA_BITS[0],
        LAST_TEIFA_BITS[1],
    )


#======================================================================
# Wrapper help
#======================================================================

def print_v4_help() -> None:
    ORIGINAL_EXECUTE(
        "HELP"
    )

    print()
    print("OHÙN IFÁ 3.0 NATIVE SERVICES")
    print("----------------------------")

    print("OPELE")
    print("ÒPẸ̀LẸ̀")
    print(
        "    Perform one complete ÒPẸ̀LẸ̀ cast."
    )
    print(
        "    Both four-line sides are generated at once."
    )
    print()

    print("OPELE LAST")
    print(
        "    Display the most recent ÒPẸ̀LẸ̀ cast again."
    )
    print()

    print("TEIFA 0000")
    print(
        "    Read one four-bit Odù: "
        "0000 = ÒGBÈ."
    )
    print()

    print("TEIFA 1111")
    print(
        "    Read one four-bit Odù: "
        "1111 = ÒYÈKÚ."
    )
    print()

    print("TEIFA 0000 1111")
    print(
        "    Read two sides as the pair "
        "ÒGBÈ ÒYÈKÚ."
    )
    print()

    print("TEIFA 00001111")
    print(
        "    Compact eight-bit form "
        "of the same pair."
    )
    print()

    print("TEIFA LAST")
    print(
        "    Display the latest TẸ IFÁ "
        "reading again."
    )
    print()

#======================================================================
# RMU programmer service
#======================================================================

def current_rmu_yara() -> tuple[int, str]:
    yara_id = (
        int(v3.ACTIVE_YARA)
        if v3.ACTIVE_YARA is not None
        else 0
    )

    yara_name = v3.YARA_NAMES.get(
        yara_id,
        f"YARA{yara_id}",
    )

    return yara_id, yara_name


def handle_rmu_command(
    normalized_service: str,
) -> bool:
    if not normalized_service.startswith("RMU"):
        return False

    if not v3.BABALAWO_MODE:
        print(
            "DENY: RMU inspection requires "
            "BABALÁWO TAN."
        )
        return True

    yara_id, yara_name = current_rmu_yara()

    if normalized_service in {
        "RMU",
        "RMU STATS",
    }:
        RMU_VIEW.show_stats(
            yara_id,
            yara_name,
        )
        return True

    if normalized_service == "RMU LAST":
        RMU_VIEW.show_last(
            yara_id,
            yara_name,
        )
        return True

    if normalized_service in {
        "RMU LIST",
        "RMU ENTRIES",
        "RMU ALL",
    }:
        RMU_VIEW.show_entries(
            yara_id,
            yara_name,
        )
        return True

    if normalized_service == "RMU CLEAR":
        RMU_VIEW.clear(yara_id)

        print(
            f"RMU view cleared for "
            f"YÀRÁ {yara_name}."
        )
        return True

    if normalized_service == "RMU CLEAR ALL":
        RMU_VIEW.clear()

        print(
            "All RMU visualization records cleared."
        )
        return True

    print("Lo:")
    print("  RMU")
    print("  RMU STATS")
    print("  RMU LAST")
    print("  RMU LIST")
    print("  RMU CLEAR")
    print("  RMU CLEAR ALL")

    return True


#======================================================================
# Hardware-synchronised Babaláwo authentication
#======================================================================

def synced_babalawo_mode_command(
    command: str,
) -> None:
    """
    Run the existing PIN/Babaláwo command and mirror its resulting
    session state into the V4 RTL bridge.

    TAN:
        V3 BABALAWO_MODE = True
        RTL BABALAWO ON

    PA:
        V3 BABALAWO_MODE = False
        RTL BABALAWO OFF
    """

    previous_mode = bool(
        v3.BABALAWO_MODE
    )

    # Preserve the exact existing PIN and shell behaviour.
    ORIGINAL_EXECUTE(
        command
    )

    current_mode = bool(
        v3.BABALAWO_MODE
    )

    # The original command may reject PA in ONÍLẸ̀ or may otherwise
    # leave the authentication state unchanged.
    if current_mode == previous_mode:
        return

    bridge_command = (
        "BABALAWO ON"
        if current_mode
        else "BABALAWO OFF"
    )

    lines = V4.command(
        bridge_command,
        display=False,
    )

    if not bridge_has_error(lines):
        return

    # Hardware did not accept the mode transition. Restore the monitor
    # session so software and RTL cannot disagree.
    v3.BABALAWO_MODE = previous_mode

    show_bridge_failure(
        bridge_command,
        lines,
    )


#======================================================================
# Context-sensitive V4 help
#======================================================================

def print_general_context_help() -> None:
    print(
        """
═══════════════════════════════════════════════════════════════════════
                     OHÙN IFÁ — GENERAL HELP
═══════════════════════════════════════════════════════════════════════

CURRENT MODE
------------
OHÙN IFÁ is the general user shell.

Use this mode for:
• Direct mathematics
• IFÁ native services
• Authentication
• Entering ONÍLẸ̀
• Selecting a YÀRÁ
• Running script files


DIRECT MATHEMATICS
------------------
2+2
5-3

PAPO MEJI ATI META
YO MARUN ATI MEJI
DAGBA 7 ATI 6
PIN 20 ATI 4
KU 5 ATI 8
GBE 3 ATI 4
SEDA 0xA5 ATI 0x11

Operation meanings:
• PAPO   Add
• YO     Subtract
• DAGBA  Multiply
• PIN    Divide
• KU     AND/relation intersection
• GBE    OR/relation cover
• SEDA   Compare/create relation


IFÁ NATIVE SERVICES
-------------------
DAIFA
DÁIFÁ
PRINTODU
PRINTODUALL

OPELE
ÒPẸ̀LẸ̀
OPELE LAST

TEIFA 0000
TEIFA 0000 1111
TEIFA 00001111
TEIFA LAST


BABALÁWO AUTHENTICATION
-----------------------
BABALAWO
    Show the current BABALÁWO mode.

TAN
BABALAWO TAN
    Authenticate and enable the privileged session.

PA
BABALAWO PA
    Disable the privileged session.

Important:
ONÍLẸ̀ administration requires BABALÁWO TAN.


ENTER ONÍLẸ̀
------------
TAN
ONILE

ONÍLẸ̀ is the supervisor and administration mode.

Use ONÍLẸ̀ for:
• Creating and destroying YÀRÁ contexts
• Delegation permissions
• Sharing relation frames
• Supervisor status


ENTER A YÀRÁ
------------
YARA OGBE

The prompt changes to:

OHÙN IFÁ[OGBE]>

A YÀRÁ is an isolated execution context containing its own:
• Processor execution state
• Relation frames
• RMU records
• Program flow


SCRIPT EXECUTION
----------------
RUN file.ifa
RUN file.ifa3
BERE file.ifa3


GENERAL SYSTEM COMMANDS
-----------------------
HELP
HELP GENERAL
HELP ONILE
HELP YARA

VERSION
STATE
HISTORY
TIME
CLEAR
EXIT
QUIT


MODE MAP
--------
OHÙN IFÁ
    │
    ├── TAN
    │
    ├── ONILE
    │       └── ONÍLẸ̀ supervisor mode
    │
    └── YARA OGBE
            └── OHÙN IFÁ[OGBE] execution mode


IMPORTANT EXCLUSIVITY
---------------------
PIN has two meanings depending on the current mode:

OHÙN IFÁ> PIN 20 ATI 4
    Division.

ONÍLẸ̀> PIN OGBE IWORI
    Grant directional delegation permission.

The current prompt determines which language is active.
"""
    )


def print_onile_context_help() -> None:
    print(
        """
═══════════════════════════════════════════════════════════════════════
                   ONÍLẸ̀ — SUPERVISOR HELP
═══════════════════════════════════════════════════════════════════════

CURRENT MODE
------------
ONÍLẸ̀ is the privileged supervisor and administration mode.

Prompt:

ONÍLẸ̀>

Use this mode for:
• YÀRÁ lifecycle management
• Directional delegation permissions
• Relation-frame sharing
• Supervisor inspection


ENTERING ONÍLẸ̀
---------------
From the general OHÙN IFÁ prompt:

OHÙN IFÁ> TAN
OHÙN IFÁ> ONILE

BABALÁWO TAN must be active.


YÀRÁ LIFECYCLE
--------------
DA OGBE
    Create YÀRÁ OGBE.

DA IWORI
    Create YÀRÁ IWORI.

PARUN OGBE
    Request destruction of YÀRÁ OGBE.

PARUN OGBE TARA
    Force or confirm destruction when required.

YARA OGBE
    Select and enter YÀRÁ OGBE.

WO
    Show YÀRÁ and supervisor status.


DELEGATION PERMISSIONS
----------------------
PIN OGBE IWORI
    Grant directional permission:

        OGBE → IWORI

FAGILE OGBE IWORI
    Revoke directional permission:

        OGBE → IWORI

ASE
ÀṢẸ
    Show the current delegation permission table.

Permissions are directional.

PIN OGBE IWORI does not automatically grant:

    IWORI → OGBE


RELATION-FRAME SHARING
----------------------
SHARE OGBE IWORI

Meaning:
Import the current relation frame from OGBE into IWORI.

Required order:

1. Create both YÀRÁ contexts.
2. Execute an operation in the source YÀRÁ.
3. Return to ONÍLẸ̀.
4. Grant permission using PIN.
5. Share using SHARE.

Example:

ONÍLẸ̀> DA OGBE
ONÍLẸ̀> DA IWORI
ONÍLẸ̀> YARA OGBE

OHÙN IFÁ[OGBE]> YO 8 ATI 9
OHÙN IFÁ[OGBE]> DURO

OHÙN IFÁ> ONILE
ONÍLẸ̀> PIN OGBE IWORI
ONÍLẸ̀> SHARE OGBE IWORI
ONÍLẸ̀> YARA IWORI

OHÙN IFÁ[IWORI]> YO 8 ATI 9

The destination should be able to reuse the imported relation frame.


COMMANDS EXCLUSIVE TO ONÍLẸ̀
----------------------------
The following commands must be entered at the ONÍLẸ̀> prompt:

• DA
• PARUN
• WO
• PIN <source> <destination>
• FAGILE <source> <destination>
• SHARE <source> <destination>
• ASE

They are not YÀRÁ program instructions.


LEAVING ONÍLẸ̀
--------------
PADA
PADÀ

This returns to:

OHÙN IFÁ>


PIN WARNING
-----------
Inside ONÍLẸ̀:

PIN OGBE IWORI
    Grants delegation permission.

Inside a YÀRÁ:

PIN 20 ATI 4
    Performs division.

The prompt determines the meaning.


AVAILABLE HELP
--------------
HELP
    Show this ONÍLẸ̀ help page.

HELP GENERAL
    Show general-shell help.

HELP YARA
    Show YÀRÁ execution help.
"""
    )


def print_yara_context_help() -> None:
    print(
        """
═══════════════════════════════════════════════════════════════════════
                     YÀRÁ — EXECUTION HELP
═══════════════════════════════════════════════════════════════════════

CURRENT MODE
------------
You are inside an isolated YÀRÁ execution context.

Example prompt:

OHÙN IFÁ[OGBE]>

Commands entered here are interpreted as:
• Processor operations
• YÀRÁ program instructions
• Relation-frame operations
• RMU operations

They are not interpreted as ONÍLẸ̀ administration commands.


MATHEMATICAL OPERATIONS
-----------------------
PAPO 3 ATI 2
    Add.

YO 8 ATI 9
    Subtract.

DAGBA 7 ATI 6
    Multiply.

PIN 20 ATI 4
    Divide.

KU 5 ATI 8
    Relation intersection / AND.

GBE 3 ATI 4
    Relation cover / OR.

SEDA 13 ATI 6
    Compare/create a relation.


ODÙ AND PROCESSOR OPERATIONS
----------------------------
TE ODU

Processor output may include:

• OP
• A
• B
• Y
• FARAPỌ̀
• YÀTỌ̀
• ÌPÌLẸ̀
• GBÉ
• RMU
• VALID
• EXC
• STATE
• EQ
• GT
• LT


RMU INSPECTION
--------------
RMU
RMU LAST
RMU STATS
RMU LIST
RMU CLEAR

These inspect or manage the visible Relation Memory Unit records.


LEAVING THE YÀRÁ
----------------
DURO

This ends the current YÀRÁ execution session and returns to:

OHÙN IFÁ>


HOW TO SHARE FROM A YÀRÁ
------------------------
PIN, FAGILE, SHARE, and ASE delegation commands cannot be entered
directly at:

OHÙN IFÁ[OGBE]>

To share the current YÀRÁ relation frame:

1. Produce the relation frame:

   OHÙN IFÁ[OGBE]> YO 8 ATI 9

2. Leave the YÀRÁ:

   OHÙN IFÁ[OGBE]> DURO

3. Enter ONÍLẸ̀ again:

   OHÙN IFÁ> ONILE

4. Grant directional permission:

   ONÍLẸ̀> PIN OGBE IWORI

5. Share the frame:

   ONÍLẸ̀> SHARE OGBE IWORI


WHY PIN OGBE IWORI FAILS HERE
-----------------------------
At a YÀRÁ prompt, PIN is a processor arithmetic instruction.

Therefore:

OHÙN IFÁ[OGBE]> PIN OGBE IWORI

is sent to the YÀRÁ assembler as a division instruction and is invalid.

The delegation form belongs exclusively to ONÍLẸ̀:

ONÍLẸ̀> PIN OGBE IWORI


MODE BOUNDARIES
---------------
YÀRÁ execution:
• PAPO
• YO
• DAGBA
• PIN arithmetic
• KU
• GBE
• SEDA
• TE ODU
• RMU
• DURO

ONÍLẸ̀ administration:
• DA
• PARUN
• PIN delegation
• FAGILE
• SHARE
• ASE
• WO


AVAILABLE HELP
--------------
HELP
    Show this YÀRÁ help page.

HELP GENERAL
    Show general-shell help.

HELP ONILE
    Explain how to return to ONÍLẸ̀ and administer YÀRÁ contexts.
"""
    )


def print_context_sensitive_help(
    requested_context: str | None = None,
) -> None:
    """
    Display help for the requested context or for the currently active
    shell mode.

    Explicit requests:
        HELP GENERAL
        HELP OHUN
        HELP ONILE
        HELP YARA

    Context request aliases:
        ONILE HELP
        YARA HELP
    """

    requested = (
        requested_context.strip().upper()
        if requested_context
        else ""
    )

    if requested in {
        "GENERAL",
        "OHUN",
        "OHÙN",
        "SHELL",
    }:
        print_general_context_help()
        return

    if requested in {
        "ONILE",
        "ONÍLẸ̀",
        "SUPERVISOR",
        "ADMIN",
    }:
        print_onile_context_help()
        return

    if requested in {
        "YARA",
        "YÀRÁ",
        "ROOM",
        "EXECUTION",
    }:
        print_yara_context_help()
        return

    shell_mode = str(
        getattr(
            v3,
            "SHELL_MODE",
            "GENERAL",
        )
    ).upper()

    if shell_mode == "ONILE":
        print_onile_context_help()
        return

    if shell_mode in {
        "YARA",
        "YÀRÁ",
        "ODU",
        "EXECUTION",
    }:
        print_yara_context_help()
        return

    # Some monitor versions preserve a YÀRÁ identity separately from
    # SHELL_MODE. Detect the common forms without depending on one exact
    # variable name.
    active_yara = None

    for attribute_name in (
        "ACTIVE_YARA",
        "ACTIVE_YARA_ID",
        "CURRENT_YARA",
        "CURRENT_YARA_ID",
    ):
        if hasattr(v3, attribute_name):
            value = getattr(
                v3,
                attribute_name,
            )

            if value is not None:
                active_yara = value
                break

    # Only use this fallback when the shell mode itself identifies an
    # execution context. A selected YÀRÁ can remain known while the user
    # is back in GENERAL or ONÍLẸ̀.
    if shell_mode.startswith("YARA"):
        print_yara_context_help()
        return

    print_general_context_help()


#======================================================================
# V4-aware dispatcher
#======================================================================

def execute_v4(
    command: str,
) -> None:
    cleaned = command.strip()
    upper = cleaned.upper()

    if not cleaned:
        return

    command_parts = cleaned.split()

    normalized_parts = [
        normalize_teifa_token(part)
        for part in command_parts
    ]

    teifa_arguments = None

    # TEIFA 0000
    # TEIFA 0000 1111
    # TEIFA 00001111
    if (
        normalized_parts
        and normalized_parts[0] == "TEIFA"
    ):
        teifa_arguments = command_parts[1:]

    # TẸ IFÁ 0000
    # TẸ IFÁ 0000 1111
    elif (
        len(normalized_parts) >= 2
        and normalized_parts[0] == "TE"
        and normalized_parts[1] == "IFA"
    ):
        teifa_arguments = command_parts[2:]

    if teifa_arguments is not None:
        if (
            len(teifa_arguments) == 1
            and teifa_arguments[0].upper()
            in {
                "LAST",
                "AGAIN",
            }
        ):
            print_last_teifa()
            return

        teifa_from_input(
            teifa_arguments
        )
        return

    normalized_service = re.sub(
        r"\s+",
        " ",
        upper,
    )

    # The existing PIN system remains authoritative. We only mirror
    # the resulting authenticated session state into the RTL bridge.
    if normalized_service in {
        "TAN",
        "BABALAWO TAN",
        "BABALÁWO TAN",
        "PA",
        "BABALAWO PA",
        "BABALÁWO PA",
    }:
        synced_babalawo_mode_command(
            command
        )
        return

    # Context-sensitive help.
    #
    # HELP automatically describes the current interpreter.
    # Explicit forms can be used from any mode:
    #
    #     HELP GENERAL
    #     HELP ONILE
    #     HELP YARA
    #
    # Aliases:
    #
    #     ONILE HELP
    #     YARA HELP
    if normalized_service in {
        "HELP",
        "IRANLOWO",
        "ÌRÀNLỌ́WỌ́",
    }:
        print_context_sensitive_help()
        return

    if normalized_service in {
        "HELP GENERAL",
        "HELP OHUN",
        "HELP OHÙN",
        "GENERAL HELP",
        "OHUN HELP",
        "OHÙN HELP",
    }:
        print_context_sensitive_help(
            "GENERAL"
        )
        return

    if normalized_service in {
        "HELP ONILE",
        "HELP ONÍLẸ̀",
        "ONILE HELP",
        "ONÍLẸ̀ HELP",
    }:
        print_context_sensitive_help(
            "ONILE"
        )
        return

    if normalized_service in {
        "HELP YARA",
        "HELP YÀRÁ",
        "YARA HELP",
        "YÀRÁ HELP",
    }:
        print_context_sensitive_help(
            "YARA"
        )
        return

    if normalized_service in {
        "OPELE LAST",
        "ÒPẸLẸ LAST",
        "ÒPẸ̀LẸ̀ LAST",
        "OPELE AGAIN",
        "ÒPẸLẸ AGAIN",
        "ÒPẸ̀LẸ̀ AGAIN",
    }:
        print_last_opele()
        return

    if normalized_service in {
        "OPELE",
        "ÒPẸLẸ",
        "ÒPẸ̀LẸ̀",
        "OPELE IFA",
        "OPELE IFÁ",
        "ÒPẸLẸ IFA",
        "ÒPẸLẸ IFÁ",
        "ÒPẸ̀LẸ̀ IFA",
        "ÒPẸ̀LẸ̀ IFÁ",
    }:
        opele()
        return

    if handle_rmu_command(
        normalized_service
    ):
        return

    if normalized_service == "PRINTODU":
        printodu()
        return

    if normalized_service == "PRINTODUALL":
        printoduall()
        return

    if try_symbolic_expression(
        cleaned
    ):
        try:
            v3.add_history(
                cleaned
            )
        except Exception:
            pass

        return

    if try_native_words(
        cleaned
    ):
        try:
            v3.add_history(
                cleaned
            )
        except Exception:
            pass

        return

    # All other commands continue through the original V3 shell.
    ORIGINAL_EXECUTE(
        command
    )


#======================================================================
# Hardware-synchronised YÀRÁ lifecycle wrappers
#======================================================================

# Preserve the existing V3 lifecycle implementation.
ORIGINAL_CREATE_YARA = v3.onile_create_yara
ORIGINAL_DESTROY_YARA = v3.onile_destroy_yara
ORIGINAL_SELECT_YARA = v3.select_yara
ORIGINAL_PAUSE_YARA = v3.pause_active_yara
ORIGINAL_RESUME_YARA = v3.resume_yara

# Preserve the existing V3 delegation implementation.
ORIGINAL_GRANT_DELEGATION = v3.onile_grant_delegation
ORIGINAL_REVOKE_DELEGATION = v3.onile_revoke_delegation
ORIGINAL_SHARE_RELATION_FRAME = v3.onile_share_relation_frame

# V4Backend creates and selects YÀRÁ 0 during normal OS startup.
HARDWARE_YARA_CREATED: set[int] = {0}


def bridge_has_error(
    lines: list[str],
) -> bool:
    return any(
        line.startswith("ERROR")
        or line.startswith("DENY")
        for line in lines
    )


def show_bridge_failure(
    action: str,
    lines: list[str],
) -> None:
    print(
        f"V4 HARDWARE {action} FAILED"
    )

    for line in lines:
        if (
            line.startswith("ERROR")
            or line.startswith("DENY")
        ):
            print(line)


def synced_create_yara(
    name,
):
    """
    Create the monitor YÀRÁ and its real hardware context.

    YÀRÁ 0 already exists in hardware because it is the normal-shell
    execution context, so creating OGBE only registers it in ONÍLẸ̀.
    """

    yara_id = v3.resolve_yara_id(name)

    if yara_id is None:
        return ORIGINAL_CREATE_YARA(name)

    created = ORIGINAL_CREATE_YARA(name)

    if not created:
        return False

    if yara_id in HARDWARE_YARA_CREATED:
        return True

    lines = V4.command(
        f"CREATE {yara_id}",
        display=False,
    )

    if bridge_has_error(lines):
        # Roll back the monitor-side lifecycle state.
        state = v3.YARA_STATE[yara_id]

        state["valid"] = False
        state["running"] = False
        state["paused"] = False
        state["created_count"] = max(
            0,
            state["created_count"] - 1,
        )

        show_bridge_failure(
            "CREATE",
            lines,
        )

        return False

    HARDWARE_YARA_CREATED.add(yara_id)
    return True

def synced_select_yara(
    name,
):
    """
    Select the same YÀRÁ in both the monitor and RTL kernel.

    Selecting the hardware YÀRÁ that is already active is idempotent:
    the monitor enters that YÀRÁ without treating the bridge denial as
    a lifecycle failure.
    """

    yara_id = v3.resolve_yara_id(name)

    if yara_id is None:
        return ORIGINAL_SELECT_YARA(name)

    previous_active = v3.ACTIVE_YARA
    previous_mode = v3.SHELL_MODE

    selected = ORIGINAL_SELECT_YARA(name)

    if not selected:
        return False

    lines = V4.command(
        f"SELECT {yara_id}",
        display=False,
    )

    select_denied = any(
        line.strip() == f"DENY SELECT ID={yara_id}"
        for line in lines
    )

    other_error = any(
        (
            line.startswith("ERROR")
            or line.startswith("DENY")
        )
        and line.strip() != f"DENY SELECT ID={yara_id}"
        for line in lines
    )

    # The RTL may deny selecting a context that is already selected.
    # That is not a real failure: monitor and hardware already agree.
    if select_denied and not other_error:
        return True

    if other_error:
        v3.ACTIVE_YARA = previous_active
        v3.SHELL_MODE = previous_mode

        state = v3.YARA_STATE[yara_id]

        state["selected_count"] = max(
            0,
            state["selected_count"] - 1,
        )

        show_bridge_failure(
            "SELECT",
            lines,
        )

        return False

    return True


def synced_pause_active_yara():
    """
    Pause the active monitor context and the matching hardware context.
    """

    active_id = v3.ACTIVE_YARA

    if active_id is None:
        return ORIGINAL_PAUSE_YARA()

    paused = ORIGINAL_PAUSE_YARA()

    if not paused:
        return False

    lines = V4.command(
        f"PAUSE {active_id}",
        display=False,
    )

    if bridge_has_error(lines):
        # Restore monitor state if the hardware rejected the pause.
        state = v3.YARA_STATE[active_id]

        state["running"] = True
        state["paused"] = False
        state["pause_count"] = max(
            0,
            state["pause_count"] - 1,
        )

        v3.ACTIVE_YARA = active_id
        v3.SHELL_MODE = "YARA"

        show_bridge_failure(
            "PAUSE",
            lines,
        )

        return False

    return True


def synced_resume_yara(
    name,
):
    """
    Resume one YÀRÁ in both ONÍLẸ̀ and the RTL kernel.
    """

    yara_id = v3.resolve_yara_id(name)

    if yara_id is None:
        return ORIGINAL_RESUME_YARA(name)

    resumed = ORIGINAL_RESUME_YARA(name)

    if not resumed:
        return False

    lines = V4.command(
        f"RESUME {yara_id}",
        display=False,
    )

    if bridge_has_error(lines):
        state = v3.YARA_STATE[yara_id]

        state["running"] = False
        state["paused"] = True
        state["resume_count"] = max(
            0,
            state["resume_count"] - 1,
        )

        show_bridge_failure(
            "RESUME",
            lines,
        )

        return False

    return True


def synced_destroy_yara(
    name,
    force=False,
):
    """
    Destroy the monitor context and clear its hardware context, local
    RMU, permissions and wrapper-side RMU visualization.
    """

    yara_id = v3.resolve_yara_id(name)

    if yara_id is None:
        return ORIGINAL_DESTROY_YARA(
            name,
            force=force,
        )

    # Preserve the current state for rollback.
    previous_state = dict(
        v3.YARA_STATE[yara_id]
    )

    previous_active = v3.ACTIVE_YARA
    previous_mode = v3.SHELL_MODE

    destroyed = ORIGINAL_DESTROY_YARA(
        name,
        force=force,
    )

    if not destroyed:
        return False

    lines = V4.command(
        f"DESTROY {yara_id}",
        display=False,
    )

    if bridge_has_error(lines):
        v3.YARA_STATE[yara_id].update(
            previous_state
        )

        v3.ACTIVE_YARA = previous_active
        v3.SHELL_MODE = previous_mode

        show_bridge_failure(
            "DESTROY",
            lines,
        )

        return False

    HARDWARE_YARA_CREATED.discard(
        yara_id
    )

    RMU_VIEW.clear(
        yara_id
    )

    return True


# Install the wrappers into the original V3 monitor namespace.
#


#======================================================================
# Hardware-synchronised relation-frame delegation wrappers
#======================================================================

def snapshot_delegation_state():
    """
    Preserve all monitor state changed by grant, revoke, or share.

    This allows the monitor state to be restored if the RTL bridge
    rejects the corresponding hardware operation.
    """

    return {
        "yara_state": copy.deepcopy(
            v3.YARA_STATE
        ),
        "permissions": copy.deepcopy(
            v3.YARA_DELEGATION_PERMISSIONS
        ),
        "stats": copy.deepcopy(
            v3.DELEGATION_STATS
        ),
    }


def restore_delegation_state(
    snapshot,
) -> None:
    """
    Restore delegation-related V3 state in place.
    """

    v3.YARA_STATE.clear()
    v3.YARA_STATE.update(
        snapshot["yara_state"]
    )

    v3.YARA_DELEGATION_PERMISSIONS.clear()
    v3.YARA_DELEGATION_PERMISSIONS.update(
        snapshot["permissions"]
    )

    v3.DELEGATION_STATS.clear()
    v3.DELEGATION_STATS.update(
        snapshot["stats"]
    )


def run_v3_delegation_silently(
    function,
    source,
    destination,
):
    """
    Run one V3 delegation function while temporarily capturing output.

    A success message is displayed only after the RTL operation also
    succeeds.
    """

    output = io.StringIO()

    with redirect_stdout(output):
        result = function(
            source,
            destination,
        )

    return result, output.getvalue()


def run_hardware_delegation(
    action: str,
    source_id: int,
    destination_id: int,
) -> list[str]:
    """
    Execute a relation-frame delegation action in the RTL kernel.

    The bridge authentication state is already synchronized by the
    user's TAN/PA Babaláwo session. Individual delegation operations
    must not secretly enable or disable that session.
    """

    if action == "GRANT":
        return V4.grant(
            source_id,
            destination_id,
            display=False,
        )

    if action == "REVOKE":
        return V4.revoke(
            source_id,
            destination_id,
            display=False,
        )

    if action == "SHARE":
        return V4.share(
            source_id,
            destination_id,
            display=False,
        )

    return [
        f"ERROR UNKNOWN DELEGATION ACTION {action}"
    ]


def synced_grant_delegation(
    source,
    destination,
):
    """
    Grant the same directional delegation permission in V3 and RTL.
    """

    source_id = v3.resolve_yara_id(source)
    destination_id = v3.resolve_yara_id(destination)

    if (
        source_id is None
        or destination_id is None
    ):
        return ORIGINAL_GRANT_DELEGATION(
            source,
            destination,
        )

    snapshot = snapshot_delegation_state()

    granted, monitor_output = (
        run_v3_delegation_silently(
            ORIGINAL_GRANT_DELEGATION,
            source,
            destination,
        )
    )

    if not granted:
        print(
            monitor_output,
            end="",
        )
        return False

    lines = run_hardware_delegation(
        "GRANT",
        source_id,
        destination_id,
    )

    if bridge_has_error(lines):
        restore_delegation_state(
            snapshot
        )

        show_bridge_failure(
            "GRANT",
            lines,
        )

        return False

    print(
        monitor_output,
        end="",
    )

    return True


def synced_revoke_delegation(
    source,
    destination,
):
    """
    Revoke the same directional delegation permission in V3 and RTL.
    """

    source_id = v3.resolve_yara_id(source)
    destination_id = v3.resolve_yara_id(destination)

    if (
        source_id is None
        or destination_id is None
    ):
        return ORIGINAL_REVOKE_DELEGATION(
            source,
            destination,
        )

    snapshot = snapshot_delegation_state()

    revoked, monitor_output = (
        run_v3_delegation_silently(
            ORIGINAL_REVOKE_DELEGATION,
            source,
            destination,
        )
    )

    if not revoked:
        print(
            monitor_output,
            end="",
        )
        return False

    lines = run_hardware_delegation(
        "REVOKE",
        source_id,
        destination_id,
    )

    if bridge_has_error(lines):
        restore_delegation_state(
            snapshot
        )

        show_bridge_failure(
            "REVOKE",
            lines,
        )

        return False

    print(
        monitor_output,
        end="",
    )

    return True


def synced_share_relation_frame(
    source,
    destination,
):
    """
    Delegate the same relation frame through V3 and the real RTL RMU.

    The V3 copy preserves the visible monitor model. The RTL SHARE
    imports the source frame into the destination's independent local
    relation-memory unit.
    """

    source_id = v3.resolve_yara_id(source)
    destination_id = v3.resolve_yara_id(destination)

    if (
        source_id is None
        or destination_id is None
    ):
        return ORIGINAL_SHARE_RELATION_FRAME(
            source,
            destination,
        )

    snapshot = snapshot_delegation_state()

    shared, monitor_output = (
        run_v3_delegation_silently(
            ORIGINAL_SHARE_RELATION_FRAME,
            source,
            destination,
        )
    )

    if not shared:
        print(
            monitor_output,
            end="",
        )
        return False

    lines = run_hardware_delegation(
        "SHARE",
        source_id,
        destination_id,
    )

    if bridge_has_error(lines):
        restore_delegation_state(
            snapshot
        )

        show_bridge_failure(
            "SHARE",
            lines,
        )

        return False

    print(
        monitor_output,
        end="",
    )

    return True


# Its existing execute() dispatcher resolves these names from its module
# globals, so no existing ONÍLẸ̀ command parser needs to be rewritten.
v3.onile_create_yara = synced_create_yara
v3.onile_destroy_yara = synced_destroy_yara
v3.select_yara = synced_select_yara
v3.pause_active_yara = synced_pause_active_yara
v3.resume_yara = synced_resume_yara

v3.onile_grant_delegation = synced_grant_delegation
v3.onile_revoke_delegation = synced_revoke_delegation
v3.onile_share_relation_frame = synced_share_relation_frame


#======================================================================
# Replace only the V3 command dispatcher
#======================================================================

v3.execute = execute_v4


#======================================================================
# Main
#======================================================================

def main() -> None:
    try:
        v3.main()
    finally:
        V4.close()


if __name__ == "__main__":
    main()
