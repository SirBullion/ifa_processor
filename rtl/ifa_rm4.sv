module ifa_rm4 (
    input  logic [3:0] x,

    output logic [1:0] AB,
    output logic [1:0] AC,
    output logic [1:0] AD,
    output logic [1:0] BC,
    output logic [1:0] BD,
    output logic [1:0] CD,

    output logic [5:0] xor_feature,
    output logic [5:0] and_feature,
    output logic [5:0] or_feature
);

    logic A, B, C, D;

    assign A = x[3];
    assign B = x[2];
    assign C = x[1];
    assign D = x[0];

    // Pair routing
    assign AB = {A, B};
    assign AC = {A, C};
    assign AD = {A, D};
    assign BC = {B, C};
    assign BD = {B, D};
    assign CD = {C, D};

    // Feature order: AB AC AD BC BD CD
    assign xor_feature = {
        A ^ B,
        A ^ C,
        A ^ D,
        B ^ C,
        B ^ D,
        C ^ D
    };

    assign and_feature = {
        A & B,
        A & C,
        A & D,
        B & C,
        B & D,
        C & D
    };

    assign or_feature = {
        A | B,
        A | C,
        A | D,
        B | C,
        B | D,
        C | D
    };

endmodule
