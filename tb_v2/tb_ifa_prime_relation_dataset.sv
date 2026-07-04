module tb_ifa_prime_relation_dataset;

    localparam WIDTH = 64;

    logic [WIDTH-1:0] candidate;
    logic [WIDTH-1:0] divisor;

    logic [WIDTH-1:0] R_A, R_D, R_0;
    logic [6:0] P_A, P_D, P_0;
    logic [63:0] remainder;

    integer fd;
    integer ci, di;

    logic [63:0] candidates [0:5];
    logic        is_prime   [0:5];
    logic [63:0] divisors   [0:9];

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
        $dumpfile("sim_v2/ifa_prime_relation_dataset.vcd");
        $dumpvars(0, tb_ifa_prime_relation_dataset);

        candidates[0] = 64'd4294967291;   is_prime[0] = 1'b1;
        candidates[1] = 64'd4294967357;   is_prime[1] = 1'b1;
        candidates[2] = 64'd17179869143;  is_prime[2] = 1'b1;

        candidates[3] = 64'd4294967292;   is_prime[3] = 1'b0;
        candidates[4] = 64'd4294967313;   is_prime[4] = 1'b0;
        candidates[5] = 64'd17179869144;  is_prime[5] = 1'b0;

        divisors[0] = 64'd3;
        divisors[1] = 64'd5;
        divisors[2] = 64'd7;
        divisors[3] = 64'd11;
        divisors[4] = 64'd13;
        divisors[5] = 64'd17;
        divisors[6] = 64'd19;
        divisors[7] = 64'd23;
        divisors[8] = 64'd29;
        divisors[9] = 64'd31;

        fd = $fopen("sim_v2/ifa_prime_relation_dataset.csv", "w");

        $fwrite(fd, "candidate,is_prime,divisor,remainder,divisible,P_A,P_D,P_0,R_A,R_D,R_0\n");

        for (ci = 0; ci < 6; ci++) begin
            for (di = 0; di < 10; di++) begin
                candidate = candidates[ci];
                divisor   = divisors[di];

                #1;

                remainder = candidate % divisor;

                $fwrite(fd, "%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%h,%h,%h\n",
                    candidate,
                    is_prime[ci],
                    divisor,
                    remainder,
                    (remainder == 0),
                    P_A,
                    P_D,
                    P_0,
                    R_A,
                    R_D,
                    R_0
                );
            end
        end

        $fclose(fd);

        $display("Saved: sim_v2/ifa_prime_relation_dataset.csv");
        $finish;
    end

endmodule
