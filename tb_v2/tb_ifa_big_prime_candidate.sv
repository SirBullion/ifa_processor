module tb_ifa_big_prime_candidate;

    logic [31:0] p;
    logic [31:0] delta;

    logic [31:0] exponent;
    logic [31:0] offset;
    logic        valid_delta;
    logic        beats_record;

    ifa_big_prime_candidate dut (
        .p(p),
        .delta(delta),
        .exponent(exponent),
        .offset(offset),
        .valid_delta(valid_delta),
        .beats_record(beats_record)
    );

    initial begin
        $dumpfile("sim_v2/ifa_big_prime_candidate.vcd");
        $dumpvars(0, tb_ifa_big_prime_candidate);

        $display("p          delta   valid_delta beats_record");
        $display("-------------------------------------------");

        // Same record, no offset
        p = 32'd136279841;
        delta = 32'd0;
        #1;
        $display("%0d  %0d       %b           %b",
                 p, delta, valid_delta, beats_record);

        // Same exponent, larger odd candidate form
        p = 32'd136279841;
        delta = 32'd2;
        #1;
        $display("%0d  %0d       %b           %b",
                 p, delta, valid_delta, beats_record);

        // Bad offset: would make even candidate
        p = 32'd136279841;
        delta = 32'd1;
        #1;
        $display("%0d  %0d       %b           %b",
                 p, delta, valid_delta, beats_record);

        // Bigger exponent
        p = 32'd136279842;
        delta = 32'd0;
        #1;
        $display("%0d  %0d       %b           %b",
                 p, delta, valid_delta, beats_record);

        $finish;
    end

endmodule

