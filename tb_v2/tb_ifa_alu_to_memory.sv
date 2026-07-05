`timescale 1ns/1ps

module tb_ifa_alu_to_memory;

    parameter WIDTH = 4;
    parameter DEPTH = 16;
    parameter ADDR_WIDTH = 4;

    logic clk;
    logic we;
    logic [ADDR_WIDTH-1:0] addr;

    logic [1:0] op;
    logic [WIDTH-1:0] A, B;

    logic [WIDTH-1:0] Y;
    logic [WIDTH-1:0] R_A;
    logic [WIDTH-1:0] R_D;
    logic [WIDTH-1:0] R_0;
    logic [WIDTH-1:0] T;

    logic EQ, GT, LT;
    logic BORROW, NO_BORROW;

    logic [WIDTH-1:0] Y_mem;
    logic [WIDTH-1:0] R_A_mem;
    logic [WIDTH-1:0] R_D_mem;
    logic [WIDTH-1:0] R_0_mem;
    logic [WIDTH-1:0] T_mem;

    localparam OP_ADD = 2'b00;

    ifa_alu_4 alu (
        .op(op),
        .A(A),
        .B(B),

        .Y(Y),
        .R_A(R_A),
        .R_D(R_D),
        .R_0(R_0),
        .T(T),

        .EQ(EQ),
        .GT(GT),
        .LT(LT),
        .BORROW(BORROW),
        .NO_BORROW(NO_BORROW)
    );

    ifa_state_memory #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) mem (
        .clk(clk),
        .we(we),
        .addr(addr),

        .Y_in(Y),
        .R_A_in(R_A),
        .R_D_in(R_D),
        .R_0_in(R_0),
        .T_in(T),

        .Y_out(Y_mem),
        .R_A_out(R_A_mem),
        .R_D_out(R_D_mem),
        .R_0_out(R_0_mem),
        .T_out(T_mem)
    );

    always #5 clk = ~clk;

    initial begin
        $dumpfile("sim_v2/ifa_alu_to_memory.vcd");
        $dumpvars(0, tb_ifa_alu_to_memory);

        clk  = 0;
        we   = 0;
        addr = 4'd0;

        op = OP_ADD;

        // Test computation: 13 + 6 = 19 mod 16 = 3
        A = 4'd13;
        B = 4'd6;

        #5;
        we = 1;

        #10;
        we = 0;

        #10;

        $display("--------------------------------------");
        $display("ALU GENERATED STATE");
        $display("--------------------------------------");
        $display("A   = %b", A);
        $display("B   = %b", B);
        $display("Y   = %b", Y);
        $display("R_A = %b", R_A);
        $display("R_D = %b", R_D);
        $display("R_0 = %b", R_0);
        $display("T   = %b", T);

        $display("");
        $display("--------------------------------------");
        $display("MEMORY READBACK STATE");
        $display("--------------------------------------");
        $display("Y_mem   = %b", Y_mem);
        $display("R_A_mem = %b", R_A_mem);
        $display("R_D_mem = %b", R_D_mem);
        $display("R_0_mem = %b", R_0_mem);
        $display("T_mem   = %b", T_mem);

        $display("");
        $display("CPU would store only:");
        $display("Y = %b", Y_mem);

        $display("");
        $display("Ifa memory stores:");
        $display("(Y, R_A, R_D, R_0, T)");

        $finish;
    end

endmodule
