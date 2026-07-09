//======================================================================
// IFÁ Processor V4 End-to-End Core
//
// A,B → RPC Stub → Relation Frame → RMU → Output
//======================================================================

module ifa_v4_end_to_end_core #(
    parameter WIDTH = 8,
    parameter DEPTH = 16
)(
    input  logic                     clk,
    input  logic                     rst,

    input  logic                     in_valid,
    input  logic [WIDTH-1:0]         A,
    input  logic [WIDTH-1:0]         B,

    output logic                     rmu_hit,
    output logic                     rmu_miss,

    output logic [WIDTH-1:0]         out_y,
    output logic [WIDTH-1:0]         out_ra,
    output logic [WIDTH-1:0]         out_rd,
    output logic [WIDTH-1:0]         out_r0,
    output logic [WIDTH-1:0]         out_t,

    output logic [31:0]              hit_count,
    output logic [31:0]              miss_count,
    output logic [31:0]              store_count,
    output logic [31:0]              evict_count
);

    logic [WIDTH-1:0] rpc_y;
    logic [WIDTH-1:0] rpc_ra;
    logic [WIDTH-1:0] rpc_rd;
    logic [WIDTH-1:0] rpc_r0;
    logic [WIDTH-1:0] rpc_t;

    ifa_rpc_stub #(
        .WIDTH(WIDTH)
    ) rpc (
        .A(A),
        .B(B),

        .Y(rpc_y),
        .RA(rpc_ra),
        .RD(rpc_rd),
        .R0(rpc_r0),
        .T(rpc_t)
    );

    ifa_v4_core #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH)
    ) core (
        .clk(clk),
        .rst(rst),

        .rpc_valid(in_valid),

        .rpc_y(rpc_y),
        .rpc_ra(rpc_ra),
        .rpc_rd(rpc_rd),
        .rpc_r0(rpc_r0),
        .rpc_t(rpc_t),

        .rmu_hit(rmu_hit),
        .rmu_miss(rmu_miss),

        .out_y(out_y),
        .out_ra(out_ra),
        .out_rd(out_rd),
        .out_r0(out_r0),
        .out_t(out_t),

        .hit_count(hit_count),
        .miss_count(miss_count),
        .store_count(store_count),
        .evict_count(evict_count)
    );

endmodule
