module ifa_sub_4 (
    input  logic [3:0] A,
    input  logic [3:0] B,

    output logic [3:0] D,        // difference / output Odu
    output logic [3:0] R_A,      // subtraction agreement
    output logic [3:0] R_D,      // subtraction disagreement
    output logic [3:0] T,        // transport chain T1..T4
    output logic       BORROW,   // 1 means borrow occurred
    output logic       NO_BORROW // 1 means no borrow
);

    logic [3:0] B_rev;
    logic [4:0] t_chain;

    assign B_rev = ~B;

    // A - B = A + ~B + 1
    assign t_chain[0] = 1'b1;

    genvar i;
    generate
        for (i = 0; i < 4; i++) begin : sub_bit
            assign R_A[i] = A[i] & B_rev[i];
            assign R_D[i] = A[i] ^ B_rev[i];

            assign D[i] = R_D[i] ^ t_chain[i];

            assign t_chain[i+1] =
                R_A[i] | (R_D[i] & t_chain[i]);
        end
    endgenerate

    assign T = t_chain[4:1];

    assign NO_BORROW = t_chain[4];
    assign BORROW    = ~t_chain[4];

endmodule

