`timescale 1ns/1ps

// ============================================================================
// IFÁ Processor V4.5
// Native Relation Frame Register
// ============================================================================
//
// Purpose:
//   Stores one complete IFÁ relation frame produced by a YÀRÁ processing
//   element.
//
// Architecture:
//   Binary operands
//       ↓
//   Φ-P8
//       ↓
//   Relation operation
//       ↓
//   RelationFrame register
//       ↓
//   Relation Memory Unit
//
// This module intentionally performs no arithmetic or relation computation.
// It is a synchronous storage boundary equivalent to the Python
// RelationFrame dataclass.
// ============================================================================

module ifa_relation_frame #(
    parameter int WIDTH         = 8,
    parameter int REL_ID_WIDTH  = 8,
    parameter int OP_WIDTH      = 4,
    parameter int VALUE_WIDTH   = WIDTH + 1
) (
    input  logic                     clk,
    input  logic                     rst_n,
    input  logic                     load_i,

    // ------------------------------------------------------------------------
    // Incoming frame identity
    // ------------------------------------------------------------------------
    input  logic [REL_ID_WIDTH-1:0]  relation_id_i,
    input  logic [OP_WIDTH-1:0]      operation_i,

    // ------------------------------------------------------------------------
    // Incoming resolved operands
    // ------------------------------------------------------------------------
    input  logic [WIDTH-1:0]         operand_a_i,
    input  logic [WIDTH-1:0]         operand_b_i,

    // ------------------------------------------------------------------------
    // Incoming Φ-P8 channels
    // ------------------------------------------------------------------------
    input  logic [WIDTH-1:0]         phi_a_i,
    input  logic [WIDTH-1:0]         phi_b_i,
    input  logic [WIDTH-1:0]         phi_y_i,

    // ------------------------------------------------------------------------
    // Incoming result and relation channels
    // ------------------------------------------------------------------------
    input  logic [WIDTH-1:0]         y_i,
    input  logic [WIDTH-1:0]         ra_i,
    input  logic [WIDTH-1:0]         rd_i,
    input  logic [WIDTH-1:0]         r0_i,

    // Full unrestricted result.
    //
    // WIDTH+1 supports one-bit arithmetic transport for the first RTL stage.
    // Larger multiplication support will later use a configurable value width.
    input  logic [VALUE_WIDTH-1:0]   value_i,

    // ------------------------------------------------------------------------
    // Incoming state channels
    // ------------------------------------------------------------------------
    input  logic                     transport_i,
    input  logic                     eq_i,
    input  logic                     gt_i,
    input  logic                     lt_i,
    input  logic                     state_i,
    input  logic                     valid_i,

    // ------------------------------------------------------------------------
    // Stored frame identity
    // ------------------------------------------------------------------------
    output logic [REL_ID_WIDTH-1:0]  relation_id_o,
    output logic [OP_WIDTH-1:0]      operation_o,

    // ------------------------------------------------------------------------
    // Stored operands
    // ------------------------------------------------------------------------
    output logic [WIDTH-1:0]         operand_a_o,
    output logic [WIDTH-1:0]         operand_b_o,

    // ------------------------------------------------------------------------
    // Stored Φ-P8 channels
    // ------------------------------------------------------------------------
    output logic [WIDTH-1:0]         phi_a_o,
    output logic [WIDTH-1:0]         phi_b_o,
    output logic [WIDTH-1:0]         phi_y_o,

    // ------------------------------------------------------------------------
    // Stored result and relation channels
    // ------------------------------------------------------------------------
    output logic [WIDTH-1:0]         y_o,
    output logic [WIDTH-1:0]         ra_o,
    output logic [WIDTH-1:0]         rd_o,
    output logic [WIDTH-1:0]         r0_o,
    output logic [VALUE_WIDTH-1:0]   value_o,

    // ------------------------------------------------------------------------
    // Stored state channels
    // ------------------------------------------------------------------------
    output logic                     transport_o,
    output logic                     eq_o,
    output logic                     gt_o,
    output logic                     lt_o,
    output logic                     state_o,
    output logic                     valid_o
);

    // ------------------------------------------------------------------------
    // Synchronous frame storage
    // ------------------------------------------------------------------------
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            relation_id_o <= '0;
            operation_o   <= '0;

            operand_a_o   <= '0;
            operand_b_o   <= '0;

            phi_a_o       <= '0;
            phi_b_o       <= '0;
            phi_y_o       <= '0;

            y_o           <= '0;
            ra_o          <= '0;
            rd_o          <= '0;
            r0_o          <= '0;
            value_o       <= '0;

            transport_o   <= 1'b0;
            eq_o          <= 1'b0;
            gt_o          <= 1'b0;
            lt_o          <= 1'b0;
            state_o       <= 1'b0;
            valid_o       <= 1'b0;
        end
        else if (load_i) begin
            relation_id_o <= relation_id_i;
            operation_o   <= operation_i;

            operand_a_o   <= operand_a_i;
            operand_b_o   <= operand_b_i;

            phi_a_o       <= phi_a_i;
            phi_b_o       <= phi_b_i;
            phi_y_o       <= phi_y_i;

            y_o           <= y_i;
            ra_o          <= ra_i;
            rd_o          <= rd_i;
            r0_o          <= r0_i;
            value_o       <= value_i;

            transport_o   <= transport_i;
            eq_o          <= eq_i;
            gt_o          <= gt_i;
            lt_o          <= lt_i;
            state_o       <= state_i;
            valid_o       <= valid_i;
        end
    end

endmodule
