`timescale 1ns/1ps

module tb_ifa_yara_pe;

    localparam int WIDTH        = 8;
    localparam int REL_ID_WIDTH = 8;
    localparam int OP_WIDTH     = 4;
    localparam int VALUE_WIDTH  = 32;

    localparam logic [3:0] OP_PAPO  = 4'h0;
    localparam logic [3:0] OP_YO    = 4'h1;
    localparam logic [3:0] OP_DAGBA = 4'h2;
    localparam logic [3:0] OP_PIN   = 4'h3;
    localparam logic [3:0] OP_KU    = 4'h4;
    localparam logic [3:0] OP_GBE   = 4'h5;
    localparam logic [3:0] OP_SEDA  = 4'h6;
    localparam logic [3:0] OP_JU    = 4'h7;
    localparam logic [3:0] OP_KERE  = 4'h8;

    logic clk;
    logic rst_n;
    logic start_i;

    logic [REL_ID_WIDTH-1:0] relation_id_i;
    logic [OP_WIDTH-1:0] operation_i;

    logic [WIDTH-1:0] operand_a_i;
    logic [WIDTH-1:0] operand_b_i;

    logic [WIDTH-1:0] phi_a_i;
    logic [WIDTH-1:0] phi_b_i;

    logic busy_o;
    logic done_o;

    logic [REL_ID_WIDTH-1:0] relation_id_o;
    logic [OP_WIDTH-1:0] operation_o;

    logic [WIDTH-1:0] operand_a_o;
    logic [WIDTH-1:0] operand_b_o;

    logic [WIDTH-1:0] phi_a_o;
    logic [WIDTH-1:0] phi_b_o;
    logic [WIDTH-1:0] phi_y_o;

    logic [WIDTH-1:0] y_o;

    logic [WIDTH-1:0] ra_o;
    logic [WIDTH-1:0] rd_o;
    logic [WIDTH-1:0] r0_o;

    logic [VALUE_WIDTH-1:0] value_o;

    logic transport_o;

    logic eq_o;
    logic gt_o;
    logic lt_o;

    logic state_o;
    logic valid_o;

    int tests_run;
    int tests_failed;

    ifa_yara_pe #(
        .WIDTH        (WIDTH),
        .REL_ID_WIDTH (REL_ID_WIDTH),
        .OP_WIDTH     (OP_WIDTH),
        .VALUE_WIDTH  (VALUE_WIDTH)
    ) dut (
        .clk           (clk),
        .rst_n         (rst_n),
        .start_i       (start_i),

        .relation_id_i (relation_id_i),
        .operation_i   (operation_i),

        .operand_a_i   (operand_a_i),
        .operand_b_i   (operand_b_i),

        .phi_a_i       (phi_a_i),
        .phi_b_i       (phi_b_i),

        .busy_o        (busy_o),
        .done_o        (done_o),

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

    // --------------------------------------------------------------------
    // Exact Φ-P8 reference channels for PE integration verification
    // --------------------------------------------------------------------
    logic [7:0] phi_reference_a_i;
    logic [7:0] phi_reference_b_i;
    logic [7:0] phi_reference_y_i;

    logic [7:0] expected_phi_a;
    logic [7:0] expected_phi_b;
    logic [7:0] expected_phi_y;

    ifa_phi_p8 phi_reference_a (
        .binary_i(phi_reference_a_i),
        .phi_o   (expected_phi_a)
    );

    ifa_phi_p8 phi_reference_b (
        .binary_i(phi_reference_b_i),
        .phi_o   (expected_phi_b)
    );

    ifa_phi_p8 phi_reference_y (
        .binary_i(phi_reference_y_i),
        .phi_o   (expected_phi_y)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    task automatic expect_value(
        input string name,
        input logic [63:0] actual,
        input logic [63:0] expected
    );
        begin
            tests_run++;

            if (actual !== expected) begin
                tests_failed++;

                $display(
                    "FAIL: %-24s actual=0x%0h expected=0x%0h",
                    name,
                    actual,
                    expected
                );
            end
            else begin
                $display(
                    "PASS: %-24s value=0x%0h",
                    name,
                    actual
                );
            end
        end
    endtask

    task automatic execute_and_check(
        input logic [7:0] relation_id,
        input logic [3:0] operation,
        input logic [7:0] a,
        input logic [7:0] b,
        input logic [31:0] expected_value,
        input logic [7:0] expected_y,
        input logic expected_transport,
        input logic expected_valid
    );
        logic expected_eq;
        logic expected_gt;
        logic expected_lt;

        logic [7:0] expected_ra;
        logic [7:0] expected_rd;
        logic [7:0] expected_r0;

        begin
            expected_eq = (a == b);
            expected_gt = (a > b);
            expected_lt = (a < b);

            expected_ra = a & b;
            expected_rd = a ^ b;
            expected_r0 = ~(a | b);

            @(negedge clk);

            relation_id_i = relation_id;
            operation_i   = operation;

            operand_a_i   = a;
            operand_b_i   = b;

            // Legacy PE ports are retained temporarily but are no longer
            // used by the DUT. Exact Φ-P8 is generated internally.
            phi_a_i = '0;
            phi_b_i = '0;

            // Drive the independent Φ-P8 reference blocks.
            phi_reference_a_i = a;
            phi_reference_b_i = b;
            phi_reference_y_i = expected_y;

            start_i       = 1'b1;

            @(posedge clk);
            #1;

            start_i = 1'b0;

            expect_value("relation_id", relation_id_o, relation_id);
            expect_value("operation", operation_o, operation);

            expect_value("operand A", operand_a_o, a);
            expect_value("operand B", operand_b_o, b);

            expect_value("exact phi A", phi_a_o, expected_phi_a);
            expect_value("exact phi B", phi_b_o, expected_phi_b);
            expect_value("exact phi Y", phi_y_o, expected_phi_y);

            expect_value("VALUE", value_o, expected_value);
            expect_value("Y", y_o, expected_y);

            expect_value("RA", ra_o, expected_ra);
            expect_value("RD", rd_o, expected_rd);
            expect_value("R0", r0_o, expected_r0);

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

            expect_value("transport", transport_o, expected_transport);
            expect_value("state", state_o, expected_transport);
            expect_value("valid", valid_o, expected_valid);

            expect_value("EQ", eq_o, expected_eq);
            expect_value("GT", gt_o, expected_gt);
            expect_value("LT", lt_o, expected_lt);

            expect_value("done pulse", done_o, 1'b1);

            @(posedge clk);
            #1;

            expect_value("done cleared", done_o, 1'b0);
            expect_value("busy cleared", busy_o, 1'b0);
        end
    endtask

    initial begin
        $dumpfile("sim_v45/ifa_yara_pe.vcd");
        $dumpvars(0, tb_ifa_yara_pe);

        tests_run    = 0;
        tests_failed = 0;

        rst_n         = 1'b0;
        start_i       = 1'b0;

        relation_id_i = '0;
        operation_i   = '0;

        operand_a_i   = '0;
        operand_b_i   = '0;

        phi_a_i       = '0;
        phi_b_i       = '0;

        phi_reference_a_i = '0;
        phi_reference_b_i = '0;
        phi_reference_y_i = '0;

        #2;

        expect_value("reset valid", valid_o, 0);
        expect_value("reset done", done_o, 0);
        expect_value("reset busy", busy_o, 0);
        expect_value("reset value", value_o, 0);

        repeat (2) @(posedge clk);
        rst_n = 1'b1;

        // --------------------------------------------------------------------
        // PAPO
        // --------------------------------------------------------------------
        execute_and_check(
            8'h00,
            OP_PAPO,
            8'd2,
            8'd3,
            32'd5,
            8'd5,
            1'b0,
            1'b1
        );

        execute_and_check(
            8'h01,
            OP_PAPO,
            8'd250,
            8'd10,
            32'd260,
            8'd4,
            1'b1,
            1'b1
        );

        // --------------------------------------------------------------------
        // YO
        // --------------------------------------------------------------------
        execute_and_check(
            8'h02,
            OP_YO,
            8'd10,
            8'd4,
            32'd6,
            8'd6,
            1'b0,
            1'b1
        );

        execute_and_check(
            8'h03,
            OP_YO,
            8'd2,
            8'd3,
            32'hFFFFFFFF,
            8'hFF,
            1'b1,
            1'b1
        );

        // --------------------------------------------------------------------
        // DAGBA
        // --------------------------------------------------------------------
        execute_and_check(
            8'h04,
            OP_DAGBA,
            8'd5,
            8'd6,
            32'd30,
            8'd30,
            1'b0,
            1'b1
        );

        execute_and_check(
            8'h05,
            OP_DAGBA,
            8'd11,
            8'd28,
            32'd308,
            8'h34,
            1'b1,
            1'b1
        );

        // --------------------------------------------------------------------
        // PIN
        // --------------------------------------------------------------------
        execute_and_check(
            8'h06,
            OP_PIN,
            8'd20,
            8'd4,
            32'd5,
            8'd5,
            1'b0,
            1'b1
        );

        execute_and_check(
            8'h07,
            OP_PIN,
            8'd20,
            8'd0,
            32'd0,
            8'd0,
            1'b0,
            1'b0
        );

        // --------------------------------------------------------------------
        // KU
        // --------------------------------------------------------------------
        execute_and_check(
            8'h08,
            OP_KU,
            8'd20,
            8'd6,
            32'd2,
            8'd2,
            1'b0,
            1'b1
        );

        execute_and_check(
            8'h09,
            OP_KU,
            8'd20,
            8'd0,
            32'd0,
            8'd0,
            1'b0,
            1'b0
        );

        // --------------------------------------------------------------------
        // GBE
        // --------------------------------------------------------------------
        execute_and_check(
            8'h0A,
            OP_GBE,
            8'd2,
            8'd4,
            32'd16,
            8'd16,
            1'b0,
            1'b1
        );

        execute_and_check(
            8'h0B,
            OP_GBE,
            8'd3,
            8'd6,
            32'd729,
            8'hD9,
            1'b1,
            1'b1
        );

        // --------------------------------------------------------------------
        // Comparisons
        // --------------------------------------------------------------------
        execute_and_check(
            8'h0C,
            OP_SEDA,
            8'd5,
            8'd5,
            32'd1,
            8'd1,
            1'b0,
            1'b1
        );

        execute_and_check(
            8'h0D,
            OP_SEDA,
            8'd5,
            8'd6,
            32'd0,
            8'd0,
            1'b0,
            1'b1
        );

        execute_and_check(
            8'h0E,
            OP_JU,
            8'd8,
            8'd2,
            32'd1,
            8'd1,
            1'b0,
            1'b1
        );

        execute_and_check(
            8'h0F,
            OP_KERE,
            8'd2,
            8'd8,
            32'd1,
            8'd1,
            1'b0,
            1'b1
        );

        // --------------------------------------------------------------------
        // Invalid opcode
        // --------------------------------------------------------------------
        execute_and_check(
            8'h10,
            4'hF,
            8'd7,
            8'd3,
            32'd0,
            8'd0,
            1'b0,
            1'b0
        );

        $display("");
        $display("============================================================");
        $display("IFÁ V4.5 YÀRÁ PE RTL TEST SUMMARY");
        $display("============================================================");
        $display("Tests run    : %0d", tests_run);
        $display("Tests failed : %0d", tests_failed);

        if (tests_failed == 0) begin
            $display("RESULT       : PASS");
            $display("Native YÀRÁ relation computation verified.");
        end
        else begin
            $display("RESULT       : FAIL");

            $fatal(
                1,
                "%0d YÀRÁ PE tests failed.",
                tests_failed
            );
        end

        $finish;
    end

endmodule
