`timescale 1ns/1ps
module tb_relation_equivalence_full;
    parameter WIDTH = 8;
    localparam MOD  = (1 << WIDTH);
    localparam MASK = MOD - 1;

    logic [WIDTH-1:0] A, B;
    logic [3:0] op;

    logic [WIDTH-1:0] py_Y, py_RA, py_RD, py_R0, py_T;
    logic [WIDTH-1:0] diff, wrap;

    task automatic python_relation_model(
        input [WIDTH-1:0] a,
        input [WIDTH-1:0] b
    );
        begin
            py_Y  = a + b;
            py_RA = a & b;
            py_RD = a ^ b;
            py_R0 = ~(a | b);
            if (a >= b) diff = a - b; else diff = b - a;
            wrap = MOD - diff;
            py_T = (diff <= wrap) ? diff : wrap;
        end
    endtask

    logic [WIDTH-1:0] dut_result;
    logic dut_carry_borrow, dut_eq, dut_gt, dut_lt;
    logic [WIDTH-1:0] dut_ra, dut_rd, dut_r1, dut_r0;
    logic [WIDTH-1:0] dut_a_over_b, dut_b_over_a;

    ifa_rpc #(.WIDTH(WIDTH)) dut (
        .op(op), .A(A), .B(B),
        .result(dut_result), .carry_borrow(dut_carry_borrow),
        .eq(dut_eq), .gt(dut_gt), .lt(dut_lt),
        .ra(dut_ra), .rd(dut_rd), .r1(dut_r1), .r0(dut_r0),
        .a_over_b(dut_a_over_b), .b_over_a(dut_b_over_a)
    );

    integer total_vectors;
    integer ra_mismatches, rd_mismatches, r0_mismatches;
    integer add_sum_mismatches, add_carry_mismatches;
    integer sub_diff_mismatches, sub_borrow_mismatches;
    integer eq_mismatches, gt_mismatches, lt_mismatches;
    integer max_report, reported;
    integer ai, bi;
    logic [WIDTH:0] add_full_ref;

    initial begin
        $dumpfile("sim_v2/relation_equivalence_full.vcd");
        $dumpvars(0, tb_relation_equivalence_full);

        total_vectors = 0;
        ra_mismatches = 0; rd_mismatches = 0; r0_mismatches = 0;
        add_sum_mismatches = 0; add_carry_mismatches = 0;
        sub_diff_mismatches = 0; sub_borrow_mismatches = 0;
        eq_mismatches = 0; gt_mismatches = 0; lt_mismatches = 0;
        max_report = 20; reported = 0;

        $display("=========================================================");
        $display("EXHAUSTIVE RELATION EQUIVALENCE: ALL %0d x %0d = %0d VECTORS",
                  MOD, MOD, MOD*MOD);
        $display("=========================================================");

        for (ai = 0; ai < MOD; ai = ai + 1) begin
            for (bi = 0; bi < MOD; bi = bi + 1) begin
                A = ai[WIDTH-1:0];
                B = bi[WIDTH-1:0];

                op = 4'd0; #1;
                python_relation_model(A, B);
                total_vectors = total_vectors + 1;

                if (py_RA !== dut_ra) begin
                    ra_mismatches = ra_mismatches + 1;
                    if (reported < max_report) begin
                        $display("[RA MISMATCH] A=0x%0h B=0x%0h python=0x%0h rtl=0x%0h",
                                  A, B, py_RA, dut_ra);
                        reported = reported + 1;
                    end
                end
                if (py_RD !== dut_rd) rd_mismatches = rd_mismatches + 1;
                if (py_R0 !== dut_r0) r0_mismatches = r0_mismatches + 1;

                if ((py_Y !== dut_result))
                    add_sum_mismatches = add_sum_mismatches + 1;
                add_full_ref = {1'b0, A} + {1'b0, B};
                if (add_full_ref[WIDTH] !== dut_carry_borrow)
                    add_carry_mismatches = add_carry_mismatches + 1;

                op = 4'd1; #1;
                if ((A - B) !== dut_result)
                    sub_diff_mismatches = sub_diff_mismatches + 1;
                if ((A < B) !== dut_carry_borrow)
                    sub_borrow_mismatches = sub_borrow_mismatches + 1;

                if ((A == B) !== dut_eq) eq_mismatches = eq_mismatches + 1;
                if ((A > B)  !== dut_gt) gt_mismatches = gt_mismatches + 1;
                if ((A < B)  !== dut_lt) lt_mismatches = lt_mismatches + 1;
            end
        end

        $display("=========================================================");
        $display("RESULTS: %0d total vectors", total_vectors);
        $display("RA mismatches            : %0d", ra_mismatches);
        $display("RD mismatches            : %0d", rd_mismatches);
        $display("R0 mismatches            : %0d", r0_mismatches);
        $display("ADD sum mismatches       : %0d", add_sum_mismatches);
        $display("ADD carry mismatches     : %0d", add_carry_mismatches);
        $display("SUB diff mismatches      : %0d", sub_diff_mismatches);
        $display("SUB borrow mismatches    : %0d", sub_borrow_mismatches);
        $display("EQ flag mismatches       : %0d", eq_mismatches);
        $display("GT flag mismatches       : %0d", gt_mismatches);
        $display("LT flag mismatches       : %0d", lt_mismatches);
        $display("=========================================================");

        if (ra_mismatches + rd_mismatches + r0_mismatches +
            add_sum_mismatches + add_carry_mismatches +
            sub_diff_mismatches + sub_borrow_mismatches +
            eq_mismatches + gt_mismatches + lt_mismatches == 0)
            $display("PASS: full equivalence confirmed across all %0d vectors.", total_vectors);
        else
            $display("FAIL: mismatches found -- patch is NOT fully verified.");
        $display("=========================================================");

        $finish;
    end
endmodule
