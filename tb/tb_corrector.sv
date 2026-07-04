`timescale 1ns/1ps

module tb_corrector;

    logic [7:0] x;
    logic [7:0] y;
    logic [7:0] e;
    logic [7:0] y_corrupt;

    logic [7:0] x_recovered_corrupt;
    logic [7:0] delta_observed;

    logic [7:0] error_e_recovered;
    logic [7:0] y_corrected;
    logic [7:0] x_final;

    int tests = 0;
    int failures = 0;

    ifa_p8 enc (
        .x(x),
        .y(y)
    );

    assign y_corrupt = y ^ e;

    ifa_p8_inv dec_corrupt (
        .y(y_corrupt),
        .x(x_recovered_corrupt)
    );

    assign delta_observed = x ^ x_recovered_corrupt;

    ifa_corrector corr (
        .y_corrupt(y_corrupt),
        .delta(delta_observed),
        .error_e(error_e_recovered),
        .y_corrected(y_corrected)
    );

    ifa_p8_inv dec_final (
        .y(y_corrected),
        .x(x_final)
    );

    initial begin
        $dumpfile("sim/corrector.vcd");
        $dumpvars(0, tb_corrector);

        $display("x        y        e        y_err    delta    e_rec    y_corr   x_final");
        $display("------------------------------------------------------------------------");

        for (int xi = 0; xi < 256; xi++) begin
            x = xi[7:0];

            for (int k = 0; k < 8; k++) begin
                e = 8'b00000001 << k;
                #1;
                tests++;

                $display(
                    "%08b %08b %08b %08b %08b %08b %08b %08b",
                    x, y, e, y_corrupt, delta_observed,
                    error_e_recovered, y_corrected, x_final
                );

                if (error_e_recovered !== e || y_corrected !== y || x_final !== x) begin
                    failures++;
                    $display(
                        "FAIL: x=%08b k=%0d e=%08b e_rec=%08b y=%08b y_corr=%08b x_final=%08b",
                        x, k, e, error_e_recovered, y, y_corrected, x_final
                    );
                end
            end
        end

        $display("------------------------------------------------------------------------");
        $display("Total correction tests = %0d", tests);
        $display("Correction failures = %0d", failures);

        if (failures == 0)
            $display("PASS: decoder-assisted correction works for all 2048 single-bit errors.");
        else
            $display("FAIL: correction mismatch detected.");

        $finish;
    end

endmodule
