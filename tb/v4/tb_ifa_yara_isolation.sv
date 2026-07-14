`timescale 1ns/1ps

module tb_ifa_yara_isolation;

    localparam WIDTH = 8;
    localparam DEPTH = 16;
    localparam YARA_COUNT = 2;

    logic clk;
    logic rst;

    logic [$clog2(YARA_COUNT)-1:0] active_yara;
    logic in_valid;

    logic [WIDTH-1:0] A;
    logic [WIDTH-1:0] B;

    logic [YARA_COUNT-1:0] clear_yara;

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

    logic [31:0] yara0_hit_count;
    logic [31:0] yara0_miss_count;
    logic [31:0] yara1_hit_count;
    logic [31:0] yara1_miss_count;

    ifa_yara_v4_core #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH),
        .YARA_COUNT(YARA_COUNT)
    ) dut (
        .clk(clk),
        .rst(rst),

        .active_yara(active_yara),

        .in_valid(in_valid),
        .A(A),
        .B(B),

        .clear_yara(clear_yara),

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
        .evict_count(evict_count),

        .yara0_hit_count(yara0_hit_count),
        .yara0_miss_count(yara0_miss_count),
        .yara1_hit_count(yara1_hit_count),
        .yara1_miss_count(yara1_miss_count)
    );

    always #5 clk = ~clk;

    task automatic execute_relation(
        input logic yara,
        input logic [7:0] a,
        input logic [7:0] b
    );
    begin
        @(negedge clk);
        active_yara = yara;
        A = a;
        B = b;
        in_valid = 1'b1;

        @(negedge clk);
        in_valid = 1'b0;

        // Sample registered hit/miss result without race.
        #1;

        $display("YARA=%0d A=%02h B=%02h | hit=%0d miss=%0d | Y=%02h RA=%02h RD=%02h R0=%02h T=%02h",
                 yara, a, b, rmu_hit, rmu_miss,
                 out_y, out_ra, out_rd, out_r0, out_t);
    end
    endtask

    task automatic clear_room(input logic yara);
    begin
        @(negedge clk);
        clear_yara = '0;
        clear_yara[yara] = 1'b1;

        @(negedge clk);
        clear_yara = '0;

        #1;
        $display("CLEARED YARA %0d", yara);
    end
    endtask

    initial begin
        $dumpfile("sim/v4/ifa_yara_isolation.vcd");
        $dumpvars(0, tb_ifa_yara_isolation);

        clk = 0;
        rst = 1;

        active_yara = 0;
        in_valid = 0;

        A = 0;
        B = 0;

        clear_yara = '0;

        repeat (3) @(negedge clk);
        rst = 0;

        $display("============================================================");
        $display("IFÁ V4 YÀRÁ ISOLATION TEST");
        $display("Isolation by local RMU namespace");
        $display("============================================================");

        // ---------------------------------------------------------
        // YÀRÁ 0: first access MISS, second access HIT
        // ---------------------------------------------------------

        execute_relation(0, 8'h0D, 8'h06);

        if (rmu_miss !== 1'b1)
            $fatal(1, "YARA 0 first access should MISS");

        execute_relation(0, 8'h0D, 8'h06);

        if (rmu_hit !== 1'b1)
            $fatal(1, "YARA 0 second access should HIT");

        // ---------------------------------------------------------
        // Same relation in YÀRÁ 1 must still MISS.
        // This proves there was no cross-room reuse.
        // ---------------------------------------------------------

        execute_relation(1, 8'h0D, 8'h06);

        if (rmu_miss !== 1'b1)
            $fatal(1, "YARA 1 first access must MISS");

        execute_relation(1, 8'h0D, 8'h06);

        if (rmu_hit !== 1'b1)
            $fatal(1, "YARA 1 second access should HIT");

        // ---------------------------------------------------------
        // Clear only YÀRÁ 0
        // ---------------------------------------------------------

        clear_room(0);

        // YÀRÁ 0 must MISS after its local clear.
        execute_relation(0, 8'h0D, 8'h06);

        if (rmu_miss !== 1'b1)
            $fatal(1, "YARA 0 must MISS after local clear");

        // YÀRÁ 1 must remain intact and still HIT.
        execute_relation(1, 8'h0D, 8'h06);

        if (rmu_hit !== 1'b1)
            $fatal(1, "YARA 1 was incorrectly affected by YARA 0 clear");

        $display("");
        $display("FINAL LOCAL COUNTERS");
        $display("------------------------------------------------------------");
        $display(
            "YARA 0: hits=%0d misses=%0d",
            yara0_hit_count,
            yara0_miss_count
        );
        $display(
            "YARA 1: hits=%0d misses=%0d",
            yara1_hit_count,
            yara1_miss_count
        );

        $display("============================================================");
        $display("PASS: YÀRÁ RMU namespaces are isolated");
        $display("PASS: Same relation does not cross-hit between rooms");
        $display("PASS: Local clear does not affect another room");
        $display("============================================================");

        $finish;
    end

endmodule
