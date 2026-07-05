`timescale 1ns/1ps

module tb_ifa_relation_compressor;

    logic [3:0] Y, R_A, R_D, R_0, T;

    logic       compressed_valid;
    logic [1:0] mode;
    logic [3:0] Y_store;
    logic [3:0] R_primary;
    logic [3:0] R_delay;

    ifa_relation_compressor dut (
        .Y(Y),
        .R_A(R_A),
        .R_D(R_D),
        .R_0(R_0),
        .T(T),
        .compressed_valid(compressed_valid),
        .mode(mode),
        .Y_store(Y_store),
        .R_primary(R_primary),
        .R_delay(R_delay)
    );

    initial begin
        $dumpfile("sim_v2/ifa_relation_compressor.vcd");
        $dumpvars(0, tb_ifa_relation_compressor);

        $display("Y RA RD R0 T | valid mode Y_store R_primary R_delay");

        // Not compressible
        Y=4'h3; R_A=4'h4; R_D=4'hB; R_0=4'h0; T=4'hC; #1;
        $display("%h %h  %h  %h  %h |   %b    %b     %h       %h        %h",
                 Y,R_A,R_D,R_0,T,compressed_valid,mode,Y_store,R_primary,R_delay);

        // Compressible: RD=R0=T=4
        Y=4'h9; R_A=4'h9; R_D=4'h4; R_0=4'h4; T=4'h4; #1;
        $display("%h %h  %h  %h  %h |   %b    %b     %h       %h        %h",
                 Y,R_A,R_D,R_0,T,compressed_valid,mode,Y_store,R_primary,R_delay);

        // Compressible: RD=R0=T=9
        Y=4'h6; R_A=4'h6; R_D=4'h9; R_0=4'h9; T=4'h9; #1;
        $display("%h %h  %h  %h  %h |   %b    %b     %h       %h        %h",
                 Y,R_A,R_D,R_0,T,compressed_valid,mode,Y_store,R_primary,R_delay);

        $finish;
    end

endmodule
