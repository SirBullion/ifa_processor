//======================================================================
// IFÁ Processor V4.5
// Complete Native Relation Arithmetic Unit
//
// Universal operand-relation functions:
//
//     RA(A,B) = A & B
//     RD(A,B) = A ^ B
//     R0(A,B) = ~(A | B)
//
// Every native operation returns:
//
//     F_op(A,B) = {Y_op, RA, RD, R0, T_op}
//
// Status is kept outside the core relation frame:
//
//     valid
//     exception_valid
//     exception_code
//     state_valid
//     state_code
//     EQ
//     GT
//     LT
//
// IFÁ does not use arithmetic "overflow".
//
// When a relation extends beyond the captured {T,Y} window, it enters
// an extended state:
//
//     STATE_POWER_EXTENDED
//======================================================================

module ifa_native_rau_v45 #(
    parameter integer WIDTH    = 8,
    parameter integer OP_WIDTH = 4
)(
    input  wire [OP_WIDTH-1:0] op,
    input  wire [WIDTH-1:0]    A,
    input  wire [WIDTH-1:0]    B,

    output reg  [WIDTH-1:0]    Y,
    output wire [WIDTH-1:0]    RA,
    output wire [WIDTH-1:0]    RD,
    output wire [WIDTH-1:0]    R0,
    output reg  [WIDTH-1:0]    T,

    output reg                 valid,

    output reg                 exception_valid,
    output reg  [3:0]          exception_code,

    output reg                 state_valid,
    output reg  [3:0]          state_code,

    output reg                 eq_flag,
    output reg                 gt_flag,
    output reg                 lt_flag
);

    //==================================================================
    // Native operation identities
    //==================================================================

    localparam [OP_WIDTH-1:0] OP_PAPO  = 4'h0;
    localparam [OP_WIDTH-1:0] OP_YO    = 4'h1;
    localparam [OP_WIDTH-1:0] OP_DAGBA = 4'h2;
    localparam [OP_WIDTH-1:0] OP_PIN   = 4'h3;
    localparam [OP_WIDTH-1:0] OP_KU    = 4'h4;
    localparam [OP_WIDTH-1:0] OP_GBE   = 4'h5;
    localparam [OP_WIDTH-1:0] OP_SEDA  = 4'h6;
    localparam [OP_WIDTH-1:0] OP_JU    = 4'h7;
    localparam [OP_WIDTH-1:0] OP_KERE  = 4'h8;

    //==================================================================
    // Exception codes
    //==================================================================

    localparam [3:0] EXC_NONE          = 4'h0;
    localparam [3:0] EXC_UNIMPLEMENTED = 4'h1;
    localparam [3:0] EXC_DIV_ZERO      = 4'h2;

    //==================================================================
    // IFÁ state codes
    //==================================================================

    localparam [3:0] STATE_NONE           = 4'h0;
    localparam [3:0] STATE_POWER_EXTENDED = 4'h1;

    //==================================================================
    // Universal relation fields
    //==================================================================

    assign RA = A & B;
    assign RD = A ^ B;
    assign R0 = ~(A | B);

    //==================================================================
    // Extended mathematical values
    //==================================================================

    reg [WIDTH:0]       add_full;
    reg [WIDTH:0]       sub_full;
    reg [(2*WIDTH)-1:0] mul_full;

    // GBÉ retains a two-word relation window:
    //
    //     {T,Y}
    //
    // Bits beyond this window are represented as an extended state.
    reg [(2*WIDTH)-1:0] power_acc;
    reg [(3*WIDTH)-1:0] power_product;

    integer power_index;

    //==================================================================
    // Native mathematical functions
    //==================================================================

    always @* begin
        Y = {WIDTH{1'b0}};
        T = {WIDTH{1'b0}};

        valid = 1'b1;

        exception_valid = 1'b0;
        exception_code  = EXC_NONE;

        state_valid = 1'b0;
        state_code  = STATE_NONE;

        eq_flag = 1'b0;
        gt_flag = 1'b0;
        lt_flag = 1'b0;

        add_full = {(WIDTH+1){1'b0}};
        sub_full = {(WIDTH+1){1'b0}};
        mul_full = {(2*WIDTH){1'b0}};

        power_acc =
            {{((2*WIDTH)-1){1'b0}}, 1'b1};

        power_product = {(3*WIDTH){1'b0}};

        case (op)

            //----------------------------------------------------------
            // PAPO — relation addition
            //
            // Y = modular sum
            // T = carry transport word
            //----------------------------------------------------------

            OP_PAPO: begin
                add_full = {1'b0, A} + {1'b0, B};

                Y = add_full[WIDTH-1:0];

                T = {WIDTH{1'b0}};
                T[0] = add_full[WIDTH];
            end

            //----------------------------------------------------------
            // YO — relation subtraction
            //
            // Y = modular difference
            // T = borrow transport word
            //----------------------------------------------------------

            OP_YO: begin
                sub_full = {1'b0, A} - {1'b0, B};

                Y = sub_full[WIDTH-1:0];

                T = {WIDTH{1'b0}};
                T[0] = (A < B);
            end

            //----------------------------------------------------------
            // DÁGBA — relation multiplication
            //
            //     A * B = {T,Y}
            //----------------------------------------------------------

            OP_DAGBA: begin
                mul_full = A * B;

                Y = mul_full[WIDTH-1:0];

                T = mul_full[
                    (2*WIDTH)-1:WIDTH
                ];
            end

            //----------------------------------------------------------
            // PIN — relation partition
            //
            // Y = quotient
            // T = remainder
            //----------------------------------------------------------

            OP_PIN: begin
                if (B == {WIDTH{1'b0}}) begin
                    Y = {WIDTH{1'b0}};
                    T = {WIDTH{1'b1}};

                    valid = 1'b0;

                    exception_valid = 1'b1;
                    exception_code  = EXC_DIV_ZERO;
                end else begin
                    Y = A / B;
                    T = A % B;
                end
            end

            //----------------------------------------------------------
            // KÙ — remaining relation
            //
            // Y = remainder
            // T = quotient
            //----------------------------------------------------------

            OP_KU: begin
                if (B == {WIDTH{1'b0}}) begin
                    Y = {WIDTH{1'b0}};
                    T = {WIDTH{1'b1}};

                    valid = 1'b0;

                    exception_valid = 1'b1;
                    exception_code  = EXC_DIV_ZERO;
                end else begin
                    Y = A % B;
                    T = A / B;
                end
            end

            //----------------------------------------------------------
            // GBÉ — relation exponentiation
            //
            // Captured relation window:
            //
            //     Y = lowest n bits
            //     T = next n bits
            //
            // If the relation extends above {T,Y}, it is not called an
            // overflow. It enters STATE_POWER_EXTENDED.
            //----------------------------------------------------------

            OP_GBE: begin
                power_acc =
                    {{((2*WIDTH)-1){1'b0}}, 1'b1};

                state_valid = 1'b0;
                state_code  = STATE_NONE;

                for (
                    power_index = 0;
                    power_index < (1 << WIDTH);
                    power_index = power_index + 1
                ) begin
                    if (power_index < B) begin
                        power_product =
                            power_acc * A;

                        if (
                            power_product[
                                (3*WIDTH)-1:
                                (2*WIDTH)
                            ] != {WIDTH{1'b0}}
                        ) begin
                            state_valid = 1'b1;
                            state_code =
                                STATE_POWER_EXTENDED;
                        end

                        power_acc =
                            power_product[
                                (2*WIDTH)-1:0
                            ];
                    end
                end

                Y = power_acc[WIDTH-1:0];

                T = power_acc[
                    (2*WIDTH)-1:WIDTH
                ];
            end

            //----------------------------------------------------------
            // SẸ̀DÁ — complete comparison
            //
            // Y = modular difference
            // T = comparison borrow
            //----------------------------------------------------------

            OP_SEDA: begin
                sub_full = {1'b0, A} - {1'b0, B};

                Y = sub_full[WIDTH-1:0];

                T = {WIDTH{1'b0}};
                T[0] = (A < B);

                eq_flag = (A == B);
                gt_flag = (A > B);
                lt_flag = (A < B);
            end

            //----------------------------------------------------------
            // JÙ — greater relation
            //----------------------------------------------------------

            OP_JU: begin
                Y = {WIDTH{1'b0}};
                Y[0] = (A > B);

                T = {WIDTH{1'b0}};
                T[0] = (A < B);

                eq_flag = (A == B);
                gt_flag = (A > B);
                lt_flag = (A < B);
            end

            //----------------------------------------------------------
            // KERÉ — lesser relation
            //----------------------------------------------------------

            OP_KERE: begin
                Y = {WIDTH{1'b0}};
                Y[0] = (A < B);

                T = {WIDTH{1'b0}};
                T[0] = (A < B);

                eq_flag = (A == B);
                gt_flag = (A > B);
                lt_flag = (A < B);
            end

            //----------------------------------------------------------
            // Unknown operation
            //----------------------------------------------------------

            default: begin
                valid = 1'b0;

                exception_valid = 1'b1;
                exception_code  = EXC_UNIMPLEMENTED;
            end
        endcase
    end

endmodule
