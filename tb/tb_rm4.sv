`timescale 1ns/1ps

module tb_rm4;

    logic [3:0] x;

    logic [1:0] AB, AC, AD, BC, BD, CD;
    logic [5:0] xor_feature;
    logic [5:0] and_feature;
    logic [5:0] or_feature;

    ifa_rm4 dut (
        .x(x),
        .AB(AB),
        .AC(AC),
        .AD(AD),
        .BC(BC),
        .BD(BD),
        .CD(CD),
        .xor_feature(xor_feature),
        .and_feature(and_feature),
        .or_feature(or_feature)
    );

    initial begin
        $dumpfile("sim/rm4.vcd");
        $dumpvars(0, tb_rm4);

        $display(" x   | AB AC AD BC BD CD | XOR    AND    OR");
        $display("------------------------------------------------");

        for (int i = 0; i < 16; i++) begin
            x = i[3:0];
            #1;

            $display(
                "%04b | %02b %02b %02b %02b %02b %02b | %06b %06b %06b",
                x, AB, AC, AD, BC, BD, CD,
                xor_feature, and_feature, or_feature
            );
        end

        $finish;
    end

endmodule
