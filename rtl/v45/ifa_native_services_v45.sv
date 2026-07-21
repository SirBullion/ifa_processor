`timescale 1ns/1ps

// IFÁ V4.5 native, non-security service projection.
// Converts existing relation-frame bytes and an explicit cast pair into the
// documented four-bit ODÙ identifiers. It performs no operation selection.
module ifa_native_services_v45 (
    input  logic       frame_valid_i,
    input  logic [7:0] y_i,
    input  logic [7:0] ra_i,
    input  logic [7:0] rd_i,
    input  logic [7:0] r0_i,
    input  logic [7:0] t_i,

    input  logic       cast_valid_i,
    input  logic [3:0] cast_right_i,
    input  logic [3:0] cast_left_i,

    output logic       frame_valid_o,
    output logic [3:0] y_high_odu_o,
    output logic [3:0] y_low_odu_o,
    output logic [3:0] ra_high_odu_o,
    output logic [3:0] ra_low_odu_o,
    output logic [3:0] rd_high_odu_o,
    output logic [3:0] rd_low_odu_o,
    output logic [3:0] r0_high_odu_o,
    output logic [3:0] r0_low_odu_o,
    output logic [3:0] t_high_odu_o,
    output logic [3:0] t_low_odu_o,

    output logic       cast_valid_o,
    output logic [3:0] cast_right_odu_o,
    output logic [3:0] cast_left_odu_o
);
    assign frame_valid_o    = frame_valid_i;
    assign y_high_odu_o     = y_i[7:4];
    assign y_low_odu_o      = y_i[3:0];
    assign ra_high_odu_o    = ra_i[7:4];
    assign ra_low_odu_o     = ra_i[3:0];
    assign rd_high_odu_o    = rd_i[7:4];
    assign rd_low_odu_o     = rd_i[3:0];
    assign r0_high_odu_o    = r0_i[7:4];
    assign r0_low_odu_o     = r0_i[3:0];
    assign t_high_odu_o     = t_i[7:4];
    assign t_low_odu_o      = t_i[3:0];
    assign cast_valid_o     = cast_valid_i;
    assign cast_right_odu_o = cast_right_i;
    assign cast_left_odu_o  = cast_left_i;
endmodule
