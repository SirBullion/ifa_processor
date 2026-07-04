`timescale 1ns/1ps

module tb_monitor_uart;

    logic clk = 0;
    logic reset = 1;

    logic uart_rx_line = 1;
    logic uart_tx_line;

    logic debug_out_valid;
    logic [7:0] debug_out_byte;

    integer outfile;

    always #5 clk = ~clk;

    ifa_monitor_uart_top #(.CLKS_PER_BIT(10)) dut (
        .clk(clk),
        .reset(reset),
        .uart_rx_line(uart_rx_line),
        .uart_tx_line(uart_tx_line),
        .debug_out_valid(debug_out_valid),
        .debug_out_byte(debug_out_byte)
    );

    task send_uart_byte(input logic [7:0] b);
        begin
            uart_rx_line <= 0;
            repeat (10) @(posedge clk);

            for (int i=0; i<8; i++) begin
                uart_rx_line <= b[i];
                repeat (10) @(posedge clk);
            end

            uart_rx_line <= 1;
            repeat (10) @(posedge clk);
        end
    endtask

    initial begin
        $dumpfile("sim/monitor_uart.vcd");
        $dumpvars(0, tb_monitor_uart);

        outfile = $fopen("sim/monitor_uart_output.txt", "w");

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

        #50000;

        $fclose(outfile);
        $display("Monitor UART test complete.");
        $finish;
    end

    always @(posedge clk) begin
        if (debug_out_valid) begin
            $write("%c", debug_out_byte);
            $fwrite(outfile, "%c", debug_out_byte);
        end
    end

endmodule
