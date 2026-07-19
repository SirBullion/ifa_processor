#!/usr/bin/env python3
"""
Generate an exact synthesizable RTL implementation of the canonical
IFÁ Φ-P8 Python transform.

Canonical source:
    python.v5.ifa_phi_p8:phi_p8

Tuple packing convention:
    Python tuple (p0,p1,p2,p3,p4,p5,p6,p7)
             ↓
    SystemVerilog vector {p0,p1,p2,p3,p4,p5,p6,p7}

Therefore:
    tuple[0] -> phi_o[7]
    tuple[7] -> phi_o[0]

The generated RTL and verification vectors are both derived from the
same canonical Python function.
"""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path
from typing import Callable, Iterable, Sequence

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CANONICAL_MODULE = "python.v5.ifa_phi_p8"
CANONICAL_FUNCTION = "phi_p8"


def load_phi_p8() -> Callable[[int], Sequence[int]]:
    module = importlib.import_module(CANONICAL_MODULE)

    function = getattr(
        module,
        CANONICAL_FUNCTION,
        None,
    )

    if function is None or not callable(function):
        raise RuntimeError(
            f"{CANONICAL_MODULE}:{CANONICAL_FUNCTION} "
            "does not exist or is not callable."
        )

    return function


def validate_bits(value: int, transformed):
    """
    Canonical phi_p8() returns an integer (0..255).
    Convert it into both:
      - packed byte
      - tuple of bits (MSB first)
    """

    packed = int(transformed)

    if packed < 0 or packed > 255:
        raise ValueError(
            f"Φ-P8({value}) returned {packed}, expected 0..255."
        )

    bits = tuple(
        (packed >> shift) & 1
        for shift in range(7, -1, -1)
    )

    return bits, packed


def pack_msb_first(bits: Sequence[int]) -> int:
    packed = 0

    for bit in bits:
        packed = (packed << 1) | int(bit)

    return packed


def build_table(
    phi_p8: Callable[[int], Sequence[int]],
) -> list[tuple[int, tuple[int, ...], int]]:
    table: list[tuple[int, tuple[int, ...], int]] = []

    seen_outputs: dict[int, int] = {}

    for value in range(256):
        bits, packed = validate_bits(
            value,
            phi_p8(value),
)

        if packed in seen_outputs:
            previous = seen_outputs[packed]

            raise ValueError(
                "Canonical Φ-P8 is not injective: "
                f"{previous} and {value} both map to 0x{packed:02X}."
            )

        seen_outputs[packed] = value

        table.append(
            (
                value,
                bits,
                packed,
            )
        )

    if len(seen_outputs) != 256:
        raise ValueError(
            f"Expected 256 unique Φ-P8 outputs; got {len(seen_outputs)}."
        )

    return table


def render_rtl(
    table: list[tuple[int, tuple[int, ...], int]],
) -> str:
    case_lines = []

    for value, bits, packed in table:
        tuple_text = "".join(str(bit) for bit in bits)

        case_lines.append(
            f"            8'h{value:02X}: "
            f"phi_o = 8'h{packed:02X}; "
            f"// ({tuple_text})"
        )

    cases = "\n".join(case_lines)

    return f"""`timescale 1ns/1ps

// ============================================================================
// IFÁ Processor V4.5
// Exact Φ-P8 Transform
// ============================================================================
//
// AUTO-GENERATED FILE. DO NOT EDIT BY HAND.
//
// Canonical source:
//     {CANONICAL_MODULE}:{CANONICAL_FUNCTION}
//
// Packing:
//     Python (p0,p1,p2,p3,p4,p5,p6,p7)
//       -> SystemVerilog {{p0,p1,p2,p3,p4,p5,p6,p7}}
//
// Exhaustive domain:
//     0x00 through 0xFF
//
// This is a pure combinational, synthesizable transform.
// ============================================================================

module ifa_phi_p8 (
    input  logic [7:0] binary_i,
    output logic [7:0] phi_o
);

    always_comb begin
        unique case (binary_i)
{cases}
            default: phi_o = 8'h00;
        endcase
    end

endmodule
"""


def render_testbench(
    table: list[tuple[int, tuple[int, ...], int]],
) -> str:
    checks = []

    for value, _, packed in table:
        checks.append(
            f"""        check_transform(
            8'h{value:02X},
            8'h{packed:02X}
        );"""
        )

    check_text = "\n\n".join(checks)

    return f"""`timescale 1ns/1ps

module tb_ifa_phi_p8;

    logic [7:0] binary_i;
    logic [7:0] phi_o;

    logic [255:0] seen_outputs;

    int tests_run;
    int tests_failed;

    ifa_phi_p8 dut (
        .binary_i (binary_i),
        .phi_o    (phi_o)
    );

    task automatic check_transform(
        input logic [7:0] binary_value,
        input logic [7:0] expected_phi
    );
        begin
            binary_i = binary_value;
            #1;

            tests_run++;

            if (phi_o !== expected_phi) begin
                tests_failed++;

                $display(
                    "FAIL: Φ-P8(0x%02h) actual=0x%02h expected=0x%02h",
                    binary_value,
                    phi_o,
                    expected_phi
                );
            end
            else begin
                $display(
                    "PASS: Φ-P8(0x%02h) = 0x%02h",
                    binary_value,
                    phi_o
                );
            end

            if (seen_outputs[phi_o] === 1'b1) begin
                tests_failed++;

                $display(
                    "FAIL: duplicate Φ-P8 output 0x%02h "
                    "encountered at input 0x%02h",
                    phi_o,
                    binary_value
                );
            end

            seen_outputs[phi_o] = 1'b1;
        end
    endtask

    initial begin
        $dumpfile("sim_v45/ifa_phi_p8.vcd");
        $dumpvars(0, tb_ifa_phi_p8);

        binary_i     = 8'h00;
        seen_outputs = '0;

        tests_run    = 0;
        tests_failed = 0;

{check_text}

        if (seen_outputs !== {{256{{1'b1}}}}) begin
            tests_failed++;

            $display(
                "FAIL: Φ-P8 output space is not a complete "
                "256-element permutation."
            );
        end
        else begin
            $display(
                "PASS: all 256 Φ-P8 outputs are unique."
            );
        end

        $display("");
        $display("============================================================");
        $display("IFÁ V4.5 EXACT Φ-P8 RTL TEST SUMMARY");
        $display("============================================================");
        $display("Canonical backend : {CANONICAL_MODULE}:{CANONICAL_FUNCTION}");
        $display("Inputs tested      : %0d", tests_run);
        $display("Tests failed       : %0d", tests_failed);

        if (tests_failed == 0) begin
            $display("RESULT             : PASS");
            $display(
                "RTL Φ-P8 is bit-for-bit identical to Python "
                "for all 256 inputs."
            );
        end
        else begin
            $display("RESULT             : FAIL");

            $fatal(
                1,
                "%0d Φ-P8 verification checks failed.",
                tests_failed
            );
        end

        $finish;
    end

endmodule
"""


def render_vectors(
    table: list[tuple[int, tuple[int, ...], int]],
) -> str:
    lines = [
        "# IFÁ V4.5 Φ-P8 golden vectors",
        "# input_hex output_hex tuple_bits",
    ]

    for value, bits, packed in table:
        tuple_text = "".join(str(bit) for bit in bits)

        lines.append(
            f"{value:02X} {packed:02X} {tuple_text}"
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--rtl",
        default="rtl/v45/ifa_phi_p8.sv",
    )

    parser.add_argument(
        "--testbench",
        default="tb/v45/tb_ifa_phi_p8.sv",
    )

    parser.add_argument(
        "--vectors",
        default="generated/v45/phi_p8_vectors.txt",
    )

    arguments = parser.parse_args()

    phi_p8 = load_phi_p8()
    table = build_table(phi_p8)

    rtl_path = Path(arguments.rtl)
    testbench_path = Path(arguments.testbench)
    vectors_path = Path(arguments.vectors)

    rtl_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    testbench_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    vectors_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    rtl_path.write_text(
        render_rtl(table),
        encoding="utf-8",
    )

    testbench_path.write_text(
        render_testbench(table),
        encoding="utf-8",
    )

    vectors_path.write_text(
        render_vectors(table),
        encoding="utf-8",
    )

    print("=" * 72)
    print("IFÁ V4.5 EXACT Φ-P8 RTL GENERATOR")
    print("=" * 72)
    print(
        f"Canonical backend : "
        f"{CANONICAL_MODULE}:{CANONICAL_FUNCTION}"
    )
    print(f"Entries generated : {len(table)}")
    print(f"Unique outputs    : {len({row[2] for row in table})}")
    print(f"RTL module        : {rtl_path}")
    print(f"Testbench         : {testbench_path}")
    print(f"Golden vectors    : {vectors_path}")
    print()
    print("Packing:")
    print("  tuple[0] -> phi_o[7]")
    print("  tuple[7] -> phi_o[0]")


if __name__ == "__main__":
    main()
