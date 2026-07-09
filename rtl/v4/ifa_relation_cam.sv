//======================================================================
// IFÁ Processor V4
//
// Relation CAM (Content Addressable Memory)
//
// KEY   = {RA, RD, T}
// WIDTH = 8
// KEY   = 24 bits
//
// Performs exact-key lookup.
//
// Author : IFÁ Processor
//======================================================================

module ifa_relation_cam #(
    parameter WIDTH = 8,
    parameter DEPTH = 16
)(
    input  logic                         clk,
    input  logic                         rst,

    // Lookup request
    input  logic                         lookup_en,
    input  logic [WIDTH-1:0]             lookup_ra,
    input  logic [WIDTH-1:0]             lookup_rd,
    input  logic [WIDTH-1:0]             lookup_t,

    // Hit outputs
    output logic                         hit,
    output logic [$clog2(DEPTH)-1:0]     hit_index
);

    //------------------------------------------------------------------
    // CAM Storage
    //------------------------------------------------------------------

    logic [WIDTH-1:0] key_ra [0:DEPTH-1];
    logic [WIDTH-1:0] key_rd [0:DEPTH-1];
    logic [WIDTH-1:0] key_t  [0:DEPTH-1];

    logic             valid  [0:DEPTH-1];

    integer i;

    //------------------------------------------------------------------
    // Reset
    //------------------------------------------------------------------

    always_ff @(posedge clk) begin

        if (rst) begin

            for (i = 0; i < DEPTH; i = i + 1) begin
                valid[i] <= 1'b0;
            end

        end

    end

    //------------------------------------------------------------------
    // Exact lookup
    //------------------------------------------------------------------

    always_comb begin

        hit       = 1'b0;
        hit_index = '0;

        if (lookup_en) begin

            for (int j = 0; j < DEPTH; j++) begin

                if ( valid[j] &&
                     key_ra[j] == lookup_ra &&
                     key_rd[j] == lookup_rd &&
                     key_t[j]  == lookup_t ) begin

                    hit       = 1'b1;
                    hit_index = j[$clog2(DEPTH)-1:0];

                end

            end

        end

    end

    //------------------------------------------------------------------
    // Store Task
    //
    // Used by Relation Memory Controller.
    //------------------------------------------------------------------

    task automatic store_key(

        input integer index,

        input logic [WIDTH-1:0] ra,
        input logic [WIDTH-1:0] rd,
        input logic [WIDTH-1:0] t

    );

        key_ra[index] = ra;
        key_rd[index] = rd;
        key_t [index] = t;

        valid[index]  = 1'b1;

    endtask

endmodule

