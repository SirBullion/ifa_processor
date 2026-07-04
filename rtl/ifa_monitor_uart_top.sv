module ifa_monitor_uart_top #(
    parameter int CLKS_PER_BIT = 10
)(
    input  logic clk,
    input  logic reset,

    input  logic uart_rx_line,
    output logic uart_tx_line,

    output logic debug_out_valid,
    output logic [7:0] debug_out_byte
);

    logic rx_valid;
    logic [7:0] rx_data;

    logic printodu_start;
    logic [7:0] printodu_value;

    logic p_valid;
    logic [7:0] p_byte;
    logic p_ready;
    logic p_busy;

    logic tx_start;
    logic tx_busy;
    logic tx_done;

    uart_rx #(.CLKS_PER_BIT(CLKS_PER_BIT)) rx0 (
        .clk(clk),
        .reset(reset),
        .rx(uart_rx_line),
        .rx_valid(rx_valid),
        .rx_data(rx_data)
    );

    ifa_monitor mon0 (
        .clk(clk),
        .reset(reset),
        .rx_valid(rx_valid),
        .rx_data(rx_data),
        .printodu_start(printodu_start),
        .printodu_value(printodu_value)
    );

    ifa_odu_printer printer0 (
        .clk(clk),
        .reset(reset),
        .start(printodu_start),
        .value(printodu_value),
        .busy(p_busy),
        .out_valid(p_valid),
        .out_byte(p_byte),
        .out_ready(p_ready),
        .done()
    );

    uart_tx #(.CLKS_PER_BIT(CLKS_PER_BIT)) tx0 (
        .clk(clk),
        .reset(reset),
        .tx_start(tx_start),
        .tx_data(p_byte),
        .tx(uart_tx_line),
        .tx_busy(tx_busy),
        .tx_done(tx_done)
    );

    assign p_ready = p_valid && !tx_busy;
    assign tx_start = p_ready;

    assign debug_out_valid = p_ready;
    assign debug_out_byte  = p_byte;

endmodule
