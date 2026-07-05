//============================================================
// ifa_phi_p_coordinate_memory.sv
//
// V2 Phi-P Coordinate Memory
//
// Stores compact coordinate:
//   R_A, R_D, T
//
// Instead of storing expanded record:
//   Y, R_A, R_D, R_0, T, mode
//============================================================

module ifa_phi_p_coordinate_memory #(
    parameter WIDTH = 4,
    parameter DEPTH = 16,
    parameter ADDR_WIDTH = 4
)(
    input  logic                 clk,
    input  logic                 we,
    input  logic [ADDR_WIDTH-1:0] addr,

    input  logic [WIDTH-1:0]     R_A_in,
    input  logic [WIDTH-1:0]     R_D_in,
    input  logic [WIDTH-1:0]     T_in,

    output logic [WIDTH-1:0]     R_A_out,
    output logic [WIDTH-1:0]     R_D_out,
    output logic [WIDTH-1:0]     T_out
);

    logic [WIDTH-1:0] mem_RA [0:DEPTH-1];
    logic [WIDTH-1:0] mem_RD [0:DEPTH-1];
    logic [WIDTH-1:0] mem_T  [0:DEPTH-1];

    always_ff @(posedge clk) begin
        if (we) begin
            mem_RA[addr] <= R_A_in;
            mem_RD[addr] <= R_D_in;
            mem_T [addr] <= T_in;
        end

        R_A_out <= mem_RA[addr];
        R_D_out <= mem_RD[addr];
        T_out   <= mem_T [addr];
    end

endmodule
