module ifa_t8 (
    input  logic [7:0] e,
    output logic [7:0] delta
);

    // Pair AB: e[7], e[6]
    assign delta[7] = e[7];
    assign delta[6] = e[7] ^ e[6];

    // Pair CD: e[5], e[4]
    assign delta[5] = e[5];
    assign delta[4] = e[5] ^ e[4];

    // Pair EF: e[3], e[2]
    assign delta[3] = e[3];
    assign delta[2] = e[3] ^ e[2];

    // Pair GH: e[1], e[0]
    assign delta[1] = e[1];
    assign delta[0] = e[1] ^ e[0];

endmodule
