module ifa_prime_relation_signature (
    input  logic [63:0] candidate,

    output logic [63:0] R_A,
    output logic [63:0] R_D,
    output logic [63:0] R_0,
    output logic [6:0]  P_A,
    output logic [6:0]  P_D,
    output logic [6:0]  P_0
);

    logic [63:0] shifted;

    assign shifted = candidate >> 1;

    assign R_A = candidate & shifted;
    assign R_D = candidate ^ shifted;
    assign R_0 = (~candidate) & (~shifted);

    always_comb begin
        P_A = $countones(R_A);
        P_D = $countones(R_D);
        P_0 = $countones(R_0);
    end

endmodule
