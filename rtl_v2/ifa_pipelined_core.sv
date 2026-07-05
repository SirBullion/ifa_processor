module ifa_pipelined_core #(
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
    output logic [WIDTH-1:0] relation_feedback
);

    // ============================================================
    // P0 — Instruction Fetch ROM
    // ============================================================

    localparam OP_NOP       = 2'b00;
    localparam OP_PHI       = 2'b01;
    localparam OP_ODU       = 2'b10;
    localparam OP_WRITE_REL = 2'b11;

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
            pc       <= 2'd0;
            p0_instr <= OP_NOP;
        end
        else if (start) begin
            p0_instr <= rom[pc];
            pc       <= pc + 1'b1;
        end
    end

    // ============================================================
    // P1 — Φ-P Coordinate Mapper
    // ============================================================

    logic [1:0] p1_instr;
    logic [WIDTH-1:0] p1_A, p1_B;

    logic [WIDTH-1:0] p1_agree;
    logic [WIDTH-1:0] p1_disagree;
    logic [WIDTH-1:0] p1_toggle;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            p1_instr    <= OP_NOP;
            p1_A        <= '0;
            p1_B        <= '0;
            p1_agree    <= '0;
            p1_disagree <= '0;
            p1_toggle   <= '0;
        end
        else begin
            p1_instr    <= p0_instr;
            p1_A        <= A_in;
            p1_B        <= B_in;

            p1_agree    <= A_in & B_in;
            p1_disagree <= A_in ^ B_in;
            p1_toggle   <= ~(A_in | B_in);
        end
    end

    // ============================================================
    // P2 — ODU
    // ============================================================

    logic [1:0] p2_instr;

    logic [WIDTH-1:0] p2_A, p2_B;
    logic [WIDTH-1:0] p2_Y;
    logic [WIDTH-1:0] p2_R_A;
    logic [WIDTH-1:0] p2_R_D;
    logic [WIDTH-1:0] p2_R_0;
    logic [WIDTH-1:0] p2_T;

    logic [WIDTH:0] carry;
    integer i;

    always_comb begin
        carry = '0;
        carry[0] = 1'b0;

        for (i = 0; i < WIDTH; i = i + 1) begin
            carry[i+1] =
                (p1_A[i] & p1_B[i]) |
                ((p1_A[i] ^ p1_B[i]) & carry[i]);
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            p2_instr <= OP_NOP;
            p2_A     <= '0;
            p2_B     <= '0;
            p2_Y     <= '0;
            p2_R_A   <= '0;
            p2_R_D   <= '0;
            p2_R_0   <= '0;
            p2_T     <= '0;
        end
        else begin
            p2_instr <= p1_instr;

            p2_A   <= p1_A;
            p2_B   <= p1_B;

            p2_Y   <= p1_A + p1_B;
            p2_R_A <= p1_agree;
            p2_R_D <= p1_disagree;
            p2_R_0 <= p1_toggle;
            p2_T   <= carry[WIDTH:1];
        end
    end

    // ============================================================
    // P3 — RMU
    // ============================================================

    logic [1:0] p3_instr;

    logic [WIDTH-1:0] p3_Y;
    logic [WIDTH-1:0] p3_R_A;
    logic [WIDTH-1:0] p3_R_D;
    logic [WIDTH-1:0] p3_R_0;
    logic [WIDTH-1:0] p3_T;

    logic [WIDTH-1:0] rmu_Y_out;
    logic [WIDTH-1:0] rmu_Y_rel;
    logic [WIDTH-1:0] rmu_R_A_mem;
    logic [WIDTH-1:0] rmu_R_D_mem;
    logic [WIDTH-1:0] rmu_R_0_mem;
    logic [WIDTH-1:0] rmu_T_mem;

    logic rmu_compressed_valid;
    logic [1:0] rmu_mode;

    logic rmu_load_en;
    logic rmu_shift_en;

    assign rmu_load_en  = (p2_instr == OP_ODU) || (p2_instr == OP_WRITE_REL);
    assign rmu_shift_en = (p2_instr == OP_WRITE_REL);

    ifa_relation_memory_unit #(
        .WIDTH(WIDTH)
    ) rmu (
        .clk(clk),
        .rst_n(rst_n),

        .load_en(rmu_load_en),
        .shift_en(rmu_shift_en),

        .Y_in(p2_Y),
        .R_A_in(p2_R_A),
        .R_D_in(p2_R_D),
        .R_0_in(p2_R_0),
        .T_in(p2_T),

        .odu_new_ra(p2_R_A),

        .Y_out(rmu_Y_out),
        .Y_rel(rmu_Y_rel),

        .R_A_mem(rmu_R_A_mem),
        .R_D_mem(rmu_R_D_mem),
        .R_0_mem(rmu_R_0_mem),
        .T_mem(rmu_T_mem),

        .compressed_valid(rmu_compressed_valid),
        .mode(rmu_mode)
    );

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            p3_instr <= OP_NOP;
            p3_Y     <= '0;
            p3_R_A   <= '0;
            p3_R_D   <= '0;
            p3_R_0   <= '0;
            p3_T     <= '0;
        end
        else begin
            p3_instr <= p2_instr;
            p3_Y     <= rmu_Y_out;
            p3_R_A   <= rmu_R_A_mem;
            p3_R_D   <= rmu_R_D_mem;
            p3_R_0   <= rmu_R_0_mem;
            p3_T     <= rmu_T_mem;
        end
    end

    assign relation_feedback = rmu_Y_rel;

    // ============================================================
    // P4 — RSM / Relation Writeback
    // ============================================================

    logic rsm_we;

    assign rsm_we = (p3_instr == OP_WRITE_REL) || (p3_instr == OP_ODU);

    ifa_relation_ram #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) rsm (
        .clk(clk),
        .we(rsm_we),
        .addr({ADDR_WIDTH{1'b0}}),

        .Y_in(p3_Y),
        .R_primary_in(p3_R_A),
        .R_secondary_in(p3_R_D),
        .mode_in(rmu_mode),

        .Y_out(Y_out),
        .R_primary_out(R_primary_out),
        .R_secondary_out(R_secondary_out),
        .mode_out(mode_out)
    );

endmodule
