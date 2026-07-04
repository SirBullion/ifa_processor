module tb_ifa_prime_filter;

    logic [63:0] candidate;
    logic divisible_small;
    logic maybe_prime;

    ifa_prime_small_filter dut (
        .candidate(candidate),
        .divisible_small(divisible_small),
        .maybe_prime(maybe_prime)
    );

    initial begin
        $dumpfile("sim_v2/ifa_prime_filter.vcd");
        $dumpvars(0, tb_ifa_prime_filter);

        $display("candidate    divisible_small maybe_prime");
        $display("----------------------------------------");

        candidate = 64'd4294967311; #1;
        $display("%0d        %b              %b", candidate, divisible_small, maybe_prime);

        candidate = 64'd4294967313; #1;
        $display("%0d        %b              %b", candidate, divisible_small, maybe_prime);

        candidate = 64'd4294967357; #1;
        $display("%0d        %b              %b", candidate, divisible_small, maybe_prime);

        candidate = 64'd17179869143; #1;
        $display("%0d       %b              %b", candidate, divisible_small, maybe_prime);

        $finish;
    end

endmodule
