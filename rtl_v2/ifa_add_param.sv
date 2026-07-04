module ifa_add_param #(
    parameter int WIDTH = 32
)(
    input  logic [WIDTH-1:0] A,
    input  logic [WIDTH-1:0] B,

    output logic [WIDTH-1:0] C,
    output logic [WIDTH-1:0] R_A,
    output logic [WIDTH-1:0] R_D,
    output logic [WIDTH-1:0] T
);

    logic [WIDTH:0] t_chain;

    assign t_chain[0] = 1'b0;

    genvar i;
    generate
        for (i = 0; i < WIDTH; i++) begin : add_bit
            assign R_A[i] = A[i] & B[i];
            assign R_D[i] = A[i] ^ B[i];

            assign C[i] = R_D[i] ^ t_chain[i];

            assign t_chain[i+1] =
                R_A[i] | (R_D[i] & t_chain[i]);
        end
    endgenerate

    assign T = t_chain[WIDTH:1];

endmodule
