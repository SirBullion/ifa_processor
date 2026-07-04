module ifa_add_4 (
    input  logic [3:0] A,
    input  logic [3:0] B,

    output logic [3:0] C,      // result / output Odu
    output logic [3:0] R_A,    // agreement
    output logic [3:0] R_D,    // disagreement
    output logic [3:0] T       // transport chain T1..T4
);

    logic [4:0] t_chain;

    assign t_chain[0] = 1'b0;

    genvar i;
    generate
        for (i = 0; i < 4; i++) begin : add_bit
            assign R_A[i] = A[i] & B[i];
            assign R_D[i] = A[i] ^ B[i];

            assign C[i] = R_D[i] ^ t_chain[i];

            assign t_chain[i+1] =
                R_A[i] | (R_D[i] & t_chain[i]);
        end
    endgenerate

    assign T = t_chain[4:1];

endmodule
