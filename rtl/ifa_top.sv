module ifa_top (
    input  logic [7:0] x,
    input  logic [7:0] error_e,

    output logic [7:0] y,
    output logic [7:0] delta,

    output logic [5:0] xor_upper,
    output logic [5:0] and_upper,
    output logic [5:0] or_upper,

    output logic [5:0] xor_lower,
    output logic [5:0] and_lower,
    output logic [5:0] or_lower
);

    // Forward reversible processor
    ifa_p8 processor (
        .x(x),
        .y(y)
    );

    // Routing Matrix on upper 4-bit block ABCD
    ifa_rm4 rm_upper (
        .x(x[7:4]),
        .AB(),
        .AC(),
        .AD(),
        .BC(),
        .BD(),
        .CD(),
        .xor_feature(xor_upper),
        .and_feature(and_upper),
        .or_feature(or_upper)
    );

    // Routing Matrix on lower 4-bit block EFGH
    ifa_rm4 rm_lower (
        .x(x[3:0]),
        .AB(),
        .AC(),
        .AD(),
        .BC(),
        .BD(),
        .CD(),
        .xor_feature(xor_lower),
        .and_feature(and_lower),
        .or_feature(or_lower)
    );

    // Error transport
    ifa_t8 transport (
        .e(error_e),
        .delta(delta)
    );

endmodule
