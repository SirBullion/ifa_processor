module ifa_alu_4 (
    input  logic [1:0] op,
    input  logic [3:0] A,
    input  logic [3:0] B,

    output logic [3:0] Y,

    output logic [3:0] R_A,
    output logic [3:0] R_D,
    output logic [3:0] R_0,

    output logic [3:0] T,

    output logic EQ,
    output logic GT,
    output logic LT,

    output logic BORROW,
    output logic NO_BORROW
);

    localparam OP_ADD = 2'b00;
    localparam OP_SUB = 2'b01;
    localparam OP_CMP = 2'b10;

    logic [3:0] add_C, add_RA, add_RD, add_T;
    logic [3:0] sub_D, sub_RA, sub_RD, sub_T;
    logic sub_BORROW, sub_NO_BORROW;

    logic [3:0] cmp_D, cmp_RD, cmp_T;
    logic cmp_EQ, cmp_GT, cmp_LT;

    logic [3:0] rel_RA;
    logic [3:0] rel_RD;
    logic [3:0] rel_R0;

        ifa_relation_4 u_relation (
        .A(A),
        .B(B),
        .R_A(rel_RA),
        .R_D(rel_RD),
        .R_0(rel_R0),
        .P_A(),
        .P_D(),
        .P_0()
    );


    ifa_add_4 u_add (
        .A(A), .B(B),
        .C(add_C),
        .R_A(add_RA),
        .R_D(add_RD),
        .T(add_T)
    );

    ifa_sub_4 u_sub (
        .A(A), .B(B),
        .D(sub_D),
        .R_A(sub_RA),
        .R_D(sub_RD),
        .T(sub_T),
        .BORROW(sub_BORROW),
        .NO_BORROW(sub_NO_BORROW)
    );

    ifa_compare_4 u_cmp (
        .A(A), .B(B),
        .R_D(cmp_RD),
        .EQ(cmp_EQ),
        .GT(cmp_GT),
        .LT(cmp_LT),
        .D(cmp_D),
        .T(cmp_T)
    );

    always_comb begin
        Y         = 4'b0000;
R_A       = 4'b0000;
R_D       = 4'b0000;
R_0       = 4'b0000;
T         = 4'b0000;
        EQ        = 1'b0;
        GT        = 1'b0;
        LT        = 1'b0;
        BORROW    = 1'b0;
        NO_BORROW = 1'b0;

        case (op)
            OP_ADD: begin
    Y   = add_C;

    R_A = rel_RA;
    R_D = rel_RD;
    R_0 = rel_R0;

    T   = add_T;
end

         OP_SUB: begin
    Y         = sub_D;
    R_A       = sub_RA;
    R_D       = sub_RD;
    R_0       = 4'b0000;
    T         = sub_T;
    BORROW    = sub_BORROW;
    NO_BORROW = sub_NO_BORROW;
end

            OP_CMP: begin
    Y   = cmp_D;

    R_A = rel_RA;
    R_D = rel_RD;
    R_0 = rel_R0;

    T   = cmp_T;

    EQ  = cmp_EQ;
    GT  = cmp_GT;
    LT  = cmp_LT;
end

            default: begin
                Y = 4'b0000;
            end
        endcase
    end

endmodule
