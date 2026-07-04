`timescale 1ns/1ps

module tb_uart_tx;

    logic clk = 0;
    logic reset = 1;

    logic tx_start;
    logic [7:0] tx_data;

    logic tx;
    logic tx_busy;
    logic tx_done;

    always #5 clk = ~clk;

    uart_tx #(
        .CLKS_PER_BIT(10)
    ) dut (
        .clk(clk),
        .reset(reset),
        .tx_start(tx_start),
        .tx_data(tx_data),
        .tx(tx),
        .tx_busy(tx_busy),
        .tx_done(tx_done)
    );

    task send_byte(input logic [7:0] b);
        begin
            @(posedge clk);
            tx_data <= b;
            tx_start <= 1'b1;

            @(posedge clk);
            tx_start <= 1'b0;

            wait(tx_done);
            @(posedge clk);
        end
    endtask

    initial begin
        $dumpfile("sim/uart_tx.vcd");
        $dumpvars(0, tb_uart_tx);

        tx_start = 0;
        tx_data = 8'h00;

        #20;
        reset = 0;

        send_byte("I");
        send_byte("F");
        send_byte("A");

        #100;
        $display("UART TX test complete.");
        $finish;
    end

endmodule
