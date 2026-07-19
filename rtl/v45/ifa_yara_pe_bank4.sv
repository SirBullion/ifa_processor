`timescale 1ns/1ps

// ============================================================================
// IFÁ Processor V4.5
// Four-YÀRÁ Verified Processing-Element Bank
// ============================================================================
//
// Preserves the V4 execution contract:
//
//     execute request
//          |
//          v
//     selected YÀRÁ PE
//          |
//          v
//     universal Relation Frame
//
// Each YÀRÁ owns a physical V4.5 PE containing the exact verified Φ-P8
// implementation.
//
// The V4 operating-system interface remains unchanged. active_yara selects
// which physical PE receives the request.
// ============================================================================

module ifa_yara_pe_bank4 #(
    parameter integer WIDTH        = 8,
    parameter integer OP_WIDTH     = 4,
    parameter integer VALUE_WIDTH  = 32,
    parameter integer MAX_YARA     = 4,
    parameter integer YARA_W =
        (MAX_YARA <= 1) ? 1 : $clog2(MAX_YARA)
)(
    input  logic                    clk,
    input  logic                    rst,

    input  logic                    start_i,
    input  logic [YARA_W-1:0]       active_yara_i,

    input  logic [OP_WIDTH-1:0]     operation_i,
    input  logic [WIDTH-1:0]        operand_a_i,
    input  logic [WIDTH-1:0]        operand_b_i,

    output logic                    busy_o,
    output logic                    done_o,

    output logic [OP_WIDTH-1:0]     operation_o,

    output logic [WIDTH-1:0]        y_o,
    output logic [WIDTH-1:0]        ra_o,
    output logic [WIDTH-1:0]        rd_o,
    output logic [WIDTH-1:0]        r0_o,
    output logic [WIDTH-1:0]        t_o,

    output logic                    operation_valid_o,

    output logic                    exception_valid_o,
    output logic [3:0]              exception_code_o,

    output logic                    state_valid_o,
    output logic [3:0]              state_code_o,

    output logic                    eq_o,
    output logic                    gt_o,
    output logic                    lt_o
);

    localparam logic [OP_WIDTH-1:0] OP_PIN = 4'h3;
    localparam logic [OP_WIDTH-1:0] OP_KU  = 4'h4;

    logic active_yara_valid;

    logic [MAX_YARA-1:0] pe_start;
    logic [MAX_YARA-1:0] pe_busy;
    logic [MAX_YARA-1:0] pe_done;
    logic [MAX_YARA-1:0] pe_transport;
    logic [MAX_YARA-1:0] pe_valid;
    logic [MAX_YARA-1:0] pe_eq;
    logic [MAX_YARA-1:0] pe_gt;
    logic [MAX_YARA-1:0] pe_lt;

    logic [OP_WIDTH-1:0] pe_operation [0:MAX_YARA-1];

    logic [WIDTH-1:0] pe_operand_b [0:MAX_YARA-1];

    logic [WIDTH-1:0] pe_y  [0:MAX_YARA-1];
    logic [WIDTH-1:0] pe_ra [0:MAX_YARA-1];
    logic [WIDTH-1:0] pe_rd [0:MAX_YARA-1];
    logic [WIDTH-1:0] pe_r0 [0:MAX_YARA-1];

    logic [WIDTH-1:0] pe_phi_a [0:MAX_YARA-1];
    logic [WIDTH-1:0] pe_phi_b [0:MAX_YARA-1];
    logic [WIDTH-1:0] pe_phi_y [0:MAX_YARA-1];

    logic [WIDTH-1:0] pe_operand_a [0:MAX_YARA-1];

    logic [VALUE_WIDTH-1:0] pe_value [0:MAX_YARA-1];

    logic selected_transport;
    logic selected_valid;
    logic [WIDTH-1:0] selected_operand_b;

    integer start_index;
    integer select_index;

    initial begin
        if (MAX_YARA != 4) begin
            $display(
                "ERROR: ifa_yara_pe_bank4 requires MAX_YARA=4; received %0d",
                MAX_YARA
            );
            $finish;
        end

        if (WIDTH != 8) begin
            $display(
                "ERROR: exact Φ-P8 V4.5 bank currently requires WIDTH=8"
            );
            $finish;
        end
    end

    always_comb begin
        active_yara_valid = (active_yara_i < MAX_YARA);

        pe_start = '0;

        if (start_i && active_yara_valid) begin
            for (
                start_index = 0;
                start_index < MAX_YARA;
                start_index = start_index + 1
            ) begin
                if (active_yara_i == start_index) begin
                    pe_start[start_index] = 1'b1;
                end
            end
        end
    end

    genvar yara_index;

    generate
        for (
            yara_index = 0;
            yara_index < MAX_YARA;
            yara_index = yara_index + 1
        ) begin : generate_yara_pe

            ifa_yara_pe #(
                .WIDTH        (WIDTH),
                .REL_ID_WIDTH (YARA_W),
                .OP_WIDTH     (OP_WIDTH),
                .VALUE_WIDTH  (VALUE_WIDTH)
            ) physical_pe (
                .clk           (clk),
                .rst_n         (~rst),

                .start_i       (pe_start[yara_index]),

                .relation_id_i (active_yara_i),
                .operation_i   (operation_i),

                .operand_a_i   (operand_a_i),
                .operand_b_i   (operand_b_i),

                // Legacy compatibility ports. The V4.5 PE generates exact
                // Φ-P8 channels internally and ignores these values.
                .phi_a_i       ('0),
                .phi_b_i       ('0),

                .busy_o        (pe_busy[yara_index]),
                .done_o        (pe_done[yara_index]),

                .relation_id_o (),
                .operation_o   (pe_operation[yara_index]),

                .operand_a_o   (pe_operand_a[yara_index]),
                .operand_b_o   (pe_operand_b[yara_index]),

                .phi_a_o       (pe_phi_a[yara_index]),
                .phi_b_o       (pe_phi_b[yara_index]),
                .phi_y_o       (pe_phi_y[yara_index]),

                .y_o           (pe_y[yara_index]),

                .ra_o          (pe_ra[yara_index]),
                .rd_o          (pe_rd[yara_index]),
                .r0_o          (pe_r0[yara_index]),

                .value_o       (pe_value[yara_index]),

                .transport_o   (pe_transport[yara_index]),

                .eq_o          (pe_eq[yara_index]),
                .gt_o          (pe_gt[yara_index]),
                .lt_o          (pe_lt[yara_index]),

                .state_o       (),
                .valid_o       (pe_valid[yara_index])
            );

        end
    endgenerate

    always_comb begin
        busy_o = 1'b0;
        done_o = 1'b0;

        operation_o = '0;

        y_o  = '0;
        ra_o = '0;
        rd_o = '0;
        r0_o = '0;
        t_o  = '0;

        selected_transport = 1'b0;
        selected_valid = 1'b0;
        selected_operand_b = '0;

        eq_o = 1'b0;
        gt_o = 1'b0;
        lt_o = 1'b0;

        if (active_yara_valid) begin
            for (
                select_index = 0;
                select_index < MAX_YARA;
                select_index = select_index + 1
            ) begin
                if (active_yara_i == select_index) begin
                    busy_o = pe_busy[select_index];
                    done_o = pe_done[select_index];

                    operation_o = pe_operation[select_index];

                    y_o  = pe_y[select_index];
                    ra_o = pe_ra[select_index];
                    rd_o = pe_rd[select_index];
                    r0_o = pe_r0[select_index];

                    selected_transport =
                        pe_transport[select_index];

                    selected_valid =
                        pe_valid[select_index];

                    selected_operand_b =
                        pe_operand_b[select_index];

                    eq_o = pe_eq[select_index];
                    gt_o = pe_gt[select_index];
                    lt_o = pe_lt[select_index];
                end
            end
        end

        t_o = {{(WIDTH-1){1'b0}}, selected_transport};

        operation_valid_o =
            done_o && selected_valid;

        exception_valid_o =
            done_o && !selected_valid;

        exception_code_o = 4'h0;

        if (exception_valid_o) begin
            if (
                (
                    operation_o == OP_PIN ||
                    operation_o == OP_KU
                )
                &&
                selected_operand_b == '0
            ) begin
                // Division/remainder relation absent because divisor is zero.
                exception_code_o = 4'h1;
            end
            else begin
                // Unsupported or invalid native operation.
                exception_code_o = 4'hF;
            end
        end

        state_valid_o =
            done_o && selected_valid;

        state_code_o =
            selected_transport ? 4'h1 : 4'h0;
    end

endmodule
