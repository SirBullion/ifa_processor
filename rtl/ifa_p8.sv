module ifa_p8 (
    input  logic [7:0] x,
    output logic [7:0] y
);

    ifa_p4 upper (
        .x(x[7:4]),
        .y(y[7:4])
    );

    ifa_p4 lower (
        .x(x[3:0]),
        .y(y[3:0])
    );

endmodule
