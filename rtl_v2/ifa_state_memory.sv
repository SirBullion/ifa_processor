module ifa_state_memory #(
    parameter int WIDTH = 4,
    parameter int DEPTH = 16,
    parameter int ADDR_WIDTH = 4
)(
    input  logic clk,
    input  logic we,

    input  logic [ADDR_WIDTH-1:0] addr,

    input  logic [WIDTH-1:0] Y_in,
    input  logic [WIDTH-1:0] R_A_in,
    input  logic [WIDTH-1:0] R_D_in,
    input  logic [WIDTH-1:0] R_0_in,
    input  logic [WIDTH-1:0] T_in,

    output logic [WIDTH-1:0] Y_out,
    output logic [WIDTH-1:0] R_A_out,
    output logic [WIDTH-1:0] R_D_out,
    output logic [WIDTH-1:0] R_0_out,
    output logic [WIDTH-1:0] T_out
);

    logic [WIDTH-1:0] mem_Y   [0:DEPTH-1];
    logic [WIDTH-1:0] mem_RA  [0:DEPTH-1];
    logic [WIDTH-1:0] mem_RD  [0:DEPTH-1];
    logic [WIDTH-1:0] mem_R0  [0:DEPTH-1];
    logic [WIDTH-1:0] mem_T   [0:DEPTH-1];

    always_ff @(posedge clk) begin
        if (we) begin
            mem_Y[addr]  <= Y_in;
            mem_RA[addr] <= R_A_in;
            mem_RD[addr] <= R_D_in;
            mem_R0[addr] <= R_0_in;
            mem_T[addr]  <= T_in;
        end

        Y_out   <= mem_Y[addr];
        R_A_out <= mem_RA[addr];
        R_D_out <= mem_RD[addr];
        R_0_out <= mem_R0[addr];
        T_out   <= mem_T[addr];
    end

endmodule
