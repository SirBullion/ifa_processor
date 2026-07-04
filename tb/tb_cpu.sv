`timescale 1ns/1ps

module tb_cpu;

    logic clk = 0;
    logic reset = 1;

    logic halted;
    logic [7:0] pc;
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

    always #5 clk = ~clk;

    ifa_cpu dut (
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
        .output_reg(output_reg)
    );

    initial begin
        $dumpfile("sim/cpu.vcd");
        $dumpvars(0, tb_cpu);

        $display("time pc ir     data     orig     enc      corrupt  err      delta    corr     rec      out      halted");
        $display("------------------------------------------------------------------------------------------------------");

        #12;
        reset = 0;

        while (!halted) begin
            @(posedge clk);
            #1;
            $display(
                "%4t %02h %04h %08b %08b %08b %08b %08b %08b %08b %08b %08b %0b",
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

        $display("------------------------------------------------------------------------------------------------------");
        $display("FINAL OUTPUT = %08b", output_reg);
        $display("EXPECTED     = 10100101");

        if (output_reg == 8'hA5)
            $display("PASS: Ifa CPU recovered original address after error correction.");
        else
            $display("FAIL: Ifa CPU output mismatch.");

        $finish;
    end

endmodule
