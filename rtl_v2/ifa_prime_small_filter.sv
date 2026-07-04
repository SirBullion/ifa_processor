module ifa_prime_small_filter (
    input  logic [63:0] candidate,

    output logic divisible_small,
    output logic maybe_prime
);

    always_comb begin
        divisible_small =
            (candidate % 64'd3  == 0) ||
            (candidate % 64'd5  == 0) ||
            (candidate % 64'd7  == 0) ||
            (candidate % 64'd11 == 0) ||
            (candidate % 64'd13 == 0) ||
            (candidate % 64'd17 == 0) ||
            (candidate % 64'd19 == 0) ||
            (candidate % 64'd23 == 0) ||
            (candidate % 64'd29 == 0) ||
            (candidate % 64'd31 == 0);

        maybe_prime = ~divisible_small;
    end

endmodule
