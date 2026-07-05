`timescale 1ns/1ps

module tb_ifa_state_memory;

    parameter WIDTH = 4;
    parameter DEPTH = 16;
    parameter ADDR_WIDTH = 4;

    logic clk;
    logic we;
    logic [ADDR_WIDTH-1:0] addr;

    logic [WIDTH-1:0] Y_in;
    logic [WIDTH-1:0] R_A_in;
    logic [WIDTH-1:0] R_D_in;
    logic [WIDTH-1:0] R_0_in;
    logic [WIDTH-1:0] T_in;

    logic [WIDTH-1:0] Y_out;
    logic [WIDTH-1:0] R_A_out;
    logic [WIDTH-1:0] R_D_out;
    logic [WIDTH-1:0] R_0_out;
    logic [WIDTH-1:0] T_out;

    ifa_state_memory #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) dut (
        .clk(clk),
        .we(we),
        .addr(addr),

        .Y_in(Y_in),
        .R_A_in(R_A_in),
        .R_D_in(R_D_in),
        .R_0_in(R_0_in),
        .T_in(T_in),

        .Y_out(Y_out),
        .R_A_out(R_A_out),
        .R_D_out(R_D_out),
        .R_0_out(R_0_out),
        .T_out(T_out)
    );

    always #5 clk = ~clk;

    initial begin

        $dumpfile("sim_v2/ifa_state_memory.vcd");
        $dumpvars(0, tb_ifa_state_memory);

        clk = 0;
        we  = 0;
        addr = 0;

        //-----------------------------
        // Store an Ifá ALU state
        //-----------------------------
        Y_in   = 4'b1001;
        R_A_in = 4'b0001;
        R_D_in = 4'b1010;
        R_0_in = 4'b0100;
        T_in   = 4'b0010;

        #5;
        we = 1;

        #10;
        we = 0;

        //-----------------------------
        // Read it back
        //-----------------------------
        #10;

        $display("--------------------------------------");
        $display("IFA MEMORY CONTENTS");
        $display("--------------------------------------");
        $display("Y   = %b", Y_out);
        $display("R_A = %b", R_A_out);
        $display("R_D = %b", R_D_out);
        $display("R_0 = %b", R_0_out);
        $display("T   = %b", T_out);
        $display("--------------------------------------");

        $display("");
        $display("CPU would only return:");
        $display("Y = %b", Y_out);

        $display("");
        $display("Ifa returns:");
        $display("Y   = %b", Y_out);
        $display("R_A = %b", R_A_out);
        $display("R_D = %b", R_D_out);
        $display("R_0 = %b", R_0_out);
        $display("T   = %b", T_out);

        $finish;

    end

endmodule
