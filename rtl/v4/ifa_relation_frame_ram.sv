//======================================================================
// IFÁ Processor V4
//
// Relation Frame RAM
//
// FRAME = {Y, RA, RD, R0, T}
// WIDTH = 8
// FRAME = 40 bits
// DEPTH = 16
//======================================================================

module ifa_relation_frame_ram #(
    parameter WIDTH = 8,
    parameter DEPTH = 16
)(
    input  logic                     clk,
    input  logic                     rst,

    input  logic                     write_en,
    input  logic [$clog2(DEPTH)-1:0] write_index,

    input  logic [WIDTH-1:0]         write_y,
    input  logic [WIDTH-1:0]         write_ra,
    input  logic [WIDTH-1:0]         write_rd,
    input  logic [WIDTH-1:0]         write_r0,
    input  logic [WIDTH-1:0]         write_t,

    input  logic [$clog2(DEPTH)-1:0] read_index,

    output logic [WIDTH-1:0]         read_y,
    output logic [WIDTH-1:0]         read_ra,
    output logic [WIDTH-1:0]         read_rd,
    output logic [WIDTH-1:0]         read_r0,
    output logic [WIDTH-1:0]         read_t
);

    logic [WIDTH-1:0] mem_y  [0:DEPTH-1];
    logic [WIDTH-1:0] mem_ra [0:DEPTH-1];
    logic [WIDTH-1:0] mem_rd [0:DEPTH-1];
    logic [WIDTH-1:0] mem_r0 [0:DEPTH-1];
    logic [WIDTH-1:0] mem_t  [0:DEPTH-1];

    integer i;

    always_ff @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < DEPTH; i = i + 1) begin
                mem_y[i]  <= '0;
                mem_ra[i] <= '0;
                mem_rd[i] <= '0;
                mem_r0[i] <= '0;
                mem_t[i]  <= '0;
            end
        end else if (write_en) begin
            mem_y [write_index] <= write_y;
            mem_ra[write_index] <= write_ra;
            mem_rd[write_index] <= write_rd;
            mem_r0[write_index] <= write_r0;
            mem_t [write_index] <= write_t;
        end
    end

    always_comb begin
        read_y  = mem_y [read_index];
        read_ra = mem_ra[read_index];
        read_rd = mem_rd[read_index];
        read_r0 = mem_r0[read_index];
        read_t  = mem_t [read_index];
    end

endmodule
