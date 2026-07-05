`timescale 1ns/1ps

module tb_ifa_pipelined_core;

    logic clk;
    logic rst_n;
    logic start;

    logic [3:0] A_in;
    logic [3:0] B_in;

    logic [3:0] Y_out;
    logic [3:0] R_primary_out;
    logic [3:0] R_secondary_out;
    logic [1:0] mode_out;
    logic [3:0] relation_feedback;

    ifa_pipelined_core dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),

        .A_in(A_in),
        .B_in(B_in),

        .Y_out(Y_out),
        .R_primary_out(R_primary_out),
        .R_secondary_out(R_secondary_out),
        .mode_out(mode_out),
        .relation_feedback(relation_feedback)
    );

    always #5 clk = ~clk;

    initial begin
        $dumpfile("sim_v2/ifa_pipelined_core.vcd");
        $dumpvars(0, tb_ifa_pipelined_core);

        clk = 0;
        rst_n = 0;
        start = 0;

        A_in = 4'hD;
        B_in = 4'h6;

        #12;
        rst_n = 1;

        repeat (12) begin
            #10;
            start = 1;
            #10;
            start = 0;

            $display(
                "Y=%h R_primary=%h R_secondary=%h mode=%b feedback=%h",
                Y_out,
                R_primary_out,
                R_secondary_out,
                mode_out,
                relation_feedback
            );
        end

        $finish;
    end

endmodule
