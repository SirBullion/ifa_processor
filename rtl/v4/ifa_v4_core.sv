//======================================================================
// IFÁ Processor V4 Core Wrapper
//
// Wraps Relation Memory Controller around incoming RPC frame.
//
// Input frame:
//   rpc_y, rpc_ra, rpc_rd, rpc_r0, rpc_t
//
// Output frame:
//   out_y, out_ra, out_rd, out_r0, out_t
//
// On HIT:
//   outputs stored frame
//
// On MISS:
//   stores incoming RPC frame and outputs it
//======================================================================

module ifa_v4_core #(
    parameter WIDTH = 8,
    parameter DEPTH = 16
)(
    input  logic                     clk,
    input  logic                     rst,

    input  logic                     rpc_valid,

    input  logic [WIDTH-1:0]         rpc_y,
    input  logic [WIDTH-1:0]         rpc_ra,
    input  logic [WIDTH-1:0]         rpc_rd,
    input  logic [WIDTH-1:0]         rpc_r0,
    input  logic [WIDTH-1:0]         rpc_t,

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

    ifa_relation_memory_controller #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH)
    ) rmc (
        .clk(clk),
        .rst(rst),

        .req_valid(rpc_valid),

        .in_y(rpc_y),
        .in_ra(rpc_ra),
        .in_rd(rpc_rd),
        .in_r0(rpc_r0),
        .in_t(rpc_t),

        .hit(rmu_hit),
        .miss(rmu_miss),

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
