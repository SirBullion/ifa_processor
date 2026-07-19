`timescale 1ns/1ps

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
                    "FAIL: duplicate Φ-P8 output 0x%02h encountered at input 0x%02h",
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

        check_transform(
            8'h00,
            8'h55
        );

        check_transform(
            8'h01,
            8'h54
        );

        check_transform(
            8'h02,
            8'h56
        );

        check_transform(
            8'h03,
            8'h57
        );

        check_transform(
            8'h04,
            8'h51
        );

        check_transform(
            8'h05,
            8'h50
        );

        check_transform(
            8'h06,
            8'h52
        );

        check_transform(
            8'h07,
            8'h53
        );

        check_transform(
            8'h08,
            8'h59
        );

        check_transform(
            8'h09,
            8'h58
        );

        check_transform(
            8'h0A,
            8'h5A
        );

        check_transform(
            8'h0B,
            8'h5B
        );

        check_transform(
            8'h0C,
            8'h5D
        );

        check_transform(
            8'h0D,
            8'h5C
        );

        check_transform(
            8'h0E,
            8'h5E
        );

        check_transform(
            8'h0F,
            8'h5F
        );

        check_transform(
            8'h10,
            8'h45
        );

        check_transform(
            8'h11,
            8'h44
        );

        check_transform(
            8'h12,
            8'h46
        );

        check_transform(
            8'h13,
            8'h47
        );

        check_transform(
            8'h14,
            8'h41
        );

        check_transform(
            8'h15,
            8'h40
        );

        check_transform(
            8'h16,
            8'h42
        );

        check_transform(
            8'h17,
            8'h43
        );

        check_transform(
            8'h18,
            8'h49
        );

        check_transform(
            8'h19,
            8'h48
        );

        check_transform(
            8'h1A,
            8'h4A
        );

        check_transform(
            8'h1B,
            8'h4B
        );

        check_transform(
            8'h1C,
            8'h4D
        );

        check_transform(
            8'h1D,
            8'h4C
        );

        check_transform(
            8'h1E,
            8'h4E
        );

        check_transform(
            8'h1F,
            8'h4F
        );

        check_transform(
            8'h20,
            8'h65
        );

        check_transform(
            8'h21,
            8'h64
        );

        check_transform(
            8'h22,
            8'h66
        );

        check_transform(
            8'h23,
            8'h67
        );

        check_transform(
            8'h24,
            8'h61
        );

        check_transform(
            8'h25,
            8'h60
        );

        check_transform(
            8'h26,
            8'h62
        );

        check_transform(
            8'h27,
            8'h63
        );

        check_transform(
            8'h28,
            8'h69
        );

        check_transform(
            8'h29,
            8'h68
        );

        check_transform(
            8'h2A,
            8'h6A
        );

        check_transform(
            8'h2B,
            8'h6B
        );

        check_transform(
            8'h2C,
            8'h6D
        );

        check_transform(
            8'h2D,
            8'h6C
        );

        check_transform(
            8'h2E,
            8'h6E
        );

        check_transform(
            8'h2F,
            8'h6F
        );

        check_transform(
            8'h30,
            8'h75
        );

        check_transform(
            8'h31,
            8'h74
        );

        check_transform(
            8'h32,
            8'h76
        );

        check_transform(
            8'h33,
            8'h77
        );

        check_transform(
            8'h34,
            8'h71
        );

        check_transform(
            8'h35,
            8'h70
        );

        check_transform(
            8'h36,
            8'h72
        );

        check_transform(
            8'h37,
            8'h73
        );

        check_transform(
            8'h38,
            8'h79
        );

        check_transform(
            8'h39,
            8'h78
        );

        check_transform(
            8'h3A,
            8'h7A
        );

        check_transform(
            8'h3B,
            8'h7B
        );

        check_transform(
            8'h3C,
            8'h7D
        );

        check_transform(
            8'h3D,
            8'h7C
        );

        check_transform(
            8'h3E,
            8'h7E
        );

        check_transform(
            8'h3F,
            8'h7F
        );

        check_transform(
            8'h40,
            8'h15
        );

        check_transform(
            8'h41,
            8'h14
        );

        check_transform(
            8'h42,
            8'h16
        );

        check_transform(
            8'h43,
            8'h17
        );

        check_transform(
            8'h44,
            8'h11
        );

        check_transform(
            8'h45,
            8'h10
        );

        check_transform(
            8'h46,
            8'h12
        );

        check_transform(
            8'h47,
            8'h13
        );

        check_transform(
            8'h48,
            8'h19
        );

        check_transform(
            8'h49,
            8'h18
        );

        check_transform(
            8'h4A,
            8'h1A
        );

        check_transform(
            8'h4B,
            8'h1B
        );

        check_transform(
            8'h4C,
            8'h1D
        );

        check_transform(
            8'h4D,
            8'h1C
        );

        check_transform(
            8'h4E,
            8'h1E
        );

        check_transform(
            8'h4F,
            8'h1F
        );

        check_transform(
            8'h50,
            8'h05
        );

        check_transform(
            8'h51,
            8'h04
        );

        check_transform(
            8'h52,
            8'h06
        );

        check_transform(
            8'h53,
            8'h07
        );

        check_transform(
            8'h54,
            8'h01
        );

        check_transform(
            8'h55,
            8'h00
        );

        check_transform(
            8'h56,
            8'h02
        );

        check_transform(
            8'h57,
            8'h03
        );

        check_transform(
            8'h58,
            8'h09
        );

        check_transform(
            8'h59,
            8'h08
        );

        check_transform(
            8'h5A,
            8'h0A
        );

        check_transform(
            8'h5B,
            8'h0B
        );

        check_transform(
            8'h5C,
            8'h0D
        );

        check_transform(
            8'h5D,
            8'h0C
        );

        check_transform(
            8'h5E,
            8'h0E
        );

        check_transform(
            8'h5F,
            8'h0F
        );

        check_transform(
            8'h60,
            8'h25
        );

        check_transform(
            8'h61,
            8'h24
        );

        check_transform(
            8'h62,
            8'h26
        );

        check_transform(
            8'h63,
            8'h27
        );

        check_transform(
            8'h64,
            8'h21
        );

        check_transform(
            8'h65,
            8'h20
        );

        check_transform(
            8'h66,
            8'h22
        );

        check_transform(
            8'h67,
            8'h23
        );

        check_transform(
            8'h68,
            8'h29
        );

        check_transform(
            8'h69,
            8'h28
        );

        check_transform(
            8'h6A,
            8'h2A
        );

        check_transform(
            8'h6B,
            8'h2B
        );

        check_transform(
            8'h6C,
            8'h2D
        );

        check_transform(
            8'h6D,
            8'h2C
        );

        check_transform(
            8'h6E,
            8'h2E
        );

        check_transform(
            8'h6F,
            8'h2F
        );

        check_transform(
            8'h70,
            8'h35
        );

        check_transform(
            8'h71,
            8'h34
        );

        check_transform(
            8'h72,
            8'h36
        );

        check_transform(
            8'h73,
            8'h37
        );

        check_transform(
            8'h74,
            8'h31
        );

        check_transform(
            8'h75,
            8'h30
        );

        check_transform(
            8'h76,
            8'h32
        );

        check_transform(
            8'h77,
            8'h33
        );

        check_transform(
            8'h78,
            8'h39
        );

        check_transform(
            8'h79,
            8'h38
        );

        check_transform(
            8'h7A,
            8'h3A
        );

        check_transform(
            8'h7B,
            8'h3B
        );

        check_transform(
            8'h7C,
            8'h3D
        );

        check_transform(
            8'h7D,
            8'h3C
        );

        check_transform(
            8'h7E,
            8'h3E
        );

        check_transform(
            8'h7F,
            8'h3F
        );

        check_transform(
            8'h80,
            8'h95
        );

        check_transform(
            8'h81,
            8'h94
        );

        check_transform(
            8'h82,
            8'h96
        );

        check_transform(
            8'h83,
            8'h97
        );

        check_transform(
            8'h84,
            8'h91
        );

        check_transform(
            8'h85,
            8'h90
        );

        check_transform(
            8'h86,
            8'h92
        );

        check_transform(
            8'h87,
            8'h93
        );

        check_transform(
            8'h88,
            8'h99
        );

        check_transform(
            8'h89,
            8'h98
        );

        check_transform(
            8'h8A,
            8'h9A
        );

        check_transform(
            8'h8B,
            8'h9B
        );

        check_transform(
            8'h8C,
            8'h9D
        );

        check_transform(
            8'h8D,
            8'h9C
        );

        check_transform(
            8'h8E,
            8'h9E
        );

        check_transform(
            8'h8F,
            8'h9F
        );

        check_transform(
            8'h90,
            8'h85
        );

        check_transform(
            8'h91,
            8'h84
        );

        check_transform(
            8'h92,
            8'h86
        );

        check_transform(
            8'h93,
            8'h87
        );

        check_transform(
            8'h94,
            8'h81
        );

        check_transform(
            8'h95,
            8'h80
        );

        check_transform(
            8'h96,
            8'h82
        );

        check_transform(
            8'h97,
            8'h83
        );

        check_transform(
            8'h98,
            8'h89
        );

        check_transform(
            8'h99,
            8'h88
        );

        check_transform(
            8'h9A,
            8'h8A
        );

        check_transform(
            8'h9B,
            8'h8B
        );

        check_transform(
            8'h9C,
            8'h8D
        );

        check_transform(
            8'h9D,
            8'h8C
        );

        check_transform(
            8'h9E,
            8'h8E
        );

        check_transform(
            8'h9F,
            8'h8F
        );

        check_transform(
            8'hA0,
            8'hA5
        );

        check_transform(
            8'hA1,
            8'hA4
        );

        check_transform(
            8'hA2,
            8'hA6
        );

        check_transform(
            8'hA3,
            8'hA7
        );

        check_transform(
            8'hA4,
            8'hA1
        );

        check_transform(
            8'hA5,
            8'hA0
        );

        check_transform(
            8'hA6,
            8'hA2
        );

        check_transform(
            8'hA7,
            8'hA3
        );

        check_transform(
            8'hA8,
            8'hA9
        );

        check_transform(
            8'hA9,
            8'hA8
        );

        check_transform(
            8'hAA,
            8'hAA
        );

        check_transform(
            8'hAB,
            8'hAB
        );

        check_transform(
            8'hAC,
            8'hAD
        );

        check_transform(
            8'hAD,
            8'hAC
        );

        check_transform(
            8'hAE,
            8'hAE
        );

        check_transform(
            8'hAF,
            8'hAF
        );

        check_transform(
            8'hB0,
            8'hB5
        );

        check_transform(
            8'hB1,
            8'hB4
        );

        check_transform(
            8'hB2,
            8'hB6
        );

        check_transform(
            8'hB3,
            8'hB7
        );

        check_transform(
            8'hB4,
            8'hB1
        );

        check_transform(
            8'hB5,
            8'hB0
        );

        check_transform(
            8'hB6,
            8'hB2
        );

        check_transform(
            8'hB7,
            8'hB3
        );

        check_transform(
            8'hB8,
            8'hB9
        );

        check_transform(
            8'hB9,
            8'hB8
        );

        check_transform(
            8'hBA,
            8'hBA
        );

        check_transform(
            8'hBB,
            8'hBB
        );

        check_transform(
            8'hBC,
            8'hBD
        );

        check_transform(
            8'hBD,
            8'hBC
        );

        check_transform(
            8'hBE,
            8'hBE
        );

        check_transform(
            8'hBF,
            8'hBF
        );

        check_transform(
            8'hC0,
            8'hD5
        );

        check_transform(
            8'hC1,
            8'hD4
        );

        check_transform(
            8'hC2,
            8'hD6
        );

        check_transform(
            8'hC3,
            8'hD7
        );

        check_transform(
            8'hC4,
            8'hD1
        );

        check_transform(
            8'hC5,
            8'hD0
        );

        check_transform(
            8'hC6,
            8'hD2
        );

        check_transform(
            8'hC7,
            8'hD3
        );

        check_transform(
            8'hC8,
            8'hD9
        );

        check_transform(
            8'hC9,
            8'hD8
        );

        check_transform(
            8'hCA,
            8'hDA
        );

        check_transform(
            8'hCB,
            8'hDB
        );

        check_transform(
            8'hCC,
            8'hDD
        );

        check_transform(
            8'hCD,
            8'hDC
        );

        check_transform(
            8'hCE,
            8'hDE
        );

        check_transform(
            8'hCF,
            8'hDF
        );

        check_transform(
            8'hD0,
            8'hC5
        );

        check_transform(
            8'hD1,
            8'hC4
        );

        check_transform(
            8'hD2,
            8'hC6
        );

        check_transform(
            8'hD3,
            8'hC7
        );

        check_transform(
            8'hD4,
            8'hC1
        );

        check_transform(
            8'hD5,
            8'hC0
        );

        check_transform(
            8'hD6,
            8'hC2
        );

        check_transform(
            8'hD7,
            8'hC3
        );

        check_transform(
            8'hD8,
            8'hC9
        );

        check_transform(
            8'hD9,
            8'hC8
        );

        check_transform(
            8'hDA,
            8'hCA
        );

        check_transform(
            8'hDB,
            8'hCB
        );

        check_transform(
            8'hDC,
            8'hCD
        );

        check_transform(
            8'hDD,
            8'hCC
        );

        check_transform(
            8'hDE,
            8'hCE
        );

        check_transform(
            8'hDF,
            8'hCF
        );

        check_transform(
            8'hE0,
            8'hE5
        );

        check_transform(
            8'hE1,
            8'hE4
        );

        check_transform(
            8'hE2,
            8'hE6
        );

        check_transform(
            8'hE3,
            8'hE7
        );

        check_transform(
            8'hE4,
            8'hE1
        );

        check_transform(
            8'hE5,
            8'hE0
        );

        check_transform(
            8'hE6,
            8'hE2
        );

        check_transform(
            8'hE7,
            8'hE3
        );

        check_transform(
            8'hE8,
            8'hE9
        );

        check_transform(
            8'hE9,
            8'hE8
        );

        check_transform(
            8'hEA,
            8'hEA
        );

        check_transform(
            8'hEB,
            8'hEB
        );

        check_transform(
            8'hEC,
            8'hED
        );

        check_transform(
            8'hED,
            8'hEC
        );

        check_transform(
            8'hEE,
            8'hEE
        );

        check_transform(
            8'hEF,
            8'hEF
        );

        check_transform(
            8'hF0,
            8'hF5
        );

        check_transform(
            8'hF1,
            8'hF4
        );

        check_transform(
            8'hF2,
            8'hF6
        );

        check_transform(
            8'hF3,
            8'hF7
        );

        check_transform(
            8'hF4,
            8'hF1
        );

        check_transform(
            8'hF5,
            8'hF0
        );

        check_transform(
            8'hF6,
            8'hF2
        );

        check_transform(
            8'hF7,
            8'hF3
        );

        check_transform(
            8'hF8,
            8'hF9
        );

        check_transform(
            8'hF9,
            8'hF8
        );

        check_transform(
            8'hFA,
            8'hFA
        );

        check_transform(
            8'hFB,
            8'hFB
        );

        check_transform(
            8'hFC,
            8'hFD
        );

        check_transform(
            8'hFD,
            8'hFC
        );

        check_transform(
            8'hFE,
            8'hFE
        );

        check_transform(
            8'hFF,
            8'hFF
        );

        if (seen_outputs !== {256{1'b1}}) begin
            tests_failed++;

            $display(
                "FAIL: Φ-P8 output space is not a complete 256-element permutation."
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
        $display("Canonical backend : python.v5.ifa_phi_p8:phi_p8");
        $display("Inputs tested      : %0d", tests_run);
        $display("Tests failed       : %0d", tests_failed);

        if (tests_failed == 0) begin
            $display("RESULT             : PASS");
            $display(
                "RTL Φ-P8 is bit-for-bit identical to Python for all 256 inputs."
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
