module ifa_relation_memory_unit #(
    parameter WIDTH = 4
)(
    input  logic             clk,
    input  logic             rst_n,
    input  logic             load_en,
    input  logic             shift_en,

    input  logic [WIDTH-1:0] Y_in,
    input  logic [WIDTH-1:0] R_A_in,
    input  logic [WIDTH-1:0] R_D_in,
    input  logic [WIDTH-1:0] R_0_in,
    input  logic [WIDTH-1:0] T_in,

    input  logic [WIDTH-1:0] odu_new_ra,

    output logic [WIDTH-1:0] Y_out,
    output logic [WIDTH-1:0] Y_rel,

    output logic [WIDTH-1:0] R_A_mem,
    output logic [WIDTH-1:0] R_D_mem,
    output logic [WIDTH-1:0] R_0_mem,
    output logic [WIDTH-1:0] T_mem,

    output logic             compressed_valid,
    output logic [1:0]       mode
);

    localparam MODE_FULL        = 2'b00;
    localparam MODE_DELAY_SHARE = 2'b01;

    assign Y_out = Y_in;
    assign Y_rel = R_A_mem;   // fixed fast feedback tap

    always_comb begin
        compressed_valid = 1'b0;
        mode = MODE_FULL;

        if ((R_D_in == R_0_in) && (R_0_in == T_in)) begin
            compressed_valid = 1'b1;
            mode = MODE_DELAY_SHARE;
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            R_A_mem <= '0;
            R_D_mem <= '0;
            R_0_mem <= '0;
            T_mem   <= '0;
        end

        else if (load_en) begin
            R_A_mem <= R_A_in;
            R_D_mem <= R_D_in;
            R_0_mem <= R_0_in;
            T_mem   <= T_in;
        end

        else if (shift_en) begin
            R_A_mem <= R_D_mem ^ odu_new_ra;
            R_D_mem <= T_mem;
            T_mem   <= R_0_mem;
            R_0_mem <= R_A_mem;
        end
    end

endmodule
