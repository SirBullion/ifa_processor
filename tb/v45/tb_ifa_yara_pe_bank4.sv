`timescale 1ns/1ps

// ============================================================================
// IFÁ Processor V4.5
// Four-YÀRÁ Physical PE Bank Verification
// ============================================================================
//
// Verifies:
//
//   - active_yara dispatches requests to PE0, PE1, PE2 and PE3
//   - each PE computes the correct universal Relation Frame
//   - each PE retains its own independent result
//   - selecting another YÀRÁ does not overwrite existing PE state
//   - transport and STATE propagate correctly
//   - invalid operations remain local to the selected PE
//   - division by zero produces the expected exception
//
// The V4 operating-system interface is unchanged. This test verifies the
// internal V4.5 execution-bank upgrade only.
// ============================================================================

module tb_ifa_yara_pe_bank4;

    localparam integer WIDTH       = 8;
    localparam integer OP_WIDTH    = 4;
    localparam integer VALUE_WIDTH = 32;
    localparam integer MAX_YARA    = 4;
    localparam integer YARA_W      = 2;

    localparam logic [OP_WIDTH-1:0] OP_PAPO  = 4'h0;
    localparam logic [OP_WIDTH-1:0] OP_YO    = 4'h1;
    localparam logic [OP_WIDTH-1:0] OP_DAGBA = 4'h2;
    localparam logic [OP_WIDTH-1:0] OP_PIN   = 4'h3;
    localparam logic [OP_WIDTH-1:0] OP_KU    = 4'h4;
    localparam logic [OP_WIDTH-1:0] OP_GBE   = 4'h5;
    localparam logic [OP_WIDTH-1:0] OP_SEDA  = 4'h6;
    localparam logic [OP_WIDTH-1:0] OP_JU    = 4'h7;
    localparam logic [OP_WIDTH-1:0] OP_KERE  = 4'h8;

    logic clk;
    logic rst;

    logic start_i;
    logic [YARA_W-1:0] active_yara_i;

    logic [OP_WIDTH-1:0] operation_i;
    logic [WIDTH-1:0] operand_a_i;
    logic [WIDTH-1:0] operand_b_i;

    logic busy_o;
    logic done_o;

    logic [OP_WIDTH-1:0] operation_o;

    logic [WIDTH-1:0] y_o;
    logic [WIDTH-1:0] ra_o;
    logic [WIDTH-1:0] rd_o;
    logic [WIDTH-1:0] r0_o;
    logic [WIDTH-1:0] t_o;

    logic operation_valid_o;

    logic exception_valid_o;
    logic [3:0] exception_code_o;

    logic state_valid_o;
    logic [3:0] state_code_o;

    logic eq_o;
    logic gt_o;
    logic lt_o;

    integer tests_run;
    integer tests_failed;

    // Stored expected result for each physical PE.
    logic [OP_WIDTH-1:0] saved_operation [0:MAX_YARA-1];
    logic [WIDTH-1:0] saved_y  [0:MAX_YARA-1];
    logic [WIDTH-1:0] saved_ra [0:MAX_YARA-1];
    logic [WIDTH-1:0] saved_rd [0:MAX_YARA-1];
    logic [WIDTH-1:0] saved_r0 [0:MAX_YARA-1];
    logic [WIDTH-1:0] saved_t  [0:MAX_YARA-1];

    ifa_yara_pe_bank4 #(
        .WIDTH       (WIDTH),
        .OP_WIDTH    (OP_WIDTH),
        .VALUE_WIDTH (VALUE_WIDTH),
        .MAX_YARA    (MAX_YARA),
        .YARA_W      (YARA_W)
    ) dut (
        .clk               (clk),
        .rst               (rst),

        .start_i           (start_i),
        .active_yara_i     (active_yara_i),

        .operation_i       (operation_i),
        .operand_a_i       (operand_a_i),
        .operand_b_i       (operand_b_i),

        .busy_o            (busy_o),
        .done_o            (done_o),

        .operation_o       (operation_o),

        .y_o               (y_o),
        .ra_o              (ra_o),
        .rd_o              (rd_o),
        .r0_o              (r0_o),
        .t_o               (t_o),

        .operation_valid_o (operation_valid_o),

        .exception_valid_o (exception_valid_o),
        .exception_code_o  (exception_code_o),

        .state_valid_o     (state_valid_o),
        .state_code_o      (state_code_o),

        .eq_o              (eq_o),
        .gt_o              (gt_o),
        .lt_o              (lt_o)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    task automatic expect_value(
        input string name,
        input logic [63:0] actual,
        input logic [63:0] expected
    );
        begin
            tests_run = tests_run + 1;

            if (actual !== expected) begin
                tests_failed = tests_failed + 1;

                $display(
                    "FAIL: %-30s actual=0x%0h expected=0x%0h",
                    name,
                    actual,
                    expected
                );
            end
            else begin
                $display(
                    "PASS: %-30s value=0x%0h",
                    name,
                    actual
                );
            end
        end
    endtask

    task automatic execute_and_check(
        input logic [YARA_W-1:0] yara,
        input logic [OP_WIDTH-1:0] operation,
        input logic [WIDTH-1:0] a,
        input logic [WIDTH-1:0] b,

        input logic [WIDTH-1:0] expected_y,
        input logic expected_transport,
        input logic expected_valid,

        input logic expected_exception,
        input logic [3:0] expected_exception_code
    );
        logic [WIDTH-1:0] expected_ra;
        logic [WIDTH-1:0] expected_rd;
        logic [WIDTH-1:0] expected_r0;

        logic expected_eq;
        logic expected_gt;
        logic expected_lt;

        begin
            expected_ra = a & b;
            expected_rd = a ^ b;
            expected_r0 = ~(a | b);

            expected_eq = (a == b);
            expected_gt = (a > b);
            expected_lt = (a < b);

            $display("");
            $display(
                "---- Execute YÀRÁ %0d OP=0x%0h A=0x%02h B=0x%02h ----",
                yara,
                operation,
                a,
                b
            );

            @(negedge clk);

            active_yara_i = yara;
            operation_i   = operation;
            operand_a_i   = a;
            operand_b_i   = b;
            start_i       = 1'b1;

            @(posedge clk);
            #1;

            start_i = 1'b0;

            expect_value("selected YÀRÁ", active_yara_i, yara);
            expect_value("busy asserted", busy_o, 1'b1);
            expect_value("done asserted", done_o, 1'b1);
            expect_value("operation output", operation_o, operation);

            expect_value("Y", y_o, expected_y);
            expect_value("RA", ra_o, expected_ra);
            expect_value("RD", rd_o, expected_rd);
            expect_value("R0", r0_o, expected_r0);

            expect_value(
                "relation partition complete",
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

            expect_value(
                "transport frame T",
                t_o,
                expected_transport ? 8'h01 : 8'h00
            );

            expect_value(
                "operation valid",
                operation_valid_o,
                expected_valid
            );

            expect_value(
                "exception valid",
                exception_valid_o,
                expected_exception
            );

            expect_value(
                "exception code",
                exception_code_o,
                expected_exception_code
            );

            expect_value(
                "state valid",
                state_valid_o,
                expected_valid
            );

            expect_value(
                "state code",
                state_code_o,
                expected_transport ? 4'h1 : 4'h0
            );

            expect_value("EQ", eq_o, expected_eq);
            expect_value("GT", gt_o, expected_gt);
            expect_value("LT", lt_o, expected_lt);

            if (expected_valid) begin
                saved_operation[yara] = operation;
                saved_y[yara]         = expected_y;
                saved_ra[yara]        = expected_ra;
                saved_rd[yara]        = expected_rd;
                saved_r0[yara]        = expected_r0;
                saved_t[yara] =
                    expected_transport ? 8'h01 : 8'h00;
            end

            @(posedge clk);
            #1;

            expect_value("done cleared", done_o, 1'b0);
            expect_value("busy cleared", busy_o, 1'b0);
            expect_value("valid pulse cleared", operation_valid_o, 1'b0);
            expect_value("state pulse cleared", state_valid_o, 1'b0);
            expect_value("exception pulse cleared", exception_valid_o, 1'b0);
        end
    endtask

    task automatic check_retained_frame(
        input logic [YARA_W-1:0] yara
    );
        begin
            $display("");
            $display(
                "---- Re-select retained physical PE%0d frame ----",
                yara
            );

            @(negedge clk);

            active_yara_i = yara;
            start_i       = 1'b0;

            #1;

            expect_value(
                "retained operation",
                operation_o,
                saved_operation[yara]
            );

            expect_value(
                "retained Y",
                y_o,
                saved_y[yara]
            );

            expect_value(
                "retained RA",
                ra_o,
                saved_ra[yara]
            );

            expect_value(
                "retained RD",
                rd_o,
                saved_rd[yara]
            );

            expect_value(
                "retained R0",
                r0_o,
                saved_r0[yara]
            );

            expect_value(
                "retained T",
                t_o,
                saved_t[yara]
            );

            expect_value(
                "no new done pulse",
                done_o,
                1'b0
            );

            expect_value(
                "no new valid pulse",
                operation_valid_o,
                1'b0
            );
        end
    endtask

    integer init_index;

    initial begin
        $dumpfile("sim_v45/ifa_yara_pe_bank4.vcd");
        $dumpvars(0, tb_ifa_yara_pe_bank4);

        tests_run    = 0;
        tests_failed = 0;

        rst           = 1'b1;
        start_i       = 1'b0;
        active_yara_i = 2'd0;

        operation_i = '0;
        operand_a_i = '0;
        operand_b_i = '0;

        for (
            init_index = 0;
            init_index < MAX_YARA;
            init_index = init_index + 1
        ) begin
            saved_operation[init_index] = '0;
            saved_y[init_index]         = '0;
            saved_ra[init_index]        = '0;
            saved_rd[init_index]        = '0;
            saved_r0[init_index]        = '0;
            saved_t[init_index]         = '0;
        end

        #2;

        expect_value("reset busy", busy_o, 1'b0);
        expect_value("reset done", done_o, 1'b0);
        expect_value("reset valid", operation_valid_o, 1'b0);
        expect_value("reset exception", exception_valid_o, 1'b0);

        repeat (2) @(posedge clk);
        rst = 1'b0;

        // --------------------------------------------------------------------
        // One independent operation for each physical YÀRÁ PE.
        // --------------------------------------------------------------------

        // PE0: 2 + 3 = 5
        execute_and_check(
            2'd0,
            OP_PAPO,
            8'd2,
            8'd3,
            8'd5,
            1'b0,
            1'b1,
            1'b0,
            4'h0
        );

        // PE1: 10 - 4 = 6
        execute_and_check(
            2'd1,
            OP_YO,
            8'd10,
            8'd4,
            8'd6,
            1'b0,
            1'b1,
            1'b0,
            4'h0
        );

        // PE2: 11 * 28 = 308 -> Y=0x34 and T=1
        execute_and_check(
            2'd2,
            OP_DAGBA,
            8'd11,
            8'd28,
            8'h34,
            1'b1,
            1'b1,
            1'b0,
            4'h0
        );

        // PE3: 81 / 9 = 9
        execute_and_check(
            2'd3,
            OP_PIN,
            8'd81,
            8'd9,
            8'd9,
            1'b0,
            1'b1,
            1'b0,
            4'h0
        );

        // --------------------------------------------------------------------
        // Re-select every physical PE and prove independent frame retention.
        // --------------------------------------------------------------------

        check_retained_frame(2'd0);
        check_retained_frame(2'd1);
        check_retained_frame(2'd2);
        check_retained_frame(2'd3);

        // --------------------------------------------------------------------
        // Additional operation coverage.
        // --------------------------------------------------------------------

        // Equality in PE0.
        execute_and_check(
            2'd0,
            OP_SEDA,
            8'd25,
            8'd25,
            8'd1,
            1'b0,
            1'b1,
            1'b0,
            4'h0
        );

        // Greater-than in PE1.
        execute_and_check(
            2'd1,
            OP_JU,
            8'd90,
            8'd12,
            8'd1,
            1'b0,
            1'b1,
            1'b0,
            4'h0
        );

        // Less-than in PE2.
        execute_and_check(
            2'd2,
            OP_KERE,
            8'd4,
            8'd19,
            8'd1,
            1'b0,
            1'b1,
            1'b0,
            4'h0
        );

        // --------------------------------------------------------------------
        // Local exception verification.
        // --------------------------------------------------------------------

        // Division by zero in PE3.
        execute_and_check(
            2'd3,
            OP_PIN,
            8'd81,
            8'd0,
            8'd0,
            1'b0,
            1'b0,
            1'b1,
            4'h1
        );

        // Unsupported operation in PE2.
        execute_and_check(
            2'd2,
            4'hF,
            8'd7,
            8'd3,
            8'd0,
            1'b0,
            1'b0,
            1'b1,
            4'hF
        );

        $display("");
        $display("============================================================");
        $display("IFÁ V4.5 FOUR-YÀRÁ PE BANK TEST SUMMARY");
        $display("============================================================");
        $display("Physical PEs tested : 4");
        $display("Tests run           : %0d", tests_run);
        $display("Tests failed        : %0d", tests_failed);

        if (tests_failed == 0) begin
            $display("RESULT              : PASS");
            $display(
                "PE0, PE1, PE2 and PE3 dispatch and isolation verified."
            );
        end
        else begin
            $display("RESULT              : FAIL");

            $fatal(
                1,
                "%0d four-YÀRÁ PE-bank tests failed.",
                tests_failed
            );
        end

        $finish;
    end

endmodule
