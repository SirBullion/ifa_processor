`timescale 1ns/1ps

module tb_top;

    logic [7:0] x;
    logic [7:0] error_e;

    logic [7:0] y;
    logic [7:0] delta;

    logic [5:0] xor_upper, and_upper, or_upper;
    logic [5:0] xor_lower, and_lower, or_lower;

    ifa_top dut (
        .x(x),
        .error_e(error_e),
        .y(y),
        .delta(delta),
        .xor_upper(xor_upper),
        .and_upper(and_upper),
        .or_upper(or_upper),
        .xor_lower(xor_lower),
        .and_lower(and_lower),
        .or_lower(or_lower)
    );

    initial begin
        $dumpfile("sim/top.vcd");
        $dumpvars(0, tb_top);

        $display("x        | y        | e        | delta    | XOR_U  AND_U  OR_U   | XOR_L  AND_L  OR_L");
        $display("------------------------------------------------------------------------------------------------");

        for (int i = 0; i < 16; i++) begin
            x = i[7:0];
            error_e = 8'b00000001 << (i % 8);
            #1;

            $display(
                "%08b | %08b | %08b | %08b | %06b %06b %06b | %06b %06b %06b",
                x, y, error_e, delta,
                xor_upper, and_upper, or_upper,
                xor_lower, and_lower, or_lower
            );
        end

        $finish;
    end

endmodule
