`timescale 1ns/1ps

module tb_uart_rx;

    logic clk = 0;
    logic reset = 1;
    logic rx = 1;

    logic rx_valid;
    logic [7:0] rx_data;

    always #5 clk = ~clk;

    uart_rx #(
        .CLKS_PER_BIT(10)
    ) dut (
        .clk(clk),
        .reset(reset),
        .rx(rx),
        .rx_valid(rx_valid),
        .rx_data(rx_data)
    );

    task send_uart_byte(input logic [7:0] b);
        begin
            // start bit
            rx <= 1'b0;
            repeat (10) @(posedge clk);

            // data bits, LSB first
            for (int i = 0; i < 8; i++) begin
                rx <= b[i];
                repeat (10) @(posedge clk);
            end

            // stop bit
            rx <= 1'b1;
            repeat (10) @(posedge clk);
        end
    endtask

    initial begin
        $dumpfile("sim/uart_rx.vcd");
        $dumpvars(0, tb_uart_rx);

        #20;
        reset = 0;

        send_uart_byte("P");
        send_uart_byte("R");
        send_uart_byte("I");
        send_uart_byte("N");
        send_uart_byte("T");
        send_uart_byte("O");
        send_uart_byte("D");
        send_uart_byte("U");
        send_uart_byte(" ");
        send_uart_byte("A");
        send_uart_byte("5");
        send_uart_byte(8'h0A);

        #200;
        $display("UART RX test complete.");
        $finish;
    end

    always @(posedge clk) begin
        if (rx_valid)
            $display("RX BYTE: %02h '%c'", rx_data, rx_data);
    end

endmodule
