`timescale 1ns/1ps

module tb_ifa_modus_tollens_v2;

    logic clk = 0;
    logic reset = 1;
    logic halted;

    ifa_odu_v2_cpu dut(
        .clk(clk),
        .reset(reset),
        .halted(halted)
    );

    always #5 clk = ~clk;

    integer cycles = 0;

    always @(posedge clk) begin
        if (!reset)
            cycles <= cycles + 1;

        if (dut.print_valid) begin
            $display("[PRINT] cycle=%0d data=0x%02h", cycles, dut.print_data);
        end

        if (halted) begin
            $display("");
            $display("===========================================");
            $display("IFA V2 MODUS TOLLENS");
            $display("===========================================");
            $display("cycles = %0d", cycles);
            $display("pc     = 0x%02h", dut.pc);
            $display("A      = 0x%02h", dut.a_reg);
            $display("B      = 0x%02h", dut.b_reg);
            $display("Y      = 0x%02h", dut.out_y);
            $display("RA     = 0x%02h", dut.out_ra);
            $display("RD     = 0x%02h", dut.out_rd);
            $display("R0     = 0x%02h", dut.out_r0);
            $display("T      = 0x%02h", dut.out_t);
            $display("halted = %0d", halted);
            $display("===========================================");
            $finish;
        end
    end

    initial begin
        $dumpfile("sim/v2/ifa_modus_tollens.vcd");
        $dumpvars(0, tb_ifa_modus_tollens_v2);

        repeat (3) @(posedge clk);
        reset = 0;

        #1000;
        $fatal(1, "Timeout: CPU did not halt");
    end

endmodule
