module ifa_cpu_uart_top #(
    parameter int CLKS_PER_BIT = 10
)(
    input  logic clk,
    input  logic reset,

    output logic uart_tx_line,
    output logic halted
);

    logic [9:0] pc;
    logic [15:0] ir;

    logic [7:0] data_reg;
    logic [7:0] original_reg;
    logic [7:0] encoded_reg;
    logic [7:0] corrupted_reg;
    logic [7:0] recovered_reg;
    logic [7:0] error_reg;
    logic [7:0] delta_reg;
    logic [7:0] corrected_reg;
    logic [7:0] output_reg;
    logic [3:0] output_index;
    logic [127:0] output_buffer_flat;

    logic out_valid;
    logic [7:0] out_byte;

    logic tx_start;
    logic tx_busy;
    logic tx_done;

    logic pending_valid;
    logic [7:0] pending_byte;

    ifa_cpu_rom_top cpu (
        .clk(clk),
        .reset(reset),
        .halted(halted),
        .pc(pc),
        .ir(ir),
        .data_reg(data_reg),
        .original_reg(original_reg),
        .encoded_reg(encoded_reg),
        .corrupted_reg(corrupted_reg),
        .recovered_reg(recovered_reg),
        .error_reg(error_reg),
        .delta_reg(delta_reg),
        .corrected_reg(corrected_reg),
        .output_reg(output_reg),
        .output_index(output_index),
        .output_buffer_flat(output_buffer_flat),
        .out_valid(out_valid),
        .out_byte(out_byte)
    );

    uart_tx #(
        .CLKS_PER_BIT(CLKS_PER_BIT)
    ) tx0 (
        .clk(clk),
        .reset(reset),
        .tx_start(tx_start),
        .tx_data(pending_byte),
        .tx(uart_tx_line),
        .tx_busy(tx_busy),
        .tx_done(tx_done)
    );

    always_ff @(posedge clk) begin
        if (reset) begin
            pending_valid <= 1'b0;
            pending_byte  <= 8'h00;
            tx_start      <= 1'b0;
        end else begin
            tx_start <= 1'b0;

            if (out_valid && !pending_valid) begin
                pending_byte  <= out_byte;
                pending_valid <= 1'b1;
            end

            if (pending_valid && !tx_busy) begin
                tx_start <= 1'b1;
                pending_valid <= 1'b0;
            end
        end
    end

endmodule
