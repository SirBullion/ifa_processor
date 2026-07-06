module ifa_rpc #(
    parameter int WIDTH = 8
)(
    input  logic [3:0] op,
    input  logic [WIDTH-1:0] A,
    input  logic [WIDTH-1:0] B,

    output logic [WIDTH-1:0] result,
    output logic carry_borrow,
    output logic eq,
    output logic gt,
    output logic lt,

    output logic [WIDTH-1:0] ra,
    output logic [WIDTH-1:0] rd,
    output logic [WIDTH-1:0] r1,
    output logic [WIDTH-1:0] r0,
    output logic [WIDTH-1:0] a_over_b,
    output logic [WIDTH-1:0] b_over_a
);

    localparam RPC_ADD     = 4'd0;
    localparam RPC_SUB     = 4'd1;
    localparam RPC_COMPARE = 4'd2;

    logic [WIDTH-1:0] add_result;
    logic add_carry;

    logic [WIDTH-1:0] sub_result;
    logic sub_borrow;

    integer i;

    always_comb begin
        ra       = ~(A ^ B);
        rd       =  (A ^ B);
        r1       =  (A & B);
        r0       = ~(A | B);
        a_over_b =  (A & ~B);
        b_over_a = (~A & B);

        add_result = '0;
        add_carry  = 1'b0;

        for (i = 0; i < WIDTH; i++) begin
            add_result[i] = rd[i] ^ add_carry;
            add_carry = r1[i] | (rd[i] & add_carry);
        end

        sub_result = '0;
        sub_borrow = 1'b0;

        for (i = 0; i < WIDTH; i++) begin
            sub_result[i] = rd[i] ^ sub_borrow;
            sub_borrow = b_over_a[i] | (ra[i] & sub_borrow);
        end

        eq = 1'b1;
        gt = 1'b0;
        lt = 1'b0;

        for (i = WIDTH-1; i >= 0; i--) begin
            if (eq && a_over_b[i]) begin
                gt = 1'b1;
                eq = 1'b0;
            end else if (eq && b_over_a[i]) begin
                lt = 1'b1;
                eq = 1'b0;
            end
        end

        result = '0;
        carry_borrow = 1'b0;

        case (op)
            RPC_ADD: begin
                result = add_result;
                carry_borrow = add_carry;
            end

            RPC_SUB: begin
                result = sub_result;
                carry_borrow = sub_borrow;
            end

            RPC_COMPARE: begin
                result = {{(WIDTH-3){1'b0}}, eq, gt, lt};
                carry_borrow = 1'b0;
            end

            default: begin
                result = '0;
                carry_borrow = 1'b0;
            end
        endcase
    end

endmodule
