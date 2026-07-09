`timescale 1ns/1ps

module tb_ifa_v4_end_to_end_core;

    localparam WIDTH = 8;
    localparam DEPTH = 16;

    logic clk;
    logic rst;
    logic in_valid;

    logic [WIDTH-1:0] A;
    logic [WIDTH-1:0] B;

    logic rmu_hit;
    logic rmu_miss;

    logic [WIDTH-1:0] out_y;
    logic [WIDTH-1:0] out_ra;
    logic [WIDTH-1:0] out_rd;
    logic [WIDTH-1:0] out_r0;
    logic [WIDTH-1:0] out_t;

    logic [31:0] hit_count;
    logic [31:0] miss_count;
    logic [31:0] store_count;
    logic [31:0] evict_count;

    ifa_v4_end_to_end_core #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH)
    ) dut (
        .clk(clk),
        .rst(rst),

        .in_valid(in_valid),
        .A(A),
        .B(B),

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

    task automatic send_operands(
        input [7:0] a,
        input [7:0] b
    );
    begin
        @(negedge clk);
        in_valid = 1'b1;
        A = a;
        B = b;

        @(negedge clk);
        in_valid = 1'b0;
    end
    endtask

    initial begin
        clk = 0;
        rst = 1;
        in_valid = 0;
        A = 0;
        B = 0;

        repeat(3) @(negedge clk);
        rst = 0;

        $display("==================================================");
        $display("IFÁ V4 END-TO-END CORE TEST");
        $display("A,B → RPC → RMU → OUTPUT");
        $display("==================================================");

        send_operands(8'h0D, 8'h06);
        @(posedge clk);

        $display("TEST 1 MISS: A=0D B=06 hit=%0d miss=%0d Y=%02h RA=%02h RD=%02h R0=%02h T=%02h",
                 rmu_hit, rmu_miss, out_y, out_ra, out_rd, out_r0, out_t);

        if (rmu_miss !== 1'b1)
            $fatal(1, "Expected MISS on first operand pair");

        if (out_y !== 8'h13)
            $fatal(1, "Expected Y=0x13");

        send_operands(8'h0D, 8'h06);
        @(posedge clk);

        $display("TEST 2 HIT: A=0D B=06 hit=%0d miss=%0d Y=%02h RA=%02h RD=%02h R0=%02h T=%02h",
                 rmu_hit, rmu_miss, out_y, out_ra, out_rd, out_r0, out_t);

        if (rmu_hit !== 1'b1)
            $fatal(1, "Expected HIT on repeated operand pair");

        // Reuse workload
        repeat(4) begin
            send_operands(8'h0D, 8'h06);
            send_operands(8'h07, 8'h08);
            send_operands(8'h01, 8'h02);
            send_operands(8'h03, 8'h04);
            send_operands(8'h09, 8'h0A);
            send_operands(8'h0B, 8'h0C);
            send_operands(8'h0F, 8'h00);
            send_operands(8'h05, 8'h06);
        end

        @(posedge clk);

        $display("");
        $display("COUNTERS: hits=%0d misses=%0d stores=%0d evicts=%0d",
                 hit_count, miss_count, store_count, evict_count);

        if (hit_count <= miss_count)
            $fatal(1, "Expected more hits than misses");

        $display("==================================================");
        $display("ALL V4 END-TO-END CORE TESTS PASSED");
        $display("==================================================");

        $finish;
    end

endmodule
