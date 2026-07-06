module ifa_relation_frame_stack #(
    parameter int WIDTH = 8,
    parameter int DEPTH = 16
)(
    input  logic clk,
    input  logic reset,

    input  logic push,
    input  logic pop,

    input  logic [WIDTH-1:0] y_in,
    input  logic [WIDTH-1:0] ra_in,
    input  logic [WIDTH-1:0] rd_in,
    input  logic [WIDTH-1:0] r0_in,
    input  logic [WIDTH-1:0] t_in,

    output logic [WIDTH-1:0] y_out,
    output logic [WIDTH-1:0] ra_out,
    output logic [WIDTH-1:0] rd_out,
    output logic [WIDTH-1:0] r0_out,
    output logic [WIDTH-1:0] t_out,

    output logic empty,
    output logic full
);

    logic [WIDTH-1:0] y_stack  [0:DEPTH-1];
    logic [WIDTH-1:0] ra_stack [0:DEPTH-1];
    logic [WIDTH-1:0] rd_stack [0:DEPTH-1];
    logic [WIDTH-1:0] r0_stack [0:DEPTH-1];
    logic [WIDTH-1:0] t_stack  [0:DEPTH-1];

    logic [$clog2(DEPTH):0] sp;

    assign empty = (sp == 0);
    assign full  = (sp == DEPTH);

    assign y_out  = (sp == 0) ? '0 : y_stack[sp-1];
    assign ra_out = (sp == 0) ? '0 : ra_stack[sp-1];
    assign rd_out = (sp == 0) ? '0 : rd_stack[sp-1];
    assign r0_out = (sp == 0) ? '0 : r0_stack[sp-1];
    assign t_out  = (sp == 0) ? '0 : t_stack[sp-1];

    integer i;

    always_ff @(posedge clk) begin
        if (reset) begin
            sp <= 0;
            for (i = 0; i < DEPTH; i++) begin
                y_stack[i]  <= '0;
                ra_stack[i] <= '0;
                rd_stack[i] <= '0;
                r0_stack[i] <= '0;
                t_stack[i]  <= '0;
            end
        end else begin
            if (push && !full) begin
                y_stack[sp]  <= y_in;
                ra_stack[sp] <= ra_in;
                rd_stack[sp] <= rd_in;
                r0_stack[sp] <= r0_in;
                t_stack[sp]  <= t_in;
                sp <= sp + 1;
            end

            if (pop && !empty) begin
                sp <= sp - 1;
            end
        end
    end

endmodule
