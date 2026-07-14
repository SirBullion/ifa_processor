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
    always_comb begin
        // FIXED: RA (Agreement) = A & B (active agreement -- both ON).
        // Was ~(A ^ B) (XNOR), which wrongly counted shared-zero as
        // agreement too. Shared-zero belongs to R0, not RA.
        ra       =  (A & B);
        rd       =  (A ^ B);
        r1       =  (A & B);   // now redundant with ra -- safe to remove
                                // once you've confirmed no other module
                                // still reads r1 specifically.
        r0       = ~(A | B);
        a_over_b =  (A & ~B);
        b_over_a = (~A & B);
        {add_carry, add_result} = A + B;
        {sub_borrow, sub_result} = A - B;
        result = (op == RPC_SUB) ? sub_result : add_result;
        carry_borrow = (op == RPC_SUB) ? sub_borrow : add_carry;
        eq = (A == B);
        gt = (A > B);
        lt = (A < B);
    end
endmodule
