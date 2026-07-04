`timescale 1ns/1ps

module tb_error_transport;

    logic [7:0] x;
    logic [7:0] y;
    logic [7:0] e;
    logic [7:0] y_corrupt;
    logic [7:0] x_recovered;
    logic [7:0] delta_observed;
    logic [7:0] delta_expected;

    int failures = 0;
    int tests = 0;

    ifa_p8 enc (
        .x(x),
        .y(y)
    );

    ifa_p8_inv dec (
        .y(y_corrupt),
        .x(x_recovered)
    );

    ifa_t8 transport (
        .e(e),
        .delta(delta_expected)
    );

    assign y_corrupt = y ^ e;
    assign delta_observed = x ^ x_recovered;

    initial begin
        $dumpfile("sim/error_transport.vcd");
        $dumpvars(0, tb_error_transport);

        $display("x        y        e        y_err    x_rec    delta_obs delta_exp");
        $display("-------------------------------------------------------------------");

        for (int xi = 0; xi < 256; xi++) begin
            x = xi[7:0];

            for (int k = 0; k < 8; k++) begin
                e = 8'b00000001 << k;
                #1;
                tests++;

                $display(
                    "%08b %08b %08b %08b %08b %08b %08b",
                    x, y, e, y_corrupt, x_recovered,
                    delta_observed, delta_expected
                );

                if (delta_observed !== delta_expected) begin
                    failures++;
                    $display("FAIL: x=%08b k=%0d observed=%08b expected=%08b",
                             x, k, delta_observed, delta_expected);
                end
            end
        end

        $display("-------------------------------------------------------------------");
        $display("Total tests = %0d", tests);
        $display("Error transport failures = %0d", failures);

        if (failures == 0)
            $display("PASS: P^-1(P(x)^e) = x^T(e) for all single-bit errors.");
        else
            $display("FAIL: error transport mismatch detected.");

        $finish;
    end

endmodule
