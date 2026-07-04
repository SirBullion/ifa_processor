module ifa_corrector (
    input  logic [7:0] y_corrupt,
    input  logic [7:0] delta,

    output logic [7:0] error_e,
    output logic [7:0] y_corrected
);

    // Since T^2 = I, recover encoded error by applying T to delta.
    ifa_t8 inverse_transport (
        .e(delta),
        .delta(error_e)
    );

    assign y_corrected = y_corrupt ^ error_e;

endmodule
