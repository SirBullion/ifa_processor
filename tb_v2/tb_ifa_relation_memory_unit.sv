`timescale 1ns/1ps

module tb_ifa_relation_memory_unit;

    logic clk, rst_n, load_en, shift_en;

    logic [3:0] Y_in, R_A_in, R_D_in, R_0_in, T_in;
    logic [3:0] odu_new_ra;

    logic [3:0] Y_out, Y_rel;
    logic [3:0] R_A_mem, R_D_mem, R_0_mem, T_mem;

    logic compressed_valid;
    logic [1:0] mode;

    ifa_relation_memory_unit dut (
        .clk(clk),
        .rst_n(rst_n),
        .load_en(load_en),
        .shift_en(shift_en),

        .Y_in(Y_in),
        .R_A_in(R_A_in),
        .R_D_in(R_D_in),
        .R_0_in(R_0_in),
        .T_in(T_in),

        .odu_new_ra(odu_new_ra),

        .Y_out(Y_out),
        .Y_rel(Y_rel),

        .R_A_mem(R_A_mem),
        .R_D_mem(R_D_mem),
        .R_0_mem(R_0_mem),
        .T_mem(T_mem),

        .compressed_valid(compressed_valid),
        .mode(mode)
    );

    always #5 clk = ~clk;

    initial begin
        $dumpfile("sim_v2/ifa_relation_memory_unit.vcd");
        $dumpvars(0, tb_ifa_relation_memory_unit);

        clk = 0;
        rst_n = 0;
        load_en = 0;
        shift_en = 0;

        odu_new_ra = 4'h2;

        // Initial ALU state: 13 + 6
        Y_in   = 4'h3;
        R_A_in = 4'h4;
        R_D_in = 4'hB;
        R_0_in = 4'h0;
        T_in   = 4'hC;

        #12;
        rst_n = 1;

        // Load full relation state
        #8;
        load_en = 1;
        #10;
        load_en = 0;

        $display("After load:");
        $display("Y_out=%h Y_rel=%h RA=%h RD=%h R0=%h T=%h valid=%b mode=%b",
                 Y_out, Y_rel, R_A_mem, R_D_mem, R_0_mem, T_mem,
                 compressed_valid, mode);

        // Barrel feedback cycles
        repeat (4) begin
            #10;
            shift_en = 1;
            #10;
            shift_en = 0;

            $display("After shift:");
            $display("Y_out=%h Y_rel=%h RA=%h RD=%h R0=%h T=%h valid=%b mode=%b",
                     Y_out, Y_rel, R_A_mem, R_D_mem, R_0_mem, T_mem,
                     compressed_valid, mode);
        end

        $finish;
    end

endmodule
