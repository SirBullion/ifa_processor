module ifa_p2_inv (
    input  logic A_p,
    input  logic B_p,
    output logic A,
    output logic B
);

    // Forward:
    // A' = A
    // B' = ~(A ^ B)
    //
    // Inverse:
    // A = A'
    // B = ~(A' ^ B')

    assign A = A_p;
    assign B = ~(A_p ^ B_p);

endmodule
