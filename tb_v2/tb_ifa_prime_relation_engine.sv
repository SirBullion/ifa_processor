module tb_ifa_prime_relation_engine;

    localparam WIDTH = 64;

    logic [WIDTH-1:0] candidate;
    logic [WIDTH-1:0] divisor;

    logic [WIDTH-1:0] R_A;
    logic [WIDTH-1:0] R_D;
    logic [WIDTH-1:0] R_0;

    logic [6:0] P_A;
    logic [6:0] P_D;
    logic [6:0] P_0;

    ifa_prime_relation_engine #(
        .WIDTH(WIDTH)
    ) dut (
        .candidate(candidate),
        .divisor(divisor),
        .R_A(R_A),
        .R_D(R_D),
        .R_0(R_0),
        .P_A(P_A),
        .P_D(P_D),
        .P_0(P_0)
    );

    initial begin

        $dumpfile("sim_v2/ifa_prime_relation_engine.vcd");
        $dumpvars(0, tb_ifa_prime_relation_engine);

        // Candidate:
        // 4294967357 (survived the small-prime filter)

        candidate = 64'd4294967357;

        $display("---------------------------------------------------------------");
        $display("Candidate = %0d", candidate);
        $display("---------------------------------------------------------------");
        $display("Divisor   P_A  P_D  P_0");
        $display("---------------------------------------------------------------");

        divisor = 64'd3;   #1;
        $display("%3d      %2d   %2d   %2d", divisor,P_A,P_D,P_0);

        divisor = 64'd5;   #1;
        $display("%3d      %2d   %2d   %2d", divisor,P_A,P_D,P_0);

        divisor = 64'd7;   #1;
        $display("%3d      %2d   %2d   %2d", divisor,P_A,P_D,P_0);

        divisor = 64'd11;  #1;
        $display("%3d      %2d   %2d   %2d", divisor,P_A,P_D,P_0);

        divisor = 64'd13;  #1;
        $display("%3d      %2d   %2d   %2d", divisor,P_A,P_D,P_0);

        divisor = 64'd17;  #1;
        $display("%3d      %2d   %2d   %2d", divisor,P_A,P_D,P_0);

        divisor = 64'd19;  #1;
        $display("%3d      %2d   %2d   %2d", divisor,P_A,P_D,P_0);

        divisor = 64'd23;  #1;
        $display("%3d      %2d   %2d   %2d", divisor,P_A,P_D,P_0);

        divisor = 64'd29;  #1;
        $display("%3d      %2d   %2d   %2d", divisor,P_A,P_D,P_0);

        divisor = 64'd31;  #1;
        $display("%3d      %2d   %2d   %2d", divisor,P_A,P_D,P_0);

        $display("---------------------------------------------------------------");

        $finish;

    end

endmodule
