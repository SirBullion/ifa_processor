`timescale 1ns/1ps

module tb_computer_view;

    logic clk = 0;
    logic reset = 1;

    logic uart_tx_line;
    logic halted;

    int cycle_count = 0;

    always #5 clk = ~clk;

    ifa_cpu_uart_top #(
        .CLKS_PER_BIT(10)
    ) dut (
        .clk(clk),
        .reset(reset),
        .uart_tx_line(uart_tx_line),
        .halted(halted)
    );

    function string opcode_name(input logic [3:0] op);
        case (op)
            4'h0: opcode_name = "NOP";
            4'h1: opcode_name = "LOAD";
            4'h2: opcode_name = "P8";
            4'h3: opcode_name = "INJECT";
            4'h4: opcode_name = "INV_CORRUPT";
            4'h5: opcode_name = "CORRECT";
            4'h6: opcode_name = "FINAL_INV";
            4'h7: opcode_name = "OUT";
            4'h8: opcode_name = "ADD";
            4'h9: opcode_name = "SUB";
            4'hA: opcode_name = "XOR_IMM";
            4'hB: opcode_name = "DEC";
            4'hC: opcode_name = "JMP";
            4'hD: opcode_name = "JZ";
            4'hE: opcode_name = "PRINT_ODU";
            4'hF: opcode_name = "HALT";
            default: opcode_name = "UNKNOWN";
        endcase
    endfunction

    initial begin
        $dumpfile("sim/computer_view.vcd");
        $dumpvars(0, tb_computer_view);

        $display("");
        $display("===============================================================================================================");
        $display("                                      IFÁ COMPUTER VIEW");
        $display("===============================================================================================================");
        $display("cycle pc  fetch  ir     opcode       imm  data     orig     enc      corrupt  delta    corr     out      valid byte");
        $display("----------------------------------------------------------------------------------------------------------------");

        #20;
        reset = 0;

        while (!halted && cycle_count < 5000) begin
            @(posedge clk);
            cycle_count++;
            #1;

            $display(
                "%5d %03h %04h   %04h   %-12s %02h   %08b %08b %08b %08b %08b %08b %08b   %0b     %02h",
                cycle_count,
                dut.cpu.pc,
                dut.cpu.instr,
                dut.cpu.ir,
                opcode_name(dut.cpu.core.opcode),
                dut.cpu.core.imm,
                dut.cpu.data_reg,
                dut.cpu.original_reg,
                dut.cpu.encoded_reg,
                dut.cpu.corrupted_reg,
                dut.cpu.delta_reg,
                dut.cpu.corrected_reg,
                dut.cpu.output_reg,
                dut.out_valid,
                dut.out_byte
            );
        end

        $display("----------------------------------------------------------------------------------------------------------------");
        $display("HALTED = %0b", halted);
        $display("CYCLES = %0d", cycle_count);
        $display("UART TX LINE FINAL = %0b", uart_tx_line);
        $display("===============================================================================================================");

        $finish;
    end

endmodule
