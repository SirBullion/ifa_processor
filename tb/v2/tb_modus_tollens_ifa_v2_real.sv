`timescale 1ns/1ps

module tb_modus_tollens_ifa_v2_real;

    logic clk = 0;
    logic reset = 1;
    logic halted;

    integer cycles = 0;

    ifa_odu_v2_cpu dut (
        .clk(clk),
        .reset(reset),
        .halted(halted)
    );

    always #5 clk = ~clk;

    always @(posedge clk) begin
        if (!reset)
            cycles <= cycles + 1;

        if (halted) begin
            $display("===========================================");
            $display("REAL IFÁ V2 MODUS TOLLENS PROGRAM");
            $display("===========================================");
            $display("cycles = %0d", cycles);
            $display("pc     = 0x%02h", dut.pc);
            $display("ir     = 0x%04h", dut.ir);
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
        $dumpfile("sim/v2/ifa_modus_tollens_real.vcd");
        $dumpvars(0, tb_modus_tollens_ifa_v2_real);

        repeat (3) @(posedge clk);
        reset = 0;

        #2000;
        $fatal(1, "Timeout: IFÁ V2 program did not halt");
    end

endmodule
