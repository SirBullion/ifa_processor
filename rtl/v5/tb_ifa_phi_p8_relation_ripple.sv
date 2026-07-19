`timescale 1ns/1ps

module tb_ifa_phi_p8_relation_ripple;

    logic [7:0] a, b;
    logic       c_initial, c_phi_initial;
    logic [7:0] a_phi, b_phi, y, y_phi;
    logic [7:0] ra, rd, r0, t;
    logic [7:0] ra_phi, rd_phi, r0_phi, t_phi;
    logic final_carry, final_phi_carry;
    logic [1:0] carry_state_0, carry_state_1, carry_state_2;
    logic [1:0] carry_state_3, carry_state_4;
    logic [10:0] transport_0, transport_1, transport_2, transport_3;
    logic illegal_carry_transition;

    integer ai, bi, failures;
    integer carry_00, carry_01, carry_10, carry_11;
    logic [8:0] expected_sum, expected_phi_sum;
    logic [7:0] expected_a_phi, expected_b_phi;

    function automatic logic [1:0] phi_p2_ref(input logic [1:0] value);
        begin
            phi_p2_ref[1] = value[1];
            phi_p2_ref[0] = ~(value[1] ^ value[0]);
        end
    endfunction

    function automatic logic [7:0] phi_p8_ref(input logic [7:0] value);
        begin
            phi_p8_ref[1:0] = phi_p2_ref(value[1:0]);
            phi_p8_ref[3:2] = phi_p2_ref(value[3:2]);
            phi_p8_ref[5:4] = phi_p2_ref(value[5:4]);
            phi_p8_ref[7:6] = phi_p2_ref(value[7:6]);
        end
    endfunction

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

    ifa_phi_p8_relation_ripple dut (
        .a(a), .b(b),
        .c_initial(c_initial),
        .c_phi_initial(c_phi_initial),
        .a_phi(a_phi), .b_phi(b_phi),
        .y(y), .y_phi(y_phi), .ra(ra), .rd(rd), .r0(r0), .t(t),
        .ra_phi(ra_phi), .rd_phi(rd_phi), .r0_phi(r0_phi), .t_phi(t_phi),
        .final_carry(final_carry), .final_phi_carry(final_phi_carry),
        .carry_state_0(carry_state_0), .carry_state_1(carry_state_1),
        .carry_state_2(carry_state_2), .carry_state_3(carry_state_3),
        .carry_state_4(carry_state_4),
        .transport_0(transport_0), .transport_1(transport_1),
        .transport_2(transport_2), .transport_3(transport_3),
        .illegal_carry_transition(illegal_carry_transition)
    );

    task automatic fail(input string name);
        begin
            failures = failures + 1;
            if (failures <= 20)
                $display("FAIL %-28s A=%02h B=%02h Y=%02h Yphi=%02h",
                         name, a, b, y, y_phi);
        end
    endtask

    task automatic check_transport(
        input logic [10:0] value,
        input string name
    );
        begin
            if (value[1:0] !== (value[10:9] ^ value[5:4]))
                fail(name);
        end
    endtask

    initial begin
        failures = 0;

        c_initial = 1'b0;
        c_phi_initial = 1'b0;

        carry_00 = 0; carry_01 = 0; carry_10 = 0; carry_11 = 0;

        for (ai = 0; ai < 256; ai = ai + 1) begin
            for (bi = 0; bi < 256; bi = bi + 1) begin
                a = ai[7:0];
                b = bi[7:0];
                #1;

                expected_a_phi = phi_p8_ref(a);
                expected_b_phi = phi_p8_ref(b);
                expected_sum = {1'b0, a} + {1'b0, b};
                expected_phi_sum =
                    {1'b0, expected_a_phi} + {1'b0, expected_b_phi};

                if (a_phi !== expected_a_phi) fail("A Phi-P8");
                if (b_phi !== expected_b_phi) fail("B Phi-P8");
                if ({final_carry, y} !== expected_sum) fail("direct sum");
                if ({final_phi_carry, y_phi} !== expected_phi_sum)
                    fail("transformed sum");
                if (ra !== (a & b)) fail("direct RA");
                if (rd !== (a ^ b)) fail("direct RD");
                if (r0 !== ~(a | b)) fail("direct R0");
                if (t !== ((a ^ b) ^ y)) fail("direct T");
                if (ra_phi !== (expected_a_phi & expected_b_phi)) fail("phi RA");
                if (rd_phi !== (expected_a_phi ^ expected_b_phi)) fail("phi RD");
                if (r0_phi !== ~(expected_a_phi | expected_b_phi)) fail("phi R0");
                if (t_phi !== ((expected_a_phi ^ expected_b_phi) ^ y_phi)) fail("phi T");
                if (carry_state_0 !== {c_initial, c_phi_initial})
                    fail("initial carry");
                if (forbidden_edge(carry_state_0, carry_state_1) ||
                    forbidden_edge(carry_state_1, carry_state_2) ||
                    forbidden_edge(carry_state_2, carry_state_3) ||
                    forbidden_edge(carry_state_3, carry_state_4))
                    fail("forbidden carry edge");
                if (illegal_carry_transition !== 1'b0) fail("illegal-edge flag");

                check_transport(transport_0, "block 0 transport");
                check_transport(transport_1, "block 1 transport");
                check_transport(transport_2, "block 2 transport");
                check_transport(transport_3, "block 3 transport");

                case (carry_state_4)
                    2'b00: carry_00 = carry_00 + 1;
                    2'b01: carry_01 = carry_01 + 1;
                    2'b10: carry_10 = carry_10 + 1;
                    2'b11: carry_11 = carry_11 + 1;
                endcase
            end
        end

        $display("Ordered byte pairs tested : 65536");
        $display("Failures                  : %0d", failures);
        $display("(0,0) : %0d", carry_00);
        $display("(0,1) : %0d", carry_01);
        $display("(1,0) : %0d", carry_10);
        $display("(1,1) : %0d", carry_11);

        if (failures == 0 && carry_00 == 24704 && carry_01 == 8192 &&
            carry_10 == 8192 && carry_11 == 24448)
            $display("OVERALL RESULT : PASS");
        else begin
            $display("OVERALL RESULT : FAIL");
            $fatal(1);
        end

        $finish;
    end
endmodule
