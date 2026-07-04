module tb_ifa_relation_pop_4;

    logic [3:0] A, B;
    logic [3:0] R_A, R_D, R_0;
    logic [2:0] P_A, P_D, P_0;
    logic [2:0] P_SUM;

    integer a, b;

    ifa_relation_4 dut (
        .A(A),
        .B(B),
        .R_A(R_A),
        .R_D(R_D),
        .R_0(R_0),
        .P_A(P_A),
        .P_D(P_D),
        .P_0(P_0)
    );

    assign P_SUM = P_A + P_D + P_0;

    initial begin
        $dumpfile("sim_v2/ifa_relation_pop_4.vcd");
        $dumpvars(0, tb_ifa_relation_pop_4);

        for (a = 0; a < 16; a++) begin
            for (b = 0; b < 16; b++) begin
                A = a[3:0];
                B = b[3:0];
                #1;
            end
        end

        $finish;
    end

endmodule
