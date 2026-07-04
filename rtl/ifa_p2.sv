module ifa_p2 (
    input  logic A,
    input  logic B,
    output logic A_out,
    output logic B_out
);

    // Corrected P2 logic:
    // A' = A
    // B' = ~(A ^ B)
    assign A_out = A;
    assign B_out = ~(A ^ B);

endmodule
