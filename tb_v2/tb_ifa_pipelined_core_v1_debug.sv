`timescale 1ns/1ps

module tb_ifa_pipelined_core_v1_debug;

    logic clk, rst_n, start;
    logic [3:0] A_in, B_in;

    logic [3:0] Y_out, R_primary_out, R_secondary_out, feedback_out;
    logic [1:0] mode_out;

    logic [1:0] dbg_pc, dbg_p0_instr, dbg_p1_instr, dbg_p2_instr, dbg_p3_instr;
    logic [3:0] dbg_p1_A, dbg_p1_B;
    logic [3:0] dbg_p2_A, dbg_p2_B, dbg_p2_agree, dbg_p2_disagree, dbg_p2_toggle;
    logic [3:0] dbg_p3_Y, dbg_p3_R_A, dbg_p3_R_D, dbg_p3_R_0, dbg_p3_T;
    logic dbg_rmu_load_en, dbg_rmu_shift_en, dbg_rmu_compressed_valid, dbg_rsm_we;
    logic [3:0] dbg_rmu_Y_out, dbg_rmu_Y_rel;
    logic [3:0] dbg_rmu_R_A_mem, dbg_rmu_R_D_mem, dbg_rmu_R_0_mem, dbg_rmu_T_mem;
    logic [1:0] dbg_rmu_mode;
    logic [3:0] dbg_feedback_reg;

    ifa_pipelined_core_v1_debug dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .A_in(A_in),
        .B_in(B_in),

        .Y_out(Y_out),
        .R_primary_out(R_primary_out),
        .R_secondary_out(R_secondary_out),
        .mode_out(mode_out),
        .feedback_out(feedback_out),

        .dbg_pc(dbg_pc),
        .dbg_p0_instr(dbg_p0_instr),

        .dbg_p1_instr(dbg_p1_instr),
        .dbg_p1_A(dbg_p1_A),
        .dbg_p1_B(dbg_p1_B),

        .dbg_p2_instr(dbg_p2_instr),
        .dbg_p2_A(dbg_p2_A),
        .dbg_p2_B(dbg_p2_B),
        .dbg_p2_agree(dbg_p2_agree),
        .dbg_p2_disagree(dbg_p2_disagree),
        .dbg_p2_toggle(dbg_p2_toggle),

        .dbg_p3_instr(dbg_p3_instr),
        .dbg_p3_Y(dbg_p3_Y),
        .dbg_p3_R_A(dbg_p3_R_A),
        .dbg_p3_R_D(dbg_p3_R_D),
        .dbg_p3_R_0(dbg_p3_R_0),
        .dbg_p3_T(dbg_p3_T),

        .dbg_rmu_load_en(dbg_rmu_load_en),
        .dbg_rmu_shift_en(dbg_rmu_shift_en),
        .dbg_rmu_Y_out(dbg_rmu_Y_out),
        .dbg_rmu_Y_rel(dbg_rmu_Y_rel),
        .dbg_rmu_R_A_mem(dbg_rmu_R_A_mem),
        .dbg_rmu_R_D_mem(dbg_rmu_R_D_mem),
        .dbg_rmu_R_0_mem(dbg_rmu_R_0_mem),
        .dbg_rmu_T_mem(dbg_rmu_T_mem),
        .dbg_rmu_compressed_valid(dbg_rmu_compressed_valid),
        .dbg_rmu_mode(dbg_rmu_mode),

        .dbg_rsm_we(dbg_rsm_we),
        .dbg_feedback_reg(dbg_feedback_reg)
    );

    always #5 clk = ~clk;

    initial begin
        $dumpfile("sim_v2/ifa_pipelined_core_v1_debug.vcd");
        $dumpvars(0, tb_ifa_pipelined_core_v1_debug);

        clk = 0;
        rst_n = 0;
        start = 0;

        A_in = 4'hD;
        B_in = 4'h6;

        #12;
        rst_n = 1;

        repeat (20) begin
            @(posedge clk);
            start = 1;
            @(posedge clk);
            start = 0;

            $display(
                "pc=%0d p0=%b p1=%b p2=%b p3=%b | A=%h Bmix=%h Y=%h RA=%h RD=%h R0=%h T=%h | RMU_RA=%h RMU_RD=%h FB=%h | RSM_Y=%h RSM_RA=%h RSM_RD=%h mode=%b",
                dbg_pc,
                dbg_p0_instr,
                dbg_p1_instr,
                dbg_p2_instr,
                dbg_p3_instr,
                dbg_p2_A,
                dbg_p2_B,
                dbg_p3_Y,
                dbg_p3_R_A,
                dbg_p3_R_D,
                dbg_p3_R_0,
                dbg_p3_T,
                dbg_rmu_R_A_mem,
                dbg_rmu_R_D_mem,
                dbg_feedback_reg,
                Y_out,
                R_primary_out,
                R_secondary_out,
                mode_out
            );
        end

        $finish;
    end

endmodule
