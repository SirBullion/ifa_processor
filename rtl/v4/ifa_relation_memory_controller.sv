//======================================================================
// IFÁ Processor V4
//
// Relation Memory Controller
//
// WIDTH = 8
// FRAME = {Y, RA, RD, R0, T}
// KEY   = {RA, RD, T}
// DEPTH = 16
// HIT   = exact key match
// EVICT = FIFO
//======================================================================

module ifa_relation_memory_controller #(
    parameter WIDTH = 8,
    parameter DEPTH = 16
)(
    input  logic                     clk,
    input  logic                     rst,

    input  logic                     req_valid,

    input  logic [WIDTH-1:0]         in_y,
    input  logic [WIDTH-1:0]         in_ra,
    input  logic [WIDTH-1:0]         in_rd,
    input  logic [WIDTH-1:0]         in_r0,
    input  logic [WIDTH-1:0]         in_t,

    output logic                     hit,
    output logic                     miss,

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

    localparam INDEX_W = $clog2(DEPTH);

    // ------------------------------------------------------------
    // Storage
    // ------------------------------------------------------------

    logic [WIDTH-1:0] mem_y  [0:DEPTH-1];
    logic [WIDTH-1:0] mem_ra [0:DEPTH-1];
    logic [WIDTH-1:0] mem_rd [0:DEPTH-1];
    logic [WIDTH-1:0] mem_r0 [0:DEPTH-1];
    logic [WIDTH-1:0] mem_t  [0:DEPTH-1];

    logic valid [0:DEPTH-1];

    logic [INDEX_W-1:0] fifo_ptr;

    // ------------------------------------------------------------
    // Lookup combinational logic
    // ------------------------------------------------------------

    logic lookup_hit;
    logic [INDEX_W-1:0] lookup_index;

    integer i;

    always_comb begin
        lookup_hit   = 1'b0;
        lookup_index = '0;

        for (int j = 0; j < DEPTH; j = j + 1) begin
            if (
                valid[j] &&
                mem_ra[j] == in_ra &&
                mem_rd[j] == in_rd &&
                mem_t [j] == in_t
            ) begin
                lookup_hit   = 1'b1;
                lookup_index = j;
            end
        end
    end

    // ------------------------------------------------------------
    // Sequential controller
    // ------------------------------------------------------------

    always_ff @(posedge clk) begin
        if (rst) begin
            fifo_ptr <= '0;

            hit  <= 1'b0;
            miss <= 1'b0;

            out_y  <= '0;
            out_ra <= '0;
            out_rd <= '0;
            out_r0 <= '0;
            out_t  <= '0;

            hit_count   <= 32'd0;
            miss_count  <= 32'd0;
            store_count <= 32'd0;
            evict_count <= 32'd0;

            for (i = 0; i < DEPTH; i = i + 1) begin
                valid[i] <= 1'b0;

                mem_y [i] <= '0;
                mem_ra[i] <= '0;
                mem_rd[i] <= '0;
                mem_r0[i] <= '0;
                mem_t [i] <= '0;
            end

        end else begin
            hit  <= 1'b0;
            miss <= 1'b0;

            if (req_valid) begin

                if (lookup_hit) begin
                    // Cache hit: return stored full frame
                    hit  <= 1'b1;
                    miss <= 1'b0;

                    hit_count <= hit_count + 32'd1;

                    out_y  <= mem_y [lookup_index];
                    out_ra <= mem_ra[lookup_index];
                    out_rd <= mem_rd[lookup_index];
                    out_r0 <= mem_r0[lookup_index];
                    out_t  <= mem_t [lookup_index];

                end else begin
                    // Cache miss: store incoming frame at FIFO pointer
                    hit  <= 1'b0;
                    miss <= 1'b1;

                    miss_count  <= miss_count + 32'd1;
                    store_count <= store_count + 32'd1;

                    mem_y [fifo_ptr] <= in_y;
                    mem_ra[fifo_ptr] <= in_ra;
                    mem_rd[fifo_ptr] <= in_rd;
                    mem_r0[fifo_ptr] <= in_r0;
                    mem_t [fifo_ptr] <= in_t;
                    if (valid[fifo_ptr]) begin
                        evict_count <= evict_count + 32'd1;
                    end

                    valid[fifo_ptr]  <= 1'b1;

                    out_y  <= in_y;
                    out_ra <= in_ra;
                    out_rd <= in_rd;
                    out_r0 <= in_r0;
                    out_t  <= in_t;

                    fifo_ptr <= fifo_ptr + 1'b1;
                end

            end
        end
    end

endmodule
