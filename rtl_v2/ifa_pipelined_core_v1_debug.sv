module ifa_pipelined_core_v1_debug #(
    parameter WIDTH = 4,
    parameter DEPTH = 16,
    parameter ADDR_WIDTH = 4
)(
    input  logic clk,
    input  logic rst_n,
    input  logic start,

    input  logic [WIDTH-1:0] A_in,
    input  logic [WIDTH-1:0] B_in,

    output logic [WIDTH-1:0] Y_out,
    output logic [WIDTH-1:0] R_primary_out,
    output logic [WIDTH-1:0] R_secondary_out,
    output logic [1:0]       mode_out,
    output logic [WIDTH-1:0] feedback_out,

    // P0
    output logic [1:0] dbg_pc,
    output logic [1:0] dbg_p0_instr,

    // P1
    output logic [1:0] dbg_p1_instr,
    output logic [WIDTH-1:0] dbg_p1_A,
    output logic [WIDTH-1:0] dbg_p1_B,

    // P2 Phi-P
    output logic [1:0] dbg_p2_instr,
    output logic [WIDTH-1:0] dbg_p2_A,
    output logic [WIDTH-1:0] dbg_p2_B,
    output logic [WIDTH-1:0] dbg_p2_agree,
    output logic [WIDTH-1:0] dbg_p2_disagree,
    output logic [WIDTH-1:0] dbg_p2_toggle,

    // P3 ODU
    output logic [1:0] dbg_p3_instr,
    output logic [WIDTH-1:0] dbg_p3_Y,
    output logic [WIDTH-1:0] dbg_p3_R_A,
    output logic [WIDTH-1:0] dbg_p3_R_D,
    output logic [WIDTH-1:0] dbg_p3_R_0,
    output logic [WIDTH-1:0] dbg_p3_T,

    // P4 RMU
    output logic dbg_rmu_load_en,
    output logic dbg_rmu_shift_en,
    output logic [WIDTH-1:0] dbg_rmu_Y_out,
    output logic [WIDTH-1:0] dbg_rmu_Y_rel,
    output logic [WIDTH-1:0] dbg_rmu_R_A_mem,
    output logic [WIDTH-1:0] dbg_rmu_R_D_mem,
    output logic [WIDTH-1:0] dbg_rmu_R_0_mem,
    output logic [WIDTH-1:0] dbg_rmu_T_mem,
    output logic dbg_rmu_compressed_valid,
    output logic [1:0] dbg_rmu_mode,

    // P5 RSM
    output logic dbg_rsm_we,

    // P6 Feedback
    output logic [WIDTH-1:0] dbg_feedback_reg
);

    localparam OP_NOP       = 2'b00;
    localparam OP_PHI       = 2'b01;
    localparam OP_ODU       = 2'b10;
    localparam OP_WRITE_REL = 2'b11;

    // P0 Fetch
    logic [1:0] rom [0:3];
    logic [1:0] pc;
    logic [1:0] p0_instr;

    initial begin
        rom[0] = OP_PHI;
        rom[1] = OP_ODU;
        rom[2] = OP_WRITE_REL;
        rom[3] = OP_WRITE_REL;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc <= 0;
            p0_instr <= OP_NOP;
        end else if (start) begin
            p0_instr <= rom[pc];
            pc <= pc + 1'b1;
        end
    end

    // P6 feedback register
    logic [WIDTH-1:0] feedback_reg;
    assign feedback_out = feedback_reg;

    // P1 Decode / feedback mix
    logic [1:0] p1_instr;
    logic [WIDTH-1:0] p1_A, p1_B;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            p1_instr <= OP_NOP;
            p1_A <= '0;
            p1_B <= '0;
        end else begin
            p1_instr <= p0_instr;
            p1_A <= A_in;
            p1_B <= B_in ^ feedback_reg;
        end
    end

    // P2 Phi-P
    logic [1:0] p2_instr;
    logic [WIDTH-1:0] p2_A, p2_B;
    logic [WIDTH-1:0] p2_agree, p2_disagree, p2_toggle;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            p2_instr <= OP_NOP;
            p2_A <= '0;
            p2_B <= '0;
            p2_agree <= '0;
            p2_disagree <= '0;
            p2_toggle <= '0;
        end else begin
            p2_instr <= p1_instr;
            p2_A <= p1_A;
            p2_B <= p1_B;
            p2_agree    <= p1_A & p1_B;
            p2_disagree <= p1_A ^ p1_B;
            p2_toggle   <= ~(p1_A | p1_B);
        end
    end

    // P3 ODU
    logic [1:0] p3_instr;
    logic [WIDTH-1:0] p3_Y, p3_R_A, p3_R_D, p3_R_0, p3_T;

    logic [WIDTH:0] carry;
    integer i;

    always_comb begin
        carry = '0;
        carry[0] = 1'b0;
        for (i = 0; i < WIDTH; i = i + 1) begin
            carry[i+1] =
                (p2_A[i] & p2_B[i]) |
                ((p2_A[i] ^ p2_B[i]) & carry[i]);
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            p3_instr <= OP_NOP;
            p3_Y <= '0;
            p3_R_A <= '0;
            p3_R_D <= '0;
            p3_R_0 <= '0;
            p3_T <= '0;
        end else begin
            p3_instr <= p2_instr;
            p3_Y   <= p2_A + p2_B;
            p3_R_A <= p2_agree;
            p3_R_D <= p2_disagree;
            p3_R_0 <= p2_toggle;
            p3_T   <= carry[WIDTH:1];
        end
    end

    // P4 RMU
    logic rmu_load_en, rmu_shift_en;
    assign rmu_load_en  = (p3_instr == OP_ODU) || (p3_instr == OP_WRITE_REL);
    assign rmu_shift_en = (p3_instr == OP_WRITE_REL);

    logic [WIDTH-1:0] rmu_Y_out, rmu_Y_rel;
    logic [WIDTH-1:0] rmu_R_A_mem, rmu_R_D_mem, rmu_R_0_mem, rmu_T_mem;
    logic rmu_compressed_valid;
    logic [1:0] rmu_mode;

    ifa_relation_memory_unit #(.WIDTH(WIDTH)) rmu (
        .clk(clk),
        .rst_n(rst_n),
        .load_en(rmu_load_en),
        .shift_en(rmu_shift_en),

        .Y_in(p3_Y),
        .R_A_in(p3_R_A),
        .R_D_in(p3_R_D),
        .R_0_in(p3_R_0),
        .T_in(p3_T),

        .odu_new_ra(p3_R_A),

        .Y_out(rmu_Y_out),
        .Y_rel(rmu_Y_rel),

        .R_A_mem(rmu_R_A_mem),
        .R_D_mem(rmu_R_D_mem),
        .R_0_mem(rmu_R_0_mem),
        .T_mem(rmu_T_mem),

        .compressed_valid(rmu_compressed_valid),
        .mode(rmu_mode)
    );

    // P5 RSM
    logic rsm_we;
    assign rsm_we = (p3_instr == OP_ODU) || (p3_instr == OP_WRITE_REL);

    ifa_relation_ram #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) rsm (
        .clk(clk),
        .we(rsm_we),
        .addr({ADDR_WIDTH{1'b0}}),

        .Y_in(rmu_Y_out),
        .R_primary_in(rmu_R_A_mem),
        .R_secondary_in(rmu_R_D_mem),
        .mode_in(rmu_mode),

        .Y_out(Y_out),
        .R_primary_out(R_primary_out),
        .R_secondary_out(R_secondary_out),
        .mode_out(mode_out)
    );

    // P6 feedback update
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            feedback_reg <= '0;
        else
            feedback_reg <= rmu_Y_rel;
    end

    // Debug assignments
    assign dbg_pc = pc;
    assign dbg_p0_instr = p0_instr;

    assign dbg_p1_instr = p1_instr;
    assign dbg_p1_A = p1_A;
    assign dbg_p1_B = p1_B;

    assign dbg_p2_instr = p2_instr;
    assign dbg_p2_A = p2_A;
    assign dbg_p2_B = p2_B;
    assign dbg_p2_agree = p2_agree;
    assign dbg_p2_disagree = p2_disagree;
    assign dbg_p2_toggle = p2_toggle;

    assign dbg_p3_instr = p3_instr;
    assign dbg_p3_Y = p3_Y;
    assign dbg_p3_R_A = p3_R_A;
    assign dbg_p3_R_D = p3_R_D;
    assign dbg_p3_R_0 = p3_R_0;
    assign dbg_p3_T = p3_T;

    assign dbg_rmu_load_en = rmu_load_en;
    assign dbg_rmu_shift_en = rmu_shift_en;
    assign dbg_rmu_Y_out = rmu_Y_out;
    assign dbg_rmu_Y_rel = rmu_Y_rel;
    assign dbg_rmu_R_A_mem = rmu_R_A_mem;
    assign dbg_rmu_R_D_mem = rmu_R_D_mem;
    assign dbg_rmu_R_0_mem = rmu_R_0_mem;
    assign dbg_rmu_T_mem = rmu_T_mem;
    assign dbg_rmu_compressed_valid = rmu_compressed_valid;
    assign dbg_rmu_mode = rmu_mode;

    assign dbg_rsm_we = rsm_we;
    assign dbg_feedback_reg = feedback_reg;

endmodule
