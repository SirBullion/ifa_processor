`timescale 1ns/1ps

module tb_cpu_uart_top;

    logic clk = 0;
    logic reset = 1;

    logic uart_tx_line;
    logic halted;

    always #5 clk = ~clk;

    ifa_cpu_uart_top #(
        .CLKS_PER_BIT(10)
    ) dut (
        .clk(clk),
        .reset(reset),
        .uart_tx_line(uart_tx_line),
        .halted(halted)
    );

    initial begin
        $dumpfile("sim/cpu_uart.vcd");
        $dumpvars(0, tb_cpu_uart_top);

        #20;
        reset = 0;

        wait(halted);

        // Wait extra time for final UART byte to finish.
        #20000;

        $display("CPU UART simulation complete.");
        $finish;
    end

endmodule
