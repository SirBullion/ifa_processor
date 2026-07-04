module ifa_prime_relation_engine #(
    parameter int WIDTH = 64
)(
    input  logic [WIDTH-1:0] candidate,
    input  logic [WIDTH-1:0] divisor,

    output logic [WIDTH-1:0] R_A,
    output logic [WIDTH-1:0] R_D,
    output logic [WIDTH-1:0] R_0,

    output logic [6:0] P_A,
    output logic [6:0] P_D,
    output logic [6:0] P_0
);

    assign R_A = candidate & divisor;
    assign R_D = candidate ^ divisor;
    assign R_0 = (~candidate) & (~divisor);

    always_comb begin
        P_A = $countones(R_A);
        P_D = $countones(R_D);
        P_0 = $countones(R_0);
    end

endmodule
