`timescale 1ns/1ps

module tb_ifa_relation_frame;

    localparam int WIDTH        = 8;
    localparam int REL_ID_WIDTH = 8;
    localparam int OP_WIDTH     = 4;

    logic clk;
    logic rst_n;
    logic load_i;

    logic [REL_ID_WIDTH-1:0] relation_id_i;
    logic [OP_WIDTH-1:0]     operation_i;

    logic [WIDTH-1:0] operand_a_i;
    logic [WIDTH-1:0] operand_b_i;

    logic [WIDTH-1:0] phi_a_i;
    logic [WIDTH-1:0] phi_b_i;
    logic [WIDTH-1:0] phi_y_i;

    logic [WIDTH-1:0] y_i;
    logic [WIDTH-1:0] ra_i;
    logic [WIDTH-1:0] rd_i;
    logic [WIDTH-1:0] r0_i;
    logic [WIDTH:0]   value_i;

    logic transport_i;
    logic eq_i;
    logic gt_i;
    logic lt_i;
    logic state_i;
    logic valid_i;

    logic [REL_ID_WIDTH-1:0] relation_id_o;
    logic [OP_WIDTH-1:0]     operation_o;

    logic [WIDTH-1:0] operand_a_o;
    logic [WIDTH-1:0] operand_b_o;

    logic [WIDTH-1:0] phi_a_o;
    logic [WIDTH-1:0] phi_b_o;
    logic [WIDTH-1:0] phi_y_o;

    logic [WIDTH-1:0] y_o;
    logic [WIDTH-1:0] ra_o;
    logic [WIDTH-1:0] rd_o;
    logic [WIDTH-1:0] r0_o;
    logic [WIDTH:0]   value_o;

    logic transport_o;
    logic eq_o;
    logic gt_o;
    logic lt_o;
    logic state_o;
    logic valid_o;

    int tests_run;
    int tests_failed;

    ifa_relation_frame #(
        .WIDTH        (WIDTH),
        .REL_ID_WIDTH (REL_ID_WIDTH),
        .OP_WIDTH     (OP_WIDTH)
    ) dut (
        .clk           (clk),
        .rst_n         (rst_n),
        .load_i        (load_i),

        .relation_id_i (relation_id_i),
        .operation_i   (operation_i),

        .operand_a_i   (operand_a_i),
        .operand_b_i   (operand_b_i),

        .phi_a_i       (phi_a_i),
        .phi_b_i       (phi_b_i),
        .phi_y_i       (phi_y_i),

        .y_i           (y_i),
        .ra_i          (ra_i),
        .rd_i          (rd_i),
        .r0_i          (r0_i),
        .value_i       (value_i),

        .transport_i   (transport_i),
        .eq_i          (eq_i),
        .gt_i          (gt_i),
        .lt_i          (lt_i),
        .state_i       (state_i),
        .valid_i       (valid_i),

        .relation_id_o (relation_id_o),
        .operation_o   (operation_o),

        .operand_a_o   (operand_a_o),
        .operand_b_o   (operand_b_o),

        .phi_a_o       (phi_a_o),
        .phi_b_o       (phi_b_o),
        .phi_y_o       (phi_y_o),

        .y_o           (y_o),
        .ra_o          (ra_o),
        .rd_o          (rd_o),
        .r0_o          (r0_o),
        .value_o       (value_o),

        .transport_o   (transport_o),
        .eq_o          (eq_o),
        .gt_o          (gt_o),
        .lt_o          (lt_o),
        .state_o       (state_o),
        .valid_o       (valid_o)
    );

    // 100 MHz clock.
    initial clk = 1'b0;
    always #5 clk = ~clk;

    task automatic expect_bit(
        input string name,
        input logic actual,
        input logic expected
    );
        begin
            tests_run++;

            if (actual !== expected) begin
                tests_failed++;

                $display(
                    "FAIL: %-18s actual=%b expected=%b",
                    name,
                    actual,
                    expected
                );
            end
            else begin
                $display(
                    "PASS: %-18s value=%b",
                    name,
                    actual
                );
            end
        end
    endtask

    task automatic expect_value(
        input string name,
        input logic [31:0] actual,
        input logic [31:0] expected
    );
        begin
            tests_run++;

            if (actual !== expected) begin
                tests_failed++;

                $display(
                    "FAIL: %-18s actual=0x%0h expected=0x%0h",
                    name,
                    actual,
                    expected
                );
            end
            else begin
                $display(
                    "PASS: %-18s value=0x%0h",
                    name,
                    actual
                );
            end
        end
    endtask

    task automatic clear_inputs;
        begin
            load_i        = 1'b0;

            relation_id_i = '0;
            operation_i   = '0;

            operand_a_i   = '0;
            operand_b_i   = '0;

            phi_a_i       = '0;
            phi_b_i       = '0;
            phi_y_i       = '0;

            y_i           = '0;
            ra_i          = '0;
            rd_i          = '0;
            r0_i          = '0;
            value_i       = '0;

            transport_i   = 1'b0;
            eq_i          = 1'b0;
            gt_i          = 1'b0;
            lt_i          = 1'b0;
            state_i       = 1'b0;
            valid_i       = 1'b0;
        end
    endtask

    task automatic check_reset_state;
        begin
            expect_value("reset relation_id", relation_id_o, 0);
            expect_value("reset operation",   operation_o,   0);

            expect_value("reset operand_a", operand_a_o, 0);
            expect_value("reset operand_b", operand_b_o, 0);

            expect_value("reset phi_a", phi_a_o, 0);
            expect_value("reset phi_b", phi_b_o, 0);
            expect_value("reset phi_y", phi_y_o, 0);

            expect_value("reset y",     y_o,     0);
            expect_value("reset ra",    ra_o,    0);
            expect_value("reset rd",    rd_o,    0);
            expect_value("reset r0",    r0_o,    0);
            expect_value("reset value", value_o, 0);

            expect_bit("reset transport", transport_o, 0);
            expect_bit("reset eq",        eq_o,        0);
            expect_bit("reset gt",        gt_o,        0);
            expect_bit("reset lt",        lt_o,        0);
            expect_bit("reset state",     state_o,     0);
            expect_bit("reset valid",     valid_o,     0);
        end
    endtask

    initial begin
        $dumpfile("sim_v45/ifa_relation_frame.vcd");
        $dumpvars(0, tb_ifa_relation_frame);

        tests_run    = 0;
        tests_failed = 0;

        clear_inputs();

        // --------------------------------------------------------------------
        // Test 1: asynchronous reset
        // --------------------------------------------------------------------
        rst_n = 1'b0;
        #2;

        check_reset_state();

        repeat (2) @(posedge clk);
        rst_n = 1'b1;

        // --------------------------------------------------------------------
        // Test 2: load R0 = PAPO 2 ATI 3
        //
        // Expected relation channels:
        //   Y  = 5
        //   RA = 2 & 3       = 2
        //   RD = 2 ^ 3       = 1
        //   R0 = ~(2 | 3)    = FC
        // --------------------------------------------------------------------
        @(negedge clk);

        load_i        = 1'b1;

        relation_id_i = 8'h00;
        operation_i   = 4'h0;

        operand_a_i   = 8'h02;
        operand_b_i   = 8'h03;

        // Values taken from the currently verified Φ-P8 software backend.
        // The storage register does not reinterpret these values.
        phi_a_i       = 8'hA2;
        phi_b_i       = 8'hA3;
        phi_y_i       = 8'hA5;

        y_i           = 8'h05;
        ra_i          = 8'h02;
        rd_i          = 8'h01;
        r0_i          = 8'hFC;
        value_i       = 9'h005;

        transport_i   = 1'b0;
        eq_i          = 1'b0;
        gt_i          = 1'b0;
        lt_i          = 1'b1;
        state_i       = 1'b0;
        valid_i       = 1'b1;

        @(posedge clk);
        #1;

        expect_value("R0 relation_id", relation_id_o, 8'h00);
        expect_value("R0 operation",   operation_o,   4'h0);

        expect_value("R0 operand_a", operand_a_o, 8'h02);
        expect_value("R0 operand_b", operand_b_o, 8'h03);

        expect_value("R0 phi_a", phi_a_o, 8'hA2);
        expect_value("R0 phi_b", phi_b_o, 8'hA3);
        expect_value("R0 phi_y", phi_y_o, 8'hA5);

        expect_value("R0 y",     y_o,     8'h05);
        expect_value("R0 ra",    ra_o,    8'h02);
        expect_value("R0 rd",    rd_o,    8'h01);
        expect_value("R0 r0",    r0_o,    8'hFC);
        expect_value("R0 value", value_o, 9'h005);

        expect_bit("R0 transport", transport_o, 1'b0);
        expect_bit("R0 eq",        eq_o,        1'b0);
        expect_bit("R0 gt",        gt_o,        1'b0);
        expect_bit("R0 lt",        lt_o,        1'b1);
        expect_bit("R0 state",     state_o,     1'b0);
        expect_bit("R0 valid",     valid_o,     1'b1);

        // --------------------------------------------------------------------
        // Test 3: load disabled; existing frame must remain unchanged
        // --------------------------------------------------------------------
        @(negedge clk);

        load_i        = 1'b0;
        relation_id_i = 8'h55;
        y_i           = 8'hFF;
        valid_i       = 1'b0;

        @(posedge clk);
        #1;

        expect_value("hold relation_id", relation_id_o, 8'h00);
        expect_value("hold y",           y_o,           8'h05);
        expect_bit  ("hold valid",       valid_o,       1'b1);

        // --------------------------------------------------------------------
        // Test 4: load transported frame
        //
        // Mirrors:
        //   R5 = 11 DAGBA 28 = 308
        //   Y  = 308 mod 256 = 52 = 0x34
        //   T  = 1
        // --------------------------------------------------------------------
        @(negedge clk);

        load_i        = 1'b1;

        relation_id_i = 8'h05;
        operation_i   = 4'h2;

        operand_a_i   = 8'h0B;
        operand_b_i   = 8'h1C;

        phi_a_i       = 8'hAB;
        phi_b_i       = 8'hBC;
        phi_y_i       = 8'hB4;

        y_i           = 8'h34;
        ra_i          = 8'h08;
        rd_i          = 8'h17;
        r0_i          = 8'hE0;
        value_i       = 9'h134;

        transport_i   = 1'b1;
        eq_i          = 1'b0;
        gt_i          = 1'b0;
        lt_i          = 1'b1;
        state_i       = 1'b1;
        valid_i       = 1'b1;

        @(posedge clk);
        #1;

        expect_value("R5 relation_id", relation_id_o, 8'h05);
        expect_value("R5 operation",   operation_o,   4'h2);

        expect_value("R5 operand_a", operand_a_o, 8'h0B);
        expect_value("R5 operand_b", operand_b_o, 8'h1C);

        expect_value("R5 y",     y_o,     8'h34);
        expect_value("R5 ra",    ra_o,    8'h08);
        expect_value("R5 rd",    rd_o,    8'h17);
        expect_value("R5 r0",    r0_o,    8'hE0);
        expect_value("R5 value", value_o, 9'h134);

        expect_bit("R5 transport", transport_o, 1'b1);
        expect_bit("R5 state",     state_o,     1'b1);
        expect_bit("R5 valid",     valid_o,     1'b1);

        // Relation partition validation for the stored R5 frame.
        expect_value(
            "partition complete",
            ra_o | rd_o | r0_o,
            8'hFF
        );

        expect_value(
            "RA/RD disjoint",
            ra_o & rd_o,
            8'h00
        );

        expect_value(
            "RA/R0 disjoint",
            ra_o & r0_o,
            8'h00
        );

        expect_value(
            "RD/R0 disjoint",
            rd_o & r0_o,
            8'h00
        );

        // --------------------------------------------------------------------
        // Test 5: reset after populated frame
        // --------------------------------------------------------------------
        #2;
        rst_n = 1'b0;
        #1;

        check_reset_state();

        // --------------------------------------------------------------------
        // Final result
        // --------------------------------------------------------------------
        $display("");
        $display("============================================================");
        $display("IFÁ V4.5 RELATION FRAME RTL TEST SUMMARY");
        $display("============================================================");
        $display("Tests run    : %0d", tests_run);
        $display("Tests failed : %0d", tests_failed);

        if (tests_failed == 0) begin
            $display("RESULT       : PASS");
            $display("RelationFrame RTL storage behaviour verified.");
        end
        else begin
            $display("RESULT       : FAIL");
            $fatal(
                1,
                "%0d RelationFrame tests failed.",
                tests_failed
            );
        end

        $finish;
    end

endmodule
