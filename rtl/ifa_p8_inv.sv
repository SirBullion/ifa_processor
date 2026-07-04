module ifa_p8_inv (
    input  logic [7:0] y,
    output logic [7:0] x
);

    ifa_p4_inv upper_inv (
        .y(y[7:4]),
        .x(x[7:4])
    );

    ifa_p4_inv lower_inv (
        .y(y[3:0]),
        .x(x[3:0])
    );

endmodule
