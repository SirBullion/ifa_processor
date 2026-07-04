`timescale 1ns/1ps

module tb_recovery;

    logic [7:0] x;
    logic [7:0] y;
    logic [7:0] recovered;

    int failures = 0;

    ifa_p8 enc (
        .x(x),
        .y(y)
    );

    ifa_p8_inv dec (
        .y(y),
        .x(recovered)
    );

    initial begin
        $dumpfile("sim/recovery.vcd");
        $dumpvars(0, tb_recovery);

        $display("x        -> y        -> recovered");
        $display("----------------------------------");

        for (int i = 0; i < 256; i++) begin
            x = i[7:0];
            #1;

            $display("%08b -> %08b -> %08b", x, y, recovered);

            if (recovered !== x) begin
                failures++;
                $display("FAIL at x=%08b", x);
            end
        end

        $display("----------------------------------");
        $display("Recovery failures = %0d", failures);

        if (failures == 0)
            $display("PASS: P^-1(P(x)) = x for all 256 states.");
        else
            $display("FAIL: recovery mismatch detected.");

        $finish;
    end

endmodule
