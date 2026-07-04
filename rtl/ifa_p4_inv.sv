module ifa_p4_inv (
    input  logic [3:0] y,
    output logic [3:0] x
);

    ifa_p2_inv inv_ab (
        .A_p(y[3]),
        .B_p(y[2]),
        .A(x[3]),
        .B(x[2])
    );

    ifa_p2_inv inv_cd (
        .A_p(y[1]),
        .B_p(y[0]),
        .A(x[1]),
        .B(x[0])
    );

endmodule
