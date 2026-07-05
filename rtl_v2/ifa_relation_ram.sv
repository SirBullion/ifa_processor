module ifa_relation_ram #(
    parameter WIDTH = 4,
    parameter DEPTH = 16,
    parameter ADDR_WIDTH = 4
)(
    input  logic                 clk,
    input  logic                 we,

    input  logic [ADDR_WIDTH-1:0] addr,

    // compressed Ifa RAM write line
    input  logic [WIDTH-1:0]     Y_in,
    input  logic [WIDTH-1:0]     R_primary_in,
    input  logic [WIDTH-1:0]     R_secondary_in,
    input  logic [1:0]           mode_in,

    // RAM read line
    output logic [WIDTH-1:0]     Y_out,
    output logic [WIDTH-1:0]     R_primary_out,
    output logic [WIDTH-1:0]     R_secondary_out,
    output logic [1:0]           mode_out
);

    logic [WIDTH-1:0] mem_Y         [0:DEPTH-1];
    logic [WIDTH-1:0] mem_primary   [0:DEPTH-1];
    logic [WIDTH-1:0] mem_secondary [0:DEPTH-1];
    logic [1:0]       mem_mode      [0:DEPTH-1];

    always_ff @(posedge clk) begin
        if (we) begin
            mem_Y[addr]         <= Y_in;
            mem_primary[addr]   <= R_primary_in;
            mem_secondary[addr] <= R_secondary_in;
            mem_mode[addr]      <= mode_in;
        end

        Y_out           <= mem_Y[addr];
        R_primary_out   <= mem_primary[addr];
        R_secondary_out <= mem_secondary[addr];
        mode_out        <= mem_mode[addr];
    end

endmodule
