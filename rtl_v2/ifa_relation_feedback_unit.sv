module ifa_relation_feedback_unit #(
    parameter int WIDTH = 8
)(
    input  logic [WIDTH-1:0] current_y,
    input  logic [WIDTH-1:0] current_ra,
    input  logic [WIDTH-1:0] current_rd,
    input  logic [WIDTH-1:0] current_r0,
    input  logic [WIDTH-1:0] current_t,

    input  logic [WIDTH-1:0] prev_y,
    input  logic [WIDTH-1:0] prev_ra,
    input  logic [WIDTH-1:0] prev_rd,
    input  logic [WIDTH-1:0] prev_r0,
    input  logic [WIDTH-1:0] prev_t,

    output logic [WIDTH-1:0] fb_y,
    output logic [WIDTH-1:0] fb_ra,
    output logic [WIDTH-1:0] fb_rd,
    output logic [WIDTH-1:0] fb_r0,
    output logic [WIDTH-1:0] fb_t
);

    always_comb begin
        fb_y  = current_y  ^ prev_t;
        fb_ra = current_ra ^ prev_rd;
        fb_rd = current_rd ^ prev_ra;
        fb_r0 = current_r0 ^ prev_y;
        fb_t  = current_t  ^ prev_r0;
    end

endmodule
