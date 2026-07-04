`timescale 1ns/1ps

module tb_p8;

    logic [7:0] x;
    logic [7:0] y;

    ifa_p8 dut (.x(x), .y(y));

    initial begin
        $dumpfile("sim/p8.vcd");
        $dumpvars(0, tb_p8);

        $display("Input     -> Output");
        $display("-------------------");

        for (int i = 0; i < 256; i++) begin
            x = i[7:0];
            #1;
            $display("%08b -> %08b", x, y);
        end

        $finish;
    end

endmodule
