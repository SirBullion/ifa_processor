`timescale 1ns/1ps

module tb_relation_barrel_loop;

logic clk;
logic rst_n;
logic shift_en;

logic [3:0] odu_new_ra;

logic [3:0] Y_rel;

logic [3:0] R_A_mem;
logic [3:0] R_D_mem;
logic [3:0] T_mem;
logic [3:0] R_0_mem;

ifa_relation_barrel_loop dut(

    .clk(clk),
    .rst_n(rst_n),
    .shift_en(shift_en),

    .odu_new_ra(odu_new_ra),

    .Y_rel(Y_rel),

    .R_A_mem(R_A_mem),
    .R_D_mem(R_D_mem),
    .T_mem(T_mem),
    .R_0_mem(R_0_mem)

);

always #5 clk=~clk;

initial begin

    $dumpfile("sim_v2/relation_barrel_loop.vcd");
    $dumpvars(0,tb_relation_barrel_loop);

    clk=0;
    rst_n=0;
    shift_en=0;

    odu_new_ra=4'h2;

    #15;

    rst_n=1;

    repeat(8) begin

        #10;

        shift_en=1;

        #10;

        shift_en=0;

        $display("--------------------------------");
        $display("Y_rel = %h",Y_rel);
        $display("RA=%h RD=%h T=%h R0=%h",
                  R_A_mem,
                  R_D_mem,
                  T_mem,
                  R_0_mem);

    end

    $finish;

end

endmodule
