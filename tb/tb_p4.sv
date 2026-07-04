`timescale 1ns/1ps

module tb_p4;

    logic [3:0] x;
    logic [3:0] y;

    ifa_p4 dut (
        .x(x),
        .y(y)
    );

    initial begin
        $dumpfile("sim/p4.vcd");
        $dumpvars(0, tb_p4);

        $display(" x    |  y");
        $display("-------------");

        for (int i = 0; i < 16; i++) begin
            x = i[3:0];
            #1;
            $display("%04b | %04b", x, y);
        end

        $finish;
    end

endmodule
