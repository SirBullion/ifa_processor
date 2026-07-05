module ifa_core_with_relation_memory #(
    parameter WIDTH = 4,
    parameter DEPTH = 16,
    parameter ADDR_WIDTH = 4
)(
    input  logic clk,
    input  logic rst_n,
    input  logic start,

    input  logic [WIDTH-1:0] A,
    input  logic [WIDTH-1:0] B,

    output logic [WIDTH-1:0] Y_out,
    output logic [WIDTH-1:0] relation_feedback,

    output logic [WIDTH-1:0] R_primary_out,
    output logic [WIDTH-1:0] R_secondary_out,
    output logic [1:0]       mode_out
);

    // --------------------------------
    // ROM instruction codes
    // --------------------------------
    localparam OP_ADD       = 2'b00;
    localparam OP_STORE_REL = 2'b01;
    localparam OP_READ_REL  = 2'b10;
    localparam OP_SHIFT_REL = 2'b11;

    logic [1:0] instr_rom [0:3];
    logic [1:0] instr;

    logic [1:0] pc;

    initial begin
        instr_rom[0] = OP_ADD;
        instr_rom[1] = OP_STORE_REL;
        instr_rom[2] = OP_READ_REL;
        instr_rom[3] = OP_SHIFT_REL;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            pc <= 2'd0;
        else if (start)
            pc <= pc + 1'b1;
    end

    assign instr = instr_rom[pc];

    // --------------------------------
    // ODU relation outputs
    // --------------------------------
    logic [WIDTH-1:0] Y;
    logic [WIDTH-1:0] R_A;
    logic [WIDTH-1:0] R_D;
    logic [WIDTH-1:0] R_0;
    logic [WIDTH-1:0] T;

    assign Y   = A + B;
    assign R_A = A & B;
    assign R_D = A ^ B;
    assign R_0 = ~(A | B);

    // simple transport for WIDTH=4 style
    logic [WIDTH:0] carry;
    integer i;

    always_comb begin
        carry = '0;
        carry[0] = 1'b0;

        for (i = 0; i < WIDTH; i = i + 1) begin
            carry[i+1] =
                (A[i] & B[i]) |
                ((A[i] ^ B[i]) & carry[i]);
        end
    end

    assign T = carry[WIDTH:1];

    // --------------------------------
    // RMU control
    // --------------------------------
    logic load_en;
    logic shift_en;

    assign load_en  = (instr == OP_STORE_REL);
    assign shift_en = (instr == OP_SHIFT_REL);

    logic [WIDTH-1:0] Y_rmu;
    logic [WIDTH-1:0] Y_rel;
    logic [WIDTH-1:0] R_A_mem;
    logic [WIDTH-1:0] R_D_mem;
    logic [WIDTH-1:0] R_0_mem;
    logic [WIDTH-1:0] T_mem;

    logic compressed_valid;
    logic [1:0] mode;

    ifa_relation_memory_unit #(
        .WIDTH(WIDTH)
    ) rmu (
        .clk(clk),
        .rst_n(rst_n),
        .load_en(load_en),
        .shift_en(shift_en),

        .Y_in(Y),
        .R_A_in(R_A),
        .R_D_in(R_D),
        .R_0_in(R_0),
        .T_in(T),

        .odu_new_ra(R_A),

        .Y_out(Y_rmu),
        .Y_rel(Y_rel),

        .R_A_mem(R_A_mem),
        .R_D_mem(R_D_mem),
        .R_0_mem(R_0_mem),
        .T_mem(T_mem),

        .compressed_valid(compressed_valid),
        .mode(mode)
    );

    // --------------------------------
    // RSM relation state memory
    // --------------------------------
    logic rsm_we;

    assign rsm_we = (instr == OP_STORE_REL);

    ifa_relation_ram #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) rsm (
        .clk(clk),
        .we(rsm_we),
        .addr(4'd0),

        .Y_in(Y_rmu),
        .R_primary_in(R_A_mem),
        .R_secondary_in(R_D_mem),
        .mode_in(mode),

        .Y_out(Y_out),
        .R_primary_out(R_primary_out),
        .R_secondary_out(R_secondary_out),
        .mode_out(mode_out)
    );

    assign relation_feedback = Y_rel;

endmodule
