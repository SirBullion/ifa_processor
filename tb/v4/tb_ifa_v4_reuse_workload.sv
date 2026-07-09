`timescale 1ns/1ps

module tb_ifa_v4_reuse_workload;

    localparam WIDTH = 8;
    localparam DEPTH = 16;

    logic clk;
    logic rst;
    logic rpc_valid;

    logic [WIDTH-1:0] rpc_y, rpc_ra, rpc_rd, rpc_r0, rpc_t;

    logic rmu_hit;
    logic rmu_miss;

    logic [WIDTH-1:0] out_y, out_ra, out_rd, out_r0, out_t;

    logic [31:0] hit_count;
    logic [31:0] miss_count;
    logic [31:0] store_count;
    logic [31:0] evict_count;

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

    task automatic send_frame(
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

    integer pass;

    initial begin

        clk = 0;
        rst = 1;
        rpc_valid = 0;

        rpc_y  = 0;
        rpc_ra = 0;
        rpc_rd = 0;
        rpc_r0 = 0;
        rpc_t  = 0;

        repeat(3) @(negedge clk);
        rst = 0;

        $display("=================================================");
        $display("IFÁ V4 REUSE WORKLOAD");
        $display("=================================================");

        for(pass=0; pass<8; pass=pass+1) begin

            send_frame(8'h13,8'h04,8'h0B,8'hF0,8'h03);
            send_frame(8'h0F,8'h00,8'h0F,8'hF0,8'h04);
            send_frame(8'h03,8'h00,8'h03,8'hFC,8'h02);
            send_frame(8'h07,8'h00,8'h07,8'hF8,8'h03);
            send_frame(8'h13,8'h08,8'h03,8'hF4,8'h02);
            send_frame(8'h17,8'h08,8'h07,8'hF0,8'h03);
            send_frame(8'h0B,8'h04,8'h03,8'hF8,8'h02);
            send_frame(8'h09,8'h08,8'h01,8'hF6,8'h01);

        end

        @(posedge clk);

        $display("");
        $display("FINAL COUNTERS");
        $display("-----------------------------------------");
        $display("Hits    : %0d", hit_count);
        $display("Misses  : %0d", miss_count);
        $display("Stores  : %0d", store_count);
        $display("Evicts  : %0d", evict_count);
        $display("-----------------------------------------");
        $display("Hit Rate: %f",
                 (hit_count*1.0)/(hit_count+miss_count));

        if(hit_count > miss_count)
            $display("PASS : RMU successfully reused relation frames.");
        else
            $display("FAIL : Reuse ineffective.");

        $finish;

    end

endmodule
