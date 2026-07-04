module tb_ifa_prime_sum_4;

    logic [3:0] primes [0:5];

    logic [3:0] A, B;
    logic [3:0] C;
    logic [3:0] R_A, R_D, R_0;
    logic [2:0] P_A, P_D, P_0;
    logic [3:0] T;

    logic [3:0] acc;
    logic [2:0] P_SUM;

    integer i;

    ifa_add_4 add_unit (
        .A(A),
        .B(B),
        .C(C),
        .R_A(),
        .R_D(),
        .T(T)
    );

    ifa_relation_4 rel_unit (
        .A(A),
        .B(B),
        .R_A(R_A),
        .R_D(R_D),
        .R_0(R_0),
        .P_A(P_A),
        .P_D(P_D),
        .P_0(P_0)
    );

    always_comb begin
        P_SUM = P_A + P_D + P_0;
    end

    initial begin
        $dumpfile("sim_v2/ifa_prime_sum_4.vcd");
        $dumpvars(0, tb_ifa_prime_sum_4);

        primes[0] = 4'd2;
        primes[1] = 4'd3;
        primes[2] = 4'd5;
        primes[3] = 4'd7;
        primes[4] = 4'd11;
        primes[5] = 4'd13;

        acc = 4'd0;

        $display("STEP | ACC_IN PRIME | ACC_OUT | R_A  R_D  R_0 | P_A P_D P_0 P_SUM | T");
        $display("----------------------------------------------------------------------------");

        for (i = 0; i < 6; i++) begin
            A = acc;
            B = primes[i];
            #1;

            $display("%0d    |  %2d     %2d  |   %2d    | %b %b %b |  %0d   %0d   %0d    %0d    | %b",
                     i, A, B, C, R_A, R_D, R_0, P_A, P_D, P_0, P_SUM, T);

            if (P_SUM != 3'd4)
                $display("ERROR: population partition failed at step %0d", i);

            acc = C;
            #1;
        end

        $display("----------------------------------------------------------------------------");
        $display("Final ACC = %0d (%b)", acc, acc);

        if (acc == 4'd9)
            $display("STATUS: PASS ✅  sum primes mod16 = 9");
        else
            $display("STATUS: FAIL ❌ expected 9");

        $finish;
    end

endmodule
