module ifa_rau #(
    parameter int WIDTH = 8
)(
    input  logic [3:0] opcode,
    input  logic [WIDTH-1:0] A,
    input  logic [WIDTH-1:0] B,

    output logic [WIDTH-1:0] RESULT,
    output logic CARRY_OUT,

    output logic [WIDTH-1:0] AGREEMENT,
    output logic [WIDTH-1:0] DISAGREEMENT,
    output logic [WIDTH-1:0] TRANSPORT
);

    localparam ADD_R     = 4'd0;
    localparam SUB_R     = 4'd1;
    localparam COMPARE_R = 4'd5;

    logic [WIDTH:0] add_full;
    logic [WIDTH:0] sub_full;

    always_comb begin
        RESULT       = '0;
        CARRY_OUT    = 1'b0;
        AGREEMENT    = ~(A ^ B);
        DISAGREEMENT =  (A ^ B);
        TRANSPORT    = '0;

        add_full = {1'b0, A} + {1'b0, B};
        sub_full = {1'b0, A} - {1'b0, B};

        case (opcode)

            ADD_R: begin
                RESULT    = add_full[WIDTH-1:0];
                CARRY_OUT = add_full[WIDTH];

                // Relation transport for ADD:
                // where A and B disagree, carry pressure can propagate.
                TRANSPORT = DISAGREEMENT ^ RESULT;
            end

            SUB_R: begin
                RESULT    = sub_full[WIDTH-1:0];
                CARRY_OUT = sub_full[WIDTH];

                // Borrow/transport estimate
                TRANSPORT = DISAGREEMENT ^ RESULT;
            end

            COMPARE_R: begin
                RESULT = (A == B) ? {{(WIDTH-1){1'b0}},1'b1} : '0;
                TRANSPORT = AGREEMENT;
            end

            default: begin
                RESULT = '0;
                CARRY_OUT = 1'b0;
                TRANSPORT = '0;
            end

        endcase
    end

endmodule
