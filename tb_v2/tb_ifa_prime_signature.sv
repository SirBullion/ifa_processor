module tb_ifa_prime_signature;

    logic [63:0] candidate;
    logic [63:0] R_A, R_D, R_0;
    logic [6:0]  P_A, P_D, P_0;

    ifa_prime_relation_signature dut (
        .candidate(candidate),
        .R_A(R_A),
        .R_D(R_D),
        .R_0(R_0),
        .P_A(P_A),
        .P_D(P_D),
        .P_0(P_0)
    );

    initial begin
        $dumpfile("sim_v2/ifa_prime_signature.vcd");
        $dumpvars(0, tb_ifa_prime_signature);

        $display("candidate       P_A P_D P_0");
        $display("----------------------------");

        candidate = 64'd4294967311; #1;
        $display("%0d  %0d  %0d  %0d", candidate, P_A, P_D, P_0);

        candidate = 64'd4294967313; #1;
        $display("%0d  %0d  %0d  %0d", candidate, P_A, P_D, P_0);

        candidate = 64'd4294967357; #1;
        $display("%0d  %0d  %0d  %0d", candidate, P_A, P_D, P_0);

        candidate = 64'd17179869143; #1;
        $display("%0d  %0d  %0d  %0d", candidate, P_A, P_D, P_0);

        $finish;
    end

endmodule
