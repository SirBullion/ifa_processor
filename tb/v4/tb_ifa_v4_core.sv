`timescale 1ns/1ps

module tb_ifa_v4_core;

    localparam WIDTH = 8;
    localparam DEPTH = 4;

    logic clk;
    logic rst;
    logic rpc_valid;

    logic [WIDTH-1:0] rpc_y;
    logic [WIDTH-1:0] rpc_ra;
    logic [WIDTH-1:0] rpc_rd;
    logic [WIDTH-1:0] rpc_r0;
    logic [WIDTH-1:0] rpc_t;

    logic rmu_hit;
    logic rmu_miss;

    logic [WIDTH-1:0] out_y;
    logic [WIDTH-1:0] out_ra;
    logic [WIDTH-1:0] out_rd;
    logic [WIDTH-1:0] out_r0;
    logic [WIDTH-1:0] out_t;
    logic [31:0] hit_count, miss_count, store_count, evict_count;

    ifa_v4_core #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH)
    ) dut (
        .clk(clk),
        .rst(rst),

        .rpc_valid(rpc_valid),

        .rpc_y(rpc_y),
        .rpc_ra(rpc_ra),
        .rpc_rd(rpc_rd),
        .rpc_r0(rpc_r0),
        .rpc_t(rpc_t),

        .rmu_hit(rmu_hit),
        .rmu_miss(rmu_miss),

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

    task automatic send_rpc_frame(
        input [7:0] y,
        input [7:0] ra,
        input [7:0] rd,
        input [7:0] r0,
        input [7:0] t
    );
        begin
            @(negedge clk);
            rpc_valid = 1'b1;
            rpc_y  = y;
            rpc_ra = ra;
            rpc_rd = rd;
            rpc_r0 = r0;
            rpc_t  = t;

            @(negedge clk);
            rpc_valid = 1'b0;
        end
    endtask

    initial begin
        clk = 0;
        rst = 1;
        rpc_valid = 0;

        rpc_y  = 0;
        rpc_ra = 0;
        rpc_rd = 0;
        rpc_r0 = 0;
        rpc_t  = 0;

        repeat (3) @(negedge clk);
        rst = 0;

        $display("==================================================");
        $display("IFÁ V4 CORE WRAPPER TEST");
        $display("==================================================");

        // First access should miss and store incoming frame
        send_rpc_frame(8'h13, 8'h04, 8'h0B, 8'hF0, 8'h03);
        @(posedge clk);

        $display("TEST 1 MISS: hit=%0d miss=%0d out_y=%02h", rmu_hit, rmu_miss, out_y);

        if (rmu_miss !== 1'b1)
            $fatal(1, "Expected MISS on first frame");

        if (out_y !== 8'h13 || out_r0 !== 8'hF0)
            $fatal(1, "MISS should output incoming RPC frame");

        // Same key, different Y/R0 should hit and return stored original frame
        send_rpc_frame(8'hAA, 8'h04, 8'h0B, 8'h55, 8'h03);
        @(posedge clk);

        $display("TEST 2 HIT: hit=%0d miss=%0d out_y=%02h out_r0=%02h",
                 rmu_hit, rmu_miss, out_y, out_r0);

        if (rmu_hit !== 1'b1)
            $fatal(1, "Expected HIT on repeated relation key");

        if (out_y !== 8'h13 || out_r0 !== 8'hF0)
            $fatal(1, "HIT should return stored full relation frame");

        $display("COUNTERS: hits=%0d misses=%0d stores=%0d evicts=%0d",
                 hit_count, miss_count, store_count, evict_count);

        $display("==================================================");
        $display("ALL V4 CORE WRAPPER TESTS PASSED");
        $display("==================================================");

        $finish;
    end

endmodule
