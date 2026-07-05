`timescale 1ns/1ps

module tb_phi_p_coordinate_memory_inverse;

    parameter WIDTH = 4;
    parameter DEPTH = 16;
    parameter ADDR_WIDTH = 4;

    logic clk, we;
    logic [ADDR_WIDTH-1:0] addr;

    logic [WIDTH-1:0] A, B;
    logic [WIDTH-1:0] R_A, R_D, T;
    logic [WIDTH-1:0] R_A_out, R_D_out, T_out;

    logic [WIDTH-1:0] Y_rec;
    logic [WIDTH-1:0] R_0_rec;
    logic found;

    logic [WIDTH-1:0] diff, wrap;

    ifa_phi_p_coordinate_memory #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) pcm (
        .clk(clk),
        .we(we),
        .addr(addr),

        .R_A_in(R_A),
        .R_D_in(R_D),
        .T_in(T),

        .R_A_out(R_A_out),
        .R_D_out(R_D_out),
        .T_out(T_out)
    );

    ifa_phi_p_inverse_reconstruct #(
        .WIDTH(WIDTH)
    ) inv (
        .R_A(R_A_out),
        .R_D(R_D_out),
        .T(T_out),

        .Y_rec(Y_rec),
        .R_0_rec(R_0_rec),
        .found(found)
    );

    initial clk = 0;
    always #5 clk = ~clk;

    task automatic compute_coord(input [WIDTH-1:0] a, input [WIDTH-1:0] b);
        begin
            R_A = a & b;
            R_D = a ^ b;

            if (a >= b)
                diff = a - b;
            else
                diff = b - a;

            wrap = (1 << WIDTH) - diff;

            if (diff <= wrap)
                T = diff;
            else
                T = wrap;
        end
    endtask

    initial begin
        $dumpfile("sim_v2/phi_p_coordinate_memory_inverse.vcd");
        $dumpvars(0, tb_phi_p_coordinate_memory_inverse);

        clk = 0;
        we = 0;
        addr = 0;

        A = 4'hD;
        B = 4'h6;

        compute_coord(A, B);

        @(posedge clk);
        we = 1;

        @(posedge clk);
        we = 0;

        @(posedge clk);
        @(posedge clk);

        $display("--------------------------------");
        $display("Phi-P Coordinate Memory Inverse");
        $display("--------------------------------");
        $display("A=%h B=%h", A, B);
        $display("Stored coordinate:");
        $display("R_A=%h R_D=%h T=%h", R_A, R_D, T);
        $display("Read coordinate:");
        $display("R_A=%h R_D=%h T=%h", R_A_out, R_D_out, T_out);
        $display("Reconstructed:");
        $display("Y=%h R_0=%h found=%b", Y_rec, R_0_rec, found);
        $display("--------------------------------");

        $finish;
    end

endmodule
