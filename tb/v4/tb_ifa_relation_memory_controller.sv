//======================================================================
// Testbench: IFÁ V4 Relation Memory Controller
//======================================================================

`timescale 1ns/1ps

module tb_ifa_relation_memory_controller;

    localparam WIDTH = 8;
    localparam DEPTH = 4;

    logic clk;
    logic rst;
    logic req_valid;

    logic [WIDTH-1:0] in_y, in_ra, in_rd, in_r0, in_t;
    logic hit, miss;
    logic [WIDTH-1:0] out_y, out_ra, out_rd, out_r0, out_t;
    logic [31:0] hit_count, miss_count, store_count, evict_count;

    ifa_relation_memory_controller #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH)
    ) dut (
        .clk(clk),
        .rst(rst),
        .req_valid(req_valid),
        .in_y(in_y),
        .in_ra(in_ra),
        .in_rd(in_rd),
        .in_r0(in_r0),
        .in_t(in_t),
        .hit(hit),
        .miss(miss),
        .out_y(out_y),
        .out_ra(out_ra),
        .out_rd(out_rd),
        .out_r0(out_r0),
        .out_t(out_t),

        .hit_count(hit_count),
        .miss_count(miss_count),
        .store_count(store_count),
        .evict_count(evict_count)
    );

    always #5 clk = ~clk;

    task automatic send_frame(
        input [7:0] y,
        input [7:0] ra,
        input [7:0] rd,
        input [7:0] r0,
        input [7:0] t
    );
        begin
            @(negedge clk);
            req_valid = 1'b1;
            in_y  = y;
            in_ra = ra;
            in_rd = rd;
            in_r0 = r0;
            in_t  = t;

            @(negedge clk);
            req_valid = 1'b0;
        end
    endtask

    initial begin
        clk = 0;
        rst = 1;
        req_valid = 0;

        in_y  = 0;
        in_ra = 0;
        in_rd = 0;
        in_r0 = 0;
        in_t  = 0;

        repeat (3) @(negedge clk);
        rst = 0;

        $display("==================================================");
        $display("IFÁ V4 RELATION MEMORY CONTROLLER TEST");
        $display("==================================================");

        // MISS: first frame
        send_frame(8'h13, 8'h04, 8'h0B, 8'hF0, 8'h03);
        @(posedge clk);
        $display("TEST 1 MISS: hit=%0d miss=%0d out_y=%02h", hit, miss, out_y);

        if (miss !== 1'b1) begin
            $fatal(1, "Expected MISS on first insert");
        end

        // HIT: same key {RA,RD,T}, different incoming Y/R0 should return stored frame
        send_frame(8'hAA, 8'h04, 8'h0B, 8'h55, 8'h03);
        @(posedge clk);
        $display("TEST 2 HIT: hit=%0d miss=%0d out_y=%02h out_r0=%02h", hit, miss, out_y, out_r0);

        if (hit !== 1'b1) begin
            $fatal(1, "Expected HIT on repeated key");
        end

        if (out_y !== 8'h13 || out_r0 !== 8'hF0) begin
            $fatal(1, "Hit did not return stored full frame");
        end

        // Fill FIFO depth
        send_frame(8'h21, 8'h01, 8'h02, 8'hFC, 8'h01);
        send_frame(8'h22, 8'h02, 8'h03, 8'hF8, 8'h02);
        send_frame(8'h23, 8'h03, 8'h04, 8'hF4, 8'h03);

        // This should evict oldest entry at FIFO wrap
        send_frame(8'h24, 8'h04, 8'h05, 8'hF2, 8'h04);

        // Oldest first key should now be evicted, so this becomes MISS again
        send_frame(8'h13, 8'h04, 8'h0B, 8'hF0, 8'h03);
        @(posedge clk);

        $display("TEST 3 FIFO EVICTION: hit=%0d miss=%0d", hit, miss);

        if (miss !== 1'b1) begin
            $fatal(1, "Expected MISS after FIFO eviction");
        end

        $display("COUNTERS: hits=%0d misses=%0d stores=%0d evicts=%0d",
                 hit_count, miss_count, store_count, evict_count);

        $display("==================================================");
        $display("ALL V4 RMC RTL TESTS PASSED");
        $display("==================================================");

        $finish;
    end

endmodule
