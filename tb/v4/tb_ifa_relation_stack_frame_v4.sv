`timescale 1ns/1ps

module tb_ifa_relation_stack_frame_v4;

    localparam integer WIDTH       = 8;
    localparam integer OP_WIDTH    = 4;
    localparam integer FRAME_WIDTH =
        (6 * WIDTH) + OP_WIDTH + 14;

    logic [WIDTH-1:0] in_return_pc;
    logic [OP_WIDTH-1:0] in_op;

    logic [WIDTH-1:0] in_y;
    logic [WIDTH-1:0] in_ra;
    logic [WIDTH-1:0] in_rd;
    logic [WIDTH-1:0] in_r0;
    logic [WIDTH-1:0] in_t;

    logic in_valid;
    logic in_exception;
    logic [3:0] in_exception_code;
    logic in_state;
    logic [3:0] in_state_code;
    logic in_eq;
    logic in_gt;
    logic in_lt;

    logic [FRAME_WIDTH-1:0] packed_frame;

    logic [WIDTH-1:0] out_return_pc;
    logic [OP_WIDTH-1:0] out_op;

    logic [WIDTH-1:0] out_y;
    logic [WIDTH-1:0] out_ra;
    logic [WIDTH-1:0] out_rd;
    logic [WIDTH-1:0] out_r0;
    logic [WIDTH-1:0] out_t;

    logic out_valid;
    logic out_exception;
    logic [3:0] out_exception_code;
    logic out_state;
    logic [3:0] out_state_code;
    logic out_eq;
    logic out_gt;
    logic out_lt;

    ifa_relation_stack_frame_v4 #(
        .WIDTH       (WIDTH),
        .OP_WIDTH    (OP_WIDTH),
        .FRAME_WIDTH (FRAME_WIDTH)
    ) dut (
        .in_return_pc(in_return_pc),
        .in_op(in_op),

        .in_y(in_y),
        .in_ra(in_ra),
        .in_rd(in_rd),
        .in_r0(in_r0),
        .in_t(in_t),

        .in_valid(in_valid),

        .in_exception(in_exception),
        .in_exception_code(in_exception_code),

        .in_state(in_state),
        .in_state_code(in_state_code),

        .in_eq(in_eq),
        .in_gt(in_gt),
        .in_lt(in_lt),

        .packed_frame(packed_frame),

        .out_return_pc(out_return_pc),
        .out_op(out_op),

        .out_y(out_y),
        .out_ra(out_ra),
        .out_rd(out_rd),
        .out_r0(out_r0),
        .out_t(out_t),

        .out_valid(out_valid),

        .out_exception(out_exception),
        .out_exception_code(out_exception_code),

        .out_state(out_state),
        .out_state_code(out_state_code),

        .out_eq(out_eq),
        .out_gt(out_gt),
        .out_lt(out_lt)
    );

    initial begin
        in_return_pc = 8'h2A;

        in_op = 4'h5;

        in_y  = 8'hB9;
        in_ra = 8'h04;
        in_rd = 8'h0B;
        in_r0 = 8'hF0;
        in_t  = 8'hA6;

        in_valid = 1'b1;

        in_exception      = 1'b0;
        in_exception_code = 4'h0;

        in_state      = 1'b1;
        in_state_code = 4'h1;

        in_eq = 1'b0;
        in_gt = 1'b1;
        in_lt = 1'b0;

        #1;

        if (FRAME_WIDTH != 66)
            $fatal(1, "Expected FRAME_WIDTH=66");

        if (out_return_pc !== in_return_pc)
            $fatal(1, "RETURN_PC round-trip failed");

        if (out_op !== in_op)
            $fatal(1, "OP round-trip failed");

        if (
            out_y  !== in_y  ||
            out_ra !== in_ra ||
            out_rd !== in_rd ||
            out_r0 !== in_r0 ||
            out_t  !== in_t
        )
            $fatal(1, "Relation-frame round-trip failed");

        if (
            out_valid          !== in_valid          ||
            out_exception      !== in_exception      ||
            out_exception_code !== in_exception_code ||
            out_state          !== in_state          ||
            out_state_code     !== in_state_code
        )
            $fatal(1, "Relation-status round-trip failed");

        if (
            out_eq !== in_eq ||
            out_gt !== in_gt ||
            out_lt !== in_lt
        )
            $fatal(1, "Predicate round-trip failed");

        $display(
            "PASS: Canonical IFÁ relation-stack frame round-trip"
        );

        $display(
            "PASS: Relation-stack FRAME_WIDTH=%0d",
            FRAME_WIDTH
        );

        $finish;
    end

endmodule
