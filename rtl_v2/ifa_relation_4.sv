module ifa_relation_4 (
    input  logic [3:0] A,
    input  logic [3:0] B,

    output logic [3:0] R_A,
    output logic [3:0] R_D,
    output logic [3:0] R_0,

    output logic [2:0] P_A,
    output logic [2:0] P_D,
    output logic [2:0] P_0
);

    assign R_A = A & B;
    assign R_D = A ^ B;
    assign R_0 = (~A) & (~B);

    assign P_A = R_A[0] + R_A[1] + R_A[2] + R_A[3];
    assign P_D = R_D[0] + R_D[1] + R_D[2] + R_D[3];
    assign P_0 = R_0[0] + R_0[1] + R_0[2] + R_0[3];

endmodule
