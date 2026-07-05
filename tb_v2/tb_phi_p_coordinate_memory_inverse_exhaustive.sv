`timescale 1ns/1ps

module tb_phi_p_coordinate_memory_inverse_exhaustive;

    parameter WIDTH = 4;
    parameter DEPTH = 256;
    parameter ADDR_WIDTH = 8;

    localparam MOD = (1 << WIDTH);

    logic clk, we;
    logic [ADDR_WIDTH-1:0] addr;

    logic [WIDTH-1:0] A, B;
    logic [WIDTH-1:0] R_A, R_D, T;
    logic [WIDTH-1:0] R_A_out, R_D_out, T_out;

    logic [WIDTH-1:0] Y_rec;
    logic [WIDTH-1:0] R_0_rec;
    logic found;

    logic [WIDTH-1:0] Y_gold;
    logic [WIDTH-1:0] R_0_gold;

    logic [WIDTH-1:0] diff, wrap;

    integer a_i, b_i;
    integer idx;
    integer errors;

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

            wrap = MOD - diff;

            if (diff <= wrap)
                T = diff;
            else
                T = wrap;
        end
    endtask

    task automatic compute_gold(input [WIDTH-1:0] a, input [WIDTH-1:0] b);
        begin
            Y_gold   = a + b;
            R_0_gold = ~(a | b);
        end
    endtask

    initial begin
        $dumpfile("sim_v2/phi_p_coordinate_memory_inverse_exhaustive.vcd");
        $dumpvars(0, tb_phi_p_coordinate_memory_inverse_exhaustive);

        errors = 0;
        we = 0;
        addr = 0;

        // WRITE ALL 256 COORDINATES
        idx = 0;
        for (a_i = 0; a_i < MOD; a_i = a_i + 1) begin
            for (b_i = 0; b_i < MOD; b_i = b_i + 1) begin
                A = a_i[WIDTH-1:0];
                B = b_i[WIDTH-1:0];

                compute_coord(A, B);

                addr = idx[ADDR_WIDTH-1:0];

                @(posedge clk);
                we = 1;
                @(posedge clk);
                we = 0;

                idx = idx + 1;
            end
        end

        $display("--- write complete: %0d coordinates stored ---", idx);

        // READ ALL BACK AND RECONSTRUCT
        idx = 0;
        for (a_i = 0; a_i < MOD; a_i = a_i + 1) begin
            for (b_i = 0; b_i < MOD; b_i = b_i + 1) begin
                A = a_i[WIDTH-1:0];
                B = b_i[WIDTH-1:0];

                compute_gold(A, B);

                addr = idx[ADDR_WIDTH-1:0];

                @(posedge clk);
                @(posedge clk);

                if (!found) begin
                    $display("[FAIL] idx=%0d A=%h B=%h not found", idx, A, B);
                    errors++;
                end

                if (Y_rec !== Y_gold) begin
                    $display("[FAIL] idx=%0d A=%h B=%h Y expected=%h got=%h",
                             idx, A, B, Y_gold, Y_rec);
                    errors++;
                end

                if (R_0_rec !== R_0_gold) begin
                    $display("[FAIL] idx=%0d A=%h B=%h R0 expected=%h got=%h",
                             idx, A, B, R_0_gold, R_0_rec);
                    errors++;
                end

                idx = idx + 1;
            end
        end

        if (errors == 0)
            $display("\n=== PASS: all 256 Phi-P coordinates reconstructed Y and R_0 correctly ===\n");
        else
            $display("\n=== FAIL: %0d reconstruction errors ===\n", errors);

        $finish;
    end

endmodule
