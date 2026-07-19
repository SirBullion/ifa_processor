`timescale 1ns/1ps

module ifa_phi_p8_relation_ripple (
    input  logic [7:0] a,
    input  logic [7:0] b,

    input  logic       c_initial,
    input  logic       c_phi_initial,

    output logic [7:0] a_phi,
    output logic [7:0] b_phi,
    output logic [7:0] y,
    output logic [7:0] y_phi,

    output logic [7:0] ra,
    output logic [7:0] rd,
    output logic [7:0] r0,
    output logic [7:0] t,

    output logic [7:0] ra_phi,
    output logic [7:0] rd_phi,
    output logic [7:0] r0_phi,
    output logic [7:0] t_phi,

    output logic final_carry,
    output logic final_phi_carry,

    output logic [1:0] carry_state_0,
    output logic [1:0] carry_state_1,
    output logic [1:0] carry_state_2,
    output logic [1:0] carry_state_3,
    output logic [1:0] carry_state_4,

    output logic [10:0] transport_0,
    output logic [10:0] transport_1,
    output logic [10:0] transport_2,
    output logic [10:0] transport_3,

    output logic illegal_carry_transition
);

    logic c0, c1, c2, c3, c4;
    logic cp0, cp1, cp2, cp3, cp4;
    logic [1:0] state_in_0, state_in_1, state_in_2, state_in_3;
    logic [1:0] state_out_0, state_out_1, state_out_2, state_out_3;

    assign c0  = c_initial;
    assign cp0 = c_phi_initial;

    ifa_phi_p2_relation_block block_0 (
        .a(a[1:0]), .b(b[1:0]), .c_in(c0), .c_phi_in(cp0),
        .a_phi(a_phi[1:0]), .b_phi(b_phi[1:0]),
        .y(y[1:0]), .c_out(c1), .ra(ra[1:0]), .rd(rd[1:0]),
        .r0(r0[1:0]), .t(t[1:0]),
        .y_phi(y_phi[1:0]), .c_phi_out(cp1),
        .ra_phi(ra_phi[1:0]), .rd_phi(rd_phi[1:0]),
        .r0_phi(r0_phi[1:0]), .t_phi(t_phi[1:0]),
        .transport_vector(transport_0),
        .carry_state_in(state_in_0), .carry_state_out(state_out_0)
    );

    ifa_phi_p2_relation_block block_1 (
        .a(a[3:2]), .b(b[3:2]), .c_in(c1), .c_phi_in(cp1),
        .a_phi(a_phi[3:2]), .b_phi(b_phi[3:2]),
        .y(y[3:2]), .c_out(c2), .ra(ra[3:2]), .rd(rd[3:2]),
        .r0(r0[3:2]), .t(t[3:2]),
        .y_phi(y_phi[3:2]), .c_phi_out(cp2),
        .ra_phi(ra_phi[3:2]), .rd_phi(rd_phi[3:2]),
        .r0_phi(r0_phi[3:2]), .t_phi(t_phi[3:2]),
        .transport_vector(transport_1),
        .carry_state_in(state_in_1), .carry_state_out(state_out_1)
    );

    ifa_phi_p2_relation_block block_2 (
        .a(a[5:4]), .b(b[5:4]), .c_in(c2), .c_phi_in(cp2),
        .a_phi(a_phi[5:4]), .b_phi(b_phi[5:4]),
        .y(y[5:4]), .c_out(c3), .ra(ra[5:4]), .rd(rd[5:4]),
        .r0(r0[5:4]), .t(t[5:4]),
        .y_phi(y_phi[5:4]), .c_phi_out(cp3),
        .ra_phi(ra_phi[5:4]), .rd_phi(rd_phi[5:4]),
        .r0_phi(r0_phi[5:4]), .t_phi(t_phi[5:4]),
        .transport_vector(transport_2),
        .carry_state_in(state_in_2), .carry_state_out(state_out_2)
    );

    ifa_phi_p2_relation_block block_3 (
        .a(a[7:6]), .b(b[7:6]), .c_in(c3), .c_phi_in(cp3),
        .a_phi(a_phi[7:6]), .b_phi(b_phi[7:6]),
        .y(y[7:6]), .c_out(c4), .ra(ra[7:6]), .rd(rd[7:6]),
        .r0(r0[7:6]), .t(t[7:6]),
        .y_phi(y_phi[7:6]), .c_phi_out(cp4),
        .ra_phi(ra_phi[7:6]), .rd_phi(rd_phi[7:6]),
        .r0_phi(r0_phi[7:6]), .t_phi(t_phi[7:6]),
        .transport_vector(transport_3),
        .carry_state_in(state_in_3), .carry_state_out(state_out_3)
    );

    assign final_carry     = c4;
    assign final_phi_carry = cp4;

    assign carry_state_0 = {c0, cp0};
    assign carry_state_1 = {c1, cp1};
    assign carry_state_2 = {c2, cp2};
    assign carry_state_3 = {c3, cp3};
    assign carry_state_4 = {c4, cp4};

    function automatic logic forbidden_edge(
        input logic [1:0] source_state,
        input logic [1:0] target_state
    );
        begin
            forbidden_edge =
                ((source_state == 2'b01) && (target_state == 2'b10)) ||
                ((source_state == 2'b10) && (target_state == 2'b01));
        end
    endfunction

    always_comb begin
        illegal_carry_transition =
            forbidden_edge(carry_state_0, carry_state_1) ||
            forbidden_edge(carry_state_1, carry_state_2) ||
            forbidden_edge(carry_state_2, carry_state_3) ||
            forbidden_edge(carry_state_3, carry_state_4);
    end

endmodule
