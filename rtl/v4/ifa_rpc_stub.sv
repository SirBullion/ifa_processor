//======================================================================
// IFÁ Processor V4
//
// RPC Stub
//
// Inputs:
//   A, B
//
// Produces Relation Frame:
//   Y  = A + B
//   RA = A & B
//   RD = A ^ B
//   R0 = ~(A | B)
//   T  = RD ^ Y
//
// WIDTH = 8
//======================================================================

module ifa_rpc_stub #(
    parameter WIDTH = 8
)(
    input  logic [WIDTH-1:0] A,
    input  logic [WIDTH-1:0] B,

    output logic [WIDTH-1:0] Y,
    output logic [WIDTH-1:0] RA,
    output logic [WIDTH-1:0] RD,
    output logic [WIDTH-1:0] R0,
    output logic [WIDTH-1:0] T
);

    integer i;

    always_comb begin
        Y  = A + B;
        RA = A & B;
        RD = A ^ B;
        R0 = ~(A | B);
        T  = RD ^ Y;

    end

endmodule
