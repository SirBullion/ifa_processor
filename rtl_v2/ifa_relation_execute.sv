module ifa_relation_execute (
    input  logic [1:0] rel_op,

    input  logic [3:0] R_A,
    input  logic [3:0] R_D,
    input  logic [3:0] R_0,
    input  logic [3:0] T,

    output logic [3:0] Y
);

    localparam READ_RA = 2'b00;
    localparam READ_RD = 2'b01;
    localparam READ_R0 = 2'b10;
    localparam READ_T  = 2'b11;

    always_comb begin
        case (rel_op)
            READ_RA: Y = R_A;
            READ_RD: Y = R_D;
            READ_R0: Y = R_0;
            READ_T:  Y = T;
            default: Y = 4'b0000;
        endcase
    end

endmodule
