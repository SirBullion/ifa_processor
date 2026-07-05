`timescale 1ns/1ps

module tb_ifa_relation_execute_from_memory;

    logic [1:0] rel_op;

    logic [3:0] R_A_mem;
    logic [3:0] R_D_mem;
    logic [3:0] R_0_mem;
    logic [3:0] T_mem;

    logic [3:0] Y_rel;

    ifa_relation_execute exec (
        .rel_op(rel_op),
        .R_A(R_A_mem),
        .R_D(R_D_mem),
        .R_0(R_0_mem),
        .T(T_mem),
        .Y(Y_rel)
    );

    initial begin
        $dumpfile("sim_v2/ifa_relation_execute_from_memory.vcd");
        $dumpvars(0, tb_ifa_relation_execute_from_memory);

        // Stored relation state from 13 + 6
        // A = 1101
        // B = 0110
        // R_A = 0100
        // R_D = 1011
        // R_0 = 0000
        // T   = 1100

        R_A_mem = 4'b0100;
        R_D_mem = 4'b1011;
        R_0_mem = 4'b0000;
        T_mem   = 4'b1100;

        $display("--------------------------------------");
        $display("EXECUTING FROM RELATION MEMORY ONLY");
        $display("--------------------------------------");

        rel_op = 2'b00; #1;
        $display("READ_RA -> %b", Y_rel);

        rel_op = 2'b01; #1;
        $display("READ_RD -> %b", Y_rel);

        rel_op = 2'b10; #1;
        $display("READ_R0 -> %b", Y_rel);

        rel_op = 2'b11; #1;
        $display("READ_T  -> %b", Y_rel);

        $display("--------------------------------------");
        $display("No A or B were read.");
        $display("No AND/XOR/NOR/carry recomputation.");
        $display("Relation state executed directly.");
        $display("--------------------------------------");

        $finish;
    end

endmodule
