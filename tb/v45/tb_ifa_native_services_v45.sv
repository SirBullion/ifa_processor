`timescale 1ns/1ps

module tb_ifa_native_services_v45;
    logic frame_valid_i, cast_valid_i;
    logic [7:0] y_i, ra_i, rd_i, r0_i, t_i;
    logic [3:0] cast_right_i, cast_left_i;
    logic frame_valid_o, cast_valid_o;
    logic [3:0] y_high_odu_o, y_low_odu_o;
    logic [3:0] ra_high_odu_o, ra_low_odu_o;
    logic [3:0] rd_high_odu_o, rd_low_odu_o;
    logic [3:0] r0_high_odu_o, r0_low_odu_o;
    logic [3:0] t_high_odu_o, t_low_odu_o;
    logic [3:0] cast_right_odu_o, cast_left_odu_o;
    int value, tests_run, tests_failed;

    ifa_native_services_v45 dut (.*);

    task automatic check(input logic condition, input string label);
        tests_run++;
        if (!condition) begin
            tests_failed++;
            $display("FAIL: %s", label);
        end
    endtask

    initial begin
        tests_run = 0;
        tests_failed = 0;
        frame_valid_i = 1'b1;
        cast_valid_i = 1'b1;
        cast_right_i = 4'h3;
        cast_left_i = 4'hC;

        for (value = 0; value < 256; value++) begin
            y_i  = value[7:0];
            ra_i = value[7:0] ^ 8'h11;
            rd_i = value[7:0] ^ 8'h22;
            r0_i = value[7:0] ^ 8'h44;
            t_i  = value[7:0] ^ 8'h88;
            #1;
            check({y_high_odu_o, y_low_odu_o} === y_i, "Y projection");
            check({ra_high_odu_o, ra_low_odu_o} === ra_i, "RA projection");
            check({rd_high_odu_o, rd_low_odu_o} === rd_i, "RD projection");
            check({r0_high_odu_o, r0_low_odu_o} === r0_i, "R0 projection");
            check({t_high_odu_o, t_low_odu_o} === t_i, "T projection");
        end
        check(frame_valid_o === frame_valid_i, "frame valid");
        check(cast_valid_o === cast_valid_i, "cast valid");
        check(cast_right_odu_o === cast_right_i, "cast right");
        check(cast_left_odu_o === cast_left_i, "cast left");

        if (tests_failed == 0)
            $display("PASS: V4.5 native services (%0d checks)", tests_run);
        else
            $display("FAIL: V4.5 native services %0d/%0d failed", tests_failed, tests_run);
        $finish(tests_failed != 0);
    end
endmodule
