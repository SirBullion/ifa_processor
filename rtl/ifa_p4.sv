module ifa_p4 (
    input  logic [3:0] x,
    output logic [3:0] y
);

    // x = A B C D
    // y = A' B' C' D'

    ifa_p2 p2_ab (
        .A(x[3]),
        .B(x[2]),
        .A_out(y[3]),
        .B_out(y[2])
    );

    ifa_p2 p2_cd (
        .A(x[1]),
        .B(x[0]),
        .A_out(y[1]),
        .B_out(y[0])
    );

endmodule
