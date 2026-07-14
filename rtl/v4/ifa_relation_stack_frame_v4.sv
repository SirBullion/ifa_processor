//======================================================================
// IFÁ Processor V4
// Canonical Relation-Stack Frame Codec
//
// The IFÁ stack preserves a complete relation and its continuation.
// It is not defined merely as a conventional byte stack.
//
// Canonical packed order:
//
// {
//     RETURN_PC,
//     OP,
//     Y,
//     RA,
//     RD,
//     R0,
//     T,
//     VALID,
//     EXC,
//     EXC_CODE,
//     STATE,
//     STATE_CODE,
//     EQ,
//     GT,
//     LT
// }
//
// For WIDTH=8 and OP_WIDTH=4:
//
//     FRAME_WIDTH = 66 bits
//
// Stack-capacity extension is represented separately as STACK_TRANSPORT.
// An absent frame is represented separately as RELATION_ABSENT.
// Neither condition modifies the mathematical T field.
//======================================================================

module ifa_relation_stack_frame_v4 #(
    parameter integer WIDTH    = 8,
    parameter integer OP_WIDTH = 4,

    parameter integer FRAME_WIDTH =
        (6 * WIDTH) + OP_WIDTH + 14
)(
    //------------------------------------------------------------------
    // Relation and continuation inputs
    //------------------------------------------------------------------

    input  logic [WIDTH-1:0]       in_return_pc,

    input  logic [OP_WIDTH-1:0]    in_op,

    input  logic [WIDTH-1:0]       in_y,
    input  logic [WIDTH-1:0]       in_ra,
    input  logic [WIDTH-1:0]       in_rd,
    input  logic [WIDTH-1:0]       in_r0,
    input  logic [WIDTH-1:0]       in_t,

    input  logic                   in_valid,

    input  logic                   in_exception,
    input  logic [3:0]             in_exception_code,

    input  logic                   in_state,
    input  logic [3:0]             in_state_code,

    input  logic                   in_eq,
    input  logic                   in_gt,
    input  logic                   in_lt,

    //------------------------------------------------------------------
    // Canonical packed frame
    //------------------------------------------------------------------

    output logic [FRAME_WIDTH-1:0] packed_frame,

    //------------------------------------------------------------------
    // Decoded frame outputs
    //------------------------------------------------------------------

    output logic [WIDTH-1:0]       out_return_pc,

    output logic [OP_WIDTH-1:0]    out_op,

    output logic [WIDTH-1:0]       out_y,
    output logic [WIDTH-1:0]       out_ra,
    output logic [WIDTH-1:0]       out_rd,
    output logic [WIDTH-1:0]       out_r0,
    output logic [WIDTH-1:0]       out_t,

    output logic                   out_valid,

    output logic                   out_exception,
    output logic [3:0]             out_exception_code,

    output logic                   out_state,
    output logic [3:0]             out_state_code,

    output logic                   out_eq,
    output logic                   out_gt,
    output logic                   out_lt
);

    //==================================================================
    // Parameter validation
    //==================================================================

    initial begin
        if (WIDTH < 1) begin
            $error(
                "ifa_relation_stack_frame_v4: WIDTH must be >= 1"
            );
            $finish;
        end

        if (OP_WIDTH < 1) begin
            $error(
                "ifa_relation_stack_frame_v4: OP_WIDTH must be >= 1"
            );
            $finish;
        end

        if (FRAME_WIDTH != ((6 * WIDTH) + OP_WIDTH + 14)) begin
            $error(
                "ifa_relation_stack_frame_v4: invalid FRAME_WIDTH"
            );
            $finish;
        end
    end

    //==================================================================
    // Canonical frame packing
    //==================================================================

    always_comb begin
        packed_frame = {
            in_return_pc,

            in_op,

            in_y,
            in_ra,
            in_rd,
            in_r0,
            in_t,

            in_valid,

            in_exception,
            in_exception_code,

            in_state,
            in_state_code,

            in_eq,
            in_gt,
            in_lt
        };
    end

    //==================================================================
    // Canonical frame unpacking
    //==================================================================

    always_comb begin
        {
            out_return_pc,

            out_op,

            out_y,
            out_ra,
            out_rd,
            out_r0,
            out_t,

            out_valid,

            out_exception,
            out_exception_code,

            out_state,
            out_state_code,

            out_eq,
            out_gt,
            out_lt
        } = packed_frame;
    end

endmodule
