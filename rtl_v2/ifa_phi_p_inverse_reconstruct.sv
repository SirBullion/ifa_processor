//============================================================
// ifa_phi_p_inverse_reconstruct.sv
//
// Reconstructs relation state from compact coordinate:
//
//   coordinate = (R_A, R_D, T)
//
// For V2 first pass:
//   R_0 is reconstructed from R_A and R_D.
//   Y is reconstructed by search over all A,B pairs
//   that match R_A, R_D, T.
//
// This is small WIDTH=4 proof hardware.
//============================================================

module ifa_phi_p_inverse_reconstruct #(
    parameter WIDTH = 4
)(
    input  logic [WIDTH-1:0] R_A,
    input  logic [WIDTH-1:0] R_D,
    input  logic [WIDTH-1:0] T,

    output logic [WIDTH-1:0] Y_rec,
    output logic [WIDTH-1:0] R_0_rec,
    output logic             found
);

    localparam integer MOD = (1 << WIDTH);

    integer ia;
    integer ib;

    logic [WIDTH-1:0] a;
    logic [WIDTH-1:0] b;
    logic [WIDTH-1:0] ra_tmp;
    logic [WIDTH-1:0] rd_tmp;
    logic [WIDTH-1:0] r0_tmp;
    logic [WIDTH-1:0] t_tmp;
    logic [WIDTH-1:0] y_tmp;
    logic [WIDTH-1:0] diff;
    logic [WIDTH-1:0] wrap;

    always @(*) begin
        Y_rec   = '0;
        R_0_rec = '0;
        found   = 1'b0;

        for (ia = 0; ia < MOD; ia = ia + 1) begin
            for (ib = 0; ib < MOD; ib = ib + 1) begin

                a = ia;
                b = ib;

                ra_tmp = a & b;
                rd_tmp = a ^ b;
                r0_tmp = ~(a | b);
                y_tmp  = a + b;

                if (a >= b)
                    diff = a - b;
                else
                    diff = b - a;

                wrap = MOD - diff;

                if (diff <= wrap)
                    t_tmp = diff;
                else
                    t_tmp = wrap;

                if (!found &&
                    ra_tmp == R_A &&
                    rd_tmp == R_D &&
                    t_tmp  == T) begin
                    Y_rec   = y_tmp;
                    R_0_rec = r0_tmp;
                    found   = 1'b1;
                end
            end
        end
    end

endmodule
