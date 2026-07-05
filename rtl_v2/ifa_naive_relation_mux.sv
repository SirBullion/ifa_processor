module ifa_naive_relation_mux #(
    parameter WIDTH = 4
)(
    input  logic [1:0] sel,

    input  logic [WIDTH-1:0] R_A,
    input  logic [WIDTH-1:0] R_D,
    input  logic [WIDTH-1:0] R_0,
    input  logic [WIDTH-1:0] T,

    output logic [WIDTH-1:0] Y_rel
);

    always_comb begin
        case (sel)
            2'b00: Y_rel = R_A;
            2'b01: Y_rel = R_D;
            2'b10: Y_rel = R_0;
            2'b11: Y_rel = T;
            default: Y_rel = '0;
        endcase
    end

endmodule
