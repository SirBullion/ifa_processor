module ifa_call_stack #(
    parameter WIDTH = 8,
    parameter DEPTH = 16
)(
    input  logic clk,
    input  logic reset,

    input  logic push,
    input  logic pop,

    input  logic [WIDTH-1:0] push_data,

    output logic [WIDTH-1:0] top,
    output logic empty,
    output logic full
);

logic [WIDTH-1:0] stack [0:DEPTH-1];
logic [$clog2(DEPTH):0] sp;

assign empty = (sp==0);
assign full  = (sp==DEPTH);

assign top =
    (sp==0) ? 0 :
    stack[sp-1];

integer i;

always_ff @(posedge clk) begin

    if(reset) begin

        sp <= 0;

        for(i=0;i<DEPTH;i=i+1)
            stack[i] <= 0;

    end
    else begin

        if(push && !full) begin
            stack[sp] <= push_data;
            sp <= sp + 1;
        end

        if(pop && !empty)
            sp <= sp - 1;

    end

end

endmodule
