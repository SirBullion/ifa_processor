module ifa_compare_4 (
    input  logic [3:0] A,
    input  logic [3:0] B,

    output logic [3:0] R_D,        // disagreement state
    output logic       EQ,         // A == B
    output logic       GT,         // A > B
    output logic       LT,         // A < B

    output logic [3:0] D,          // subtraction result (optional)
    output logic [3:0] T           // transport chain (optional)
);

    logic [3:0] R_A_sub;
    logic       BORROW;
    logic       NO_BORROW;

    // Native subtraction
    ifa_sub_4 sub (
        .A(A),
        .B(B),
        .D(D),
        .R_A(R_A_sub),
        .R_D(),          // not used here
        .T(T),
        .BORROW(BORROW),
        .NO_BORROW(NO_BORROW)
    );

    // Native disagreement for comparison
    assign R_D = A ^ B;

    // Equality
    assign EQ = (R_D == 4'b0000);

    // Ordering
    assign GT = (~EQ) & NO_BORROW;
    assign LT = (~EQ) & BORROW;

endmodule
