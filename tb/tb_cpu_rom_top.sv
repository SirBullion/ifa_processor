`timescale 1ns/1ps

module tb_cpu_rom_top;

    logic clk = 0;
    logic reset = 1;

    logic halted;
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

    logic [15:0] program_mem [0:1023];
    logic [7:0] expected_mem [0:0];
    logic [7:0] expected_output;

    int cycle_count = 0;
    integer outfile;

    always #5 clk = ~clk;

    ifa_cpu_rom_top dut (
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

    initial begin
        $readmemh("program.hex", program_mem);
        $readmemh("expected.hex", expected_mem);
        expected_output = expected_mem[0];

        outfile = $fopen("sim/odu_all_output.txt", "w");
        if (outfile == 0) begin
            $display("ERROR: could not open sim/odu_all_output.txt");
            $finish;
        end

        $dumpfile("sim/cpu_rom_top.vcd");
        $dumpvars(0, tb_cpu_rom_top);

        $display("time pc ir     data     orig     enc      corrupt  err      delta    corr     rec      out      halted");
        $display("------------------------------------------------------------------------------------------------------");

        #12;
        reset = 0;

        while (!halted) begin
            @(posedge clk);
            cycle_count++;
            #1;

            if (out_valid) begin
                $fwrite(outfile, "%c", out_byte);
            end

            $display(
                "%4t %03h %04h %08b %08b %08b %08b %08b %08b %08b %08b %08b %0b",
                $time, pc, ir,
                data_reg,
                original_reg,
                encoded_reg,
                corrupted_reg,
                error_reg,
                delta_reg,
                corrected_reg,
                recovered_reg,
                output_reg,
                halted
            );
        end

        $fclose(outfile);

        $display("------------------------------------------------------------------------------------------------------");
        $display("CYCLES       = %0d", cycle_count);
        $display("FINAL OUTPUT = %08b", output_reg);
        $display("EXPECTED     = %08b", expected_output);

        $write("OUTPUT BUFFER ASCII = ");
        for (int j = 0; j < output_index; j++) begin
            $write("%c", output_buffer_flat[j*8 +: 8]);
        end
        $write("\n");

        $write("OUTPUT BUFFER HEX   = ");
        for (int j = 0; j < output_index; j++) begin
            $write("%02h ", output_buffer_flat[j*8 +: 8]);
        end
        $write("\n");

        if (output_reg == expected_output)
            $display("PASS: ROM-based Ifa CPU recovered expected program input.");
        else
            $display("FAIL: ROM-based Ifa CPU output mismatch.");

        $finish;
    end

endmodule
