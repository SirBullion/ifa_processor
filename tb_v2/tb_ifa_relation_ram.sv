`timescale 1ns/1ps

module tb_ifa_relation_ram;

    logic clk;
    logic we;
    logic [3:0] addr;

    logic [3:0] Y_in;
    logic [3:0] R_primary_in;
    logic [3:0] R_secondary_in;
    logic [1:0] mode_in;

    logic [3:0] Y_out;
    logic [3:0] R_primary_out;
    logic [3:0] R_secondary_out;
    logic [1:0] mode_out;

    ifa_relation_ram dut (
        .clk(clk),
        .we(we),
        .addr(addr),

        .Y_in(Y_in),
        .R_primary_in(R_primary_in),
        .R_secondary_in(R_secondary_in),
        .mode_in(mode_in),

        .Y_out(Y_out),
        .R_primary_out(R_primary_out),
        .R_secondary_out(R_secondary_out),
        .mode_out(mode_out)
    );

    always #5 clk = ~clk;

    initial begin
        $dumpfile("sim_v2/ifa_relation_ram.vcd");
        $dumpvars(0, tb_ifa_relation_ram);

        clk = 0;
        we = 0;
        addr = 0;

        // write compressed Ifa RAM line
        Y_in           = 4'h3;
        R_primary_in   = 4'h4;
        R_secondary_in = 4'hB;
        mode_in        = 2'b00;

        #5;
        we = 1;

        #10;
        we = 0;

        #10;

        $display("--------------------------------");
        $display("IFA RELATION RAM READBACK");
        $display("--------------------------------");
        $display("Y           = %h", Y_out);
        $display("R_primary   = %h", R_primary_out);
        $display("R_secondary = %h", R_secondary_out);
        $display("mode        = %b", mode_out);
        $display("--------------------------------");

        $finish;
    end

endmodule
