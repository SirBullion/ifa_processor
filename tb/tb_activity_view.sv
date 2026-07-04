`timescale 1ns/1ps

module tb_activity_view;

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

    function string active_blocks;
        string s;
        begin
            s = "";

            // Always fetching when not halted.
            if (!halted)
                s = {s, "FETCH "};

            // Decode active when current instruction is valid.
            if (!reset && !halted)
                s = {s, "DECODE "};

            // Classical ALU style instructions.
            if (
                dut.cpu.core.opcode == 4'h8 || // ADD
                dut.cpu.core.opcode == 4'h9 || // SUB
                dut.cpu.core.opcode == 4'hA || // XOR_IMM
                dut.cpu.core.opcode == 4'hB    // DEC
            )
                s = {s, "ALU "};

            // Ifá processing unit activity.
            if (dut.cpu.core.opcode == 4'h2)
                s = {s, "P8 "};

            if (
                dut.cpu.core.opcode == 4'h3 || // INJECT
                dut.cpu.core.opcode == 4'h4 || // INV_CORRUPT
                dut.cpu.core.opcode == 4'h5 || // CORRECT
                dut.cpu.core.opcode == 4'h6    // FINAL_INV
            )
                s = {s, "RECOVERY "};

            if (dut.cpu.core.printing_odu)
                s = {s, "ODU_STREAM "};

            if (dut.out_valid)
                s = {s, "OUT_BYTE "};

            if (dut.tx_start)
                s = {s, "UART_START "};

            if (dut.tx_busy)
                s = {s, "UART_BUSY "};

            if (halted)
                s = {s, "HALTED "};

            if (s == "")
                s = "IDLE";

            active_blocks = s;
        end
    endfunction

    initial begin
        $dumpfile("sim/activity_view.vcd");
        $dumpvars(0, tb_activity_view);

        $display("");
        $display("==================================================================================================================");
        $display("                                      IFÁ ACTIVITY VIEW");
        $display("==================================================================================================================");
        $display("cycle pc  instr opcode       data     out_byte valid tx_start tx_busy printing_odu odu_pos active_blocks");
        $display("------------------------------------------------------------------------------------------------------------------");

        #20;
        reset = 0;

        while (!halted && cycle_count < 10000) begin
            @(posedge clk);
            cycle_count++;
            #1;

            $display(
                "%5d %03h %04h %-12s %08b %02h      %0b     %0b        %0b       %0b            %02d      %s",
                cycle_count,
                dut.cpu.pc,
                dut.cpu.instr,
                opcode_name(dut.cpu.core.opcode),
                dut.cpu.data_reg,
                dut.out_byte,
                dut.out_valid,
                dut.tx_start,
                dut.tx_busy,
                dut.cpu.core.printing_odu,
                dut.cpu.core.odu_pos,
                active_blocks()
            );
        end

        $display("------------------------------------------------------------------------------------------------------------------");
        $display("HALTED = %0b", halted);
        $display("CYCLES = %0d", cycle_count);
        $display("==================================================================================================================");

        $finish;
    end

endmodule
