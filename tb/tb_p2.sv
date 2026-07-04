`timescale 1ns/1ps

module tb_p2;

    logic A, B;
    logic A_out, B_out;

    ifa_p2 dut (
        .A(A),
        .B(B),
        .A_out(A_out),
        .B_out(B_out)
    );

    initial begin
        $dumpfile("sim/p2.vcd");
        $dumpvars(0, tb_p2);

        $display("A B | A_out B_out");
        $display("----------------");

        for (int i = 0; i < 4; i++) begin
            {A, B} = i[1:0];
            #1;
            $display("%0b %0b |   %0b     %0b", A, B, A_out, B_out);
        end

        $finish;
    end

endmodule
