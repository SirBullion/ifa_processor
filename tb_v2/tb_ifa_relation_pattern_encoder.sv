`timescale 1ns/1ps

module tb_ifa_relation_pattern_encoder;

    logic [3:0] Y, R_A, R_D, R_0, T;

    logic [1:0] mode;
    logic compressed_valid;

    logic [3:0] Y_store;
    logic [3:0] R_primary;
    logic [3:0] R_secondary;
    logic [3:0] R_delta;

    ifa_relation_pattern_encoder dut (
        .Y(Y),
        .R_A(R_A),
        .R_D(R_D),
        .R_0(R_0),
        .T(T),

        .mode(mode),
        .compressed_valid(compressed_valid),

        .Y_store(Y_store),
        .R_primary(R_primary),
        .R_secondary(R_secondary),
        .R_delta(R_delta)
    );

    task show;
        begin
            $display(
                "Y=%h RA=%h RD=%h R0=%h T=%h | valid=%b mode=%b | Y_store=%h primary=%h secondary=%h delta=%h",
                Y, R_A, R_D, R_0, T,
                compressed_valid, mode,
                Y_store, R_primary, R_secondary, R_delta
            );
        end
    endtask

    initial begin
        $dumpfile("sim_v2/ifa_relation_pattern_encoder.vcd");
        $dumpvars(0, tb_ifa_relation_pattern_encoder);

        $display("MODE 00 = FULL");
        $display("MODE 01 = DELAY_SHARE");
        $display("MODE 10 = RA_RD_SHARE");
        $display("MODE 11 = DELTA");
        $display("------------------------------------------------------------------");

        // Full mode: no clear compression pattern
        Y=4'h3; R_A=4'h4; R_D=4'hB; R_0=4'h0; T=4'hC; #1;
        show();

        // Mode 01: R_D = R_0 = T
        Y=4'h9; R_A=4'h9; R_D=4'h4; R_0=4'h4; T=4'h4; #1;
        show();

        // Mode 01 again
        Y=4'h6; R_A=4'h6; R_D=4'h9; R_0=4'h9; T=4'h9; #1;
        show();

        // Mode 10: R_A = R_D
        Y=4'hA; R_A=4'h5; R_D=4'h5; R_0=4'h0; T=4'hF; #1;
        show();

        // Mode 11: sparse delta
        Y=4'hC; R_A=4'h8; R_D=4'h9; R_0=4'h2; T=4'h7; #1;
        show();

        $finish;
    end

endmodule
