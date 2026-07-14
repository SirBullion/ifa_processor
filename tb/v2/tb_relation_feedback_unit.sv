`timescale 1ns/1ps

module tb_relation_feedback_unit;

    localparam WIDTH = 8;

    logic [WIDTH-1:0] current_y, current_ra, current_rd, current_r0, current_t;
    logic [WIDTH-1:0] prev_y, prev_ra, prev_rd, prev_r0, prev_t;
    logic [WIDTH-1:0] fb_y, fb_ra, fb_rd, fb_r0, fb_t;

    ifa_relation_feedback_unit #(.WIDTH(WIDTH)) dut (
        .current_y(current_y),
        .current_ra(current_ra),
        .current_rd(current_rd),
        .current_r0(current_r0),
        .current_t(current_t),

        .prev_y(prev_y),
        .prev_ra(prev_ra),
        .prev_rd(prev_rd),
        .prev_r0(prev_r0),
        .prev_t(prev_t),

        .fb_y(fb_y),
        .fb_ra(fb_ra),
        .fb_rd(fb_rd),
        .fb_r0(fb_r0),
        .fb_t(fb_t)
    );

    initial begin
        current_y  = 8'h13;
        current_ra = 8'h04;
        current_rd = 8'h0B;
        current_r0 = 8'hF0;
        current_t  = 8'h18;

        prev_y  = 8'h01;
        prev_ra = 8'h02;
        prev_rd = 8'h03;
        prev_r0 = 8'h04;
        prev_t  = 8'h05;

        #1;

        $display("FEEDBACK UNIT TEST");
        $display("fb_y  = %02h expected %02h", fb_y,  current_y  ^ prev_t);
        $display("fb_ra = %02h expected %02h", fb_ra, current_ra ^ prev_rd);
        $display("fb_rd = %02h expected %02h", fb_rd, current_rd ^ prev_ra);
        $display("fb_r0 = %02h expected %02h", fb_r0, current_r0 ^ prev_y);
        $display("fb_t  = %02h expected %02h", fb_t,  current_t  ^ prev_r0);

        if (fb_y  !== (current_y  ^ prev_t )) $fatal(1, "fb_y mismatch");
        if (fb_ra !== (current_ra ^ prev_rd)) $fatal(1, "fb_ra mismatch");
        if (fb_rd !== (current_rd ^ prev_ra)) $fatal(1, "fb_rd mismatch");
        if (fb_r0 !== (current_r0 ^ prev_y )) $fatal(1, "fb_r0 mismatch");
        if (fb_t  !== (current_t  ^ prev_r0)) $fatal(1, "fb_t mismatch");

        $display("PASS: feedback unit cross-coupled XOR transform verified");
        $finish;
    end

endmodule
