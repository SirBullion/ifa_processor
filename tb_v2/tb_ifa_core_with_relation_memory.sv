`timescale 1ns/1ps

module tb_ifa_core_with_relation_memory;

    logic clk;
    logic rst_n;
    logic start;

    logic [3:0] A;
    logic [3:0] B;

    logic [3:0] Y_out;
    logic [3:0] relation_feedback;
    logic [3:0] R_primary_out;
    logic [3:0] R_secondary_out;
    logic [1:0] mode_out;

    ifa_core_with_relation_memory dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .A(A),
        .B(B),
        .Y_out(Y_out),
        .relation_feedback(relation_feedback),
        .R_primary_out(R_primary_out),
        .R_secondary_out(R_secondary_out),
        .mode_out(mode_out)
    );

    always #5 clk = ~clk;

    initial begin
        $dumpfile("sim_v2/ifa_core_with_relation_memory.vcd");
        $dumpvars(0, tb_ifa_core_with_relation_memory);

        clk = 0;
        rst_n = 0;
        start = 0;

        A = 4'hD;
        B = 4'h6;

        #12;
        rst_n = 1;

        repeat (8) begin
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
