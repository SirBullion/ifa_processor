`timescale 1ns/1ps

module ifa_phi_p2_relation_block (
    input  logic [1:0] a,
    input  logic [1:0] b,
    input  logic       c_in,
    input  logic       c_phi_in,

    output logic [1:0] a_phi,
    output logic [1:0] b_phi,

    output logic [1:0] y,
    output logic       c_out,
    output logic [1:0] ra,
    output logic [1:0] rd,
    output logic [1:0] r0,
    output logic [1:0] t,

    output logic [1:0] y_phi,
    output logic       c_phi_out,
    output logic [1:0] ra_phi,
    output logic [1:0] rd_phi,
    output logic [1:0] r0_phi,
    output logic [1:0] t_phi,

    output logic [10:0] transport_vector,
    output logic [1:0]  carry_state_in,
    output logic [1:0]  carry_state_out
);

    logic [2:0] direct_sum;
    logic [2:0] transformed_sum;

    always_comb begin
        a_phi[1] = a[1];
        a_phi[0] = ~(a[1] ^ a[0]);

        b_phi[1] = b[1];
        b_phi[0] = ~(b[1] ^ b[0]);

        direct_sum = {1'b0, a} + {1'b0, b} + c_in;
        y          = direct_sum[1:0];
        c_out      = direct_sum[2];

        ra = a & b;
        rd = a ^ b;
        r0 = ~(a | b);
        t  = rd ^ y;

        transformed_sum = {1'b0, a_phi}
                        + {1'b0, b_phi}
                        + c_phi_in;

        y_phi     = transformed_sum[1:0];
        c_phi_out = transformed_sum[2];

        ra_phi = a_phi & b_phi;
        rd_phi = a_phi ^ b_phi;
        r0_phi = ~(a_phi | b_phi);
        t_phi  = rd_phi ^ y_phi;

        transport_vector = {
            y ^ y_phi,
            c_out ^ c_phi_out,
            ra ^ ra_phi,
            rd ^ rd_phi,
            r0 ^ r0_phi,
            t ^ t_phi
        };

        carry_state_in  = {c_in, c_phi_in};
        carry_state_out = {c_out, c_phi_out};
    end

endmodule
