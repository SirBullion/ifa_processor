`timescale 1ns/1ps

module tb_t8;

    logic [7:0] e;
    logic [7:0] delta;
    logic [7:0] recovered_e;

    ifa_t8 dut1 (
        .e(e),
        .delta(delta)
    );

    // T^2 = I check
    ifa_t8 dut2 (
        .e(delta),
        .delta(recovered_e)
    );

    initial begin
        $dumpfile("sim/t8.vcd");
        $dumpvars(0, tb_t8);

        $display(" e        -> delta    -> T(delta)");
        $display("-----------------------------------");

        for (int i = 0; i < 256; i++) begin
            e = i[7:0];
            #1;

            $display("%08b -> %08b -> %08b", e, delta, recovered_e);

            if (recovered_e !== e) begin
                $display("ERROR: T^2 failed at e=%08b", e);
                $finish;
            end
        end

        $display("-----------------------------------");
        $display("T8 verified for all 256 states.");
        $display("T^2 = I confirmed.");
        $finish;
    end

endmodule
