`timescale 1ns/1ps
module tb_v4_gtkwave_overall;
    parameter WIDTH = 8;
    parameter DEPTH = 16;

    logic clk, rst, in_valid;
    logic [WIDTH-1:0] A, B;
    logic rmu_hit, rmu_miss;
    logic [WIDTH-1:0] out_y, out_ra, out_rd, out_r0, out_t;
    logic [31:0] hit_count, miss_count, store_count, evict_count;

    ifa_v4_end_to_end_core #(.WIDTH(WIDTH), .DEPTH(DEPTH)) dut (
        .clk(clk), .rst(rst), .in_valid(in_valid), .A(A), .B(B),
        .rmu_hit(rmu_hit), .rmu_miss(rmu_miss),
        .out_y(out_y), .out_ra(out_ra), .out_rd(out_rd), .out_r0(out_r0), .out_t(out_t),
        .hit_count(hit_count), .miss_count(miss_count), .store_count(store_count), .evict_count(evict_count)
    );

    always #5 clk = ~clk;

    logic [WIDTH-1:0] test_a [0:11];
    logic [WIDTH-1:0] test_b [0:11];
    integer i;

    initial begin
        test_a[0]  = 8'h0D; test_b[0]  = 8'h06;
        test_a[1]  = 8'h0D; test_b[1]  = 8'h06; // repeat -> expect hit
        test_a[2]  = 8'h07; test_b[2]  = 8'h08;
        test_a[3]  = 8'h01; test_b[3]  = 8'h02;
        test_a[4]  = 8'h07; test_b[4]  = 8'h08; // repeat -> expect hit
        test_a[5]  = 8'h00; test_b[5]  = 8'h00;
        test_a[6]  = 8'hFF; test_b[6]  = 8'hFF;
        test_a[7]  = 8'h01; test_b[7]  = 8'h02; // repeat -> expect hit
        test_a[8]  = 8'h21; test_b[8]  = 8'h42;
        test_a[9]  = 8'h21; test_b[9]  = 8'h42; // repeat -> expect hit
        test_a[10] = 8'hA5; test_b[10] = 8'h5A;
        test_a[11] = 8'h00; test_b[11] = 8'h00; // repeat -> expect hit
    end

    initial begin
        $dumpfile("sim/v4/gtkwave_overall.vcd");
        $dumpvars(0, tb_v4_gtkwave_overall);

        clk = 0; rst = 1; in_valid = 0; A = 0; B = 0;
        repeat (2) @(posedge clk);
        @(negedge clk);
        rst = 0;

        $display("=========================================================");
        $display("V4 GTKWAVE OVERALL TEST -- post RA/T patch (race-free)");
        $display("=========================================================");

        for (i = 0; i < 12; i = i + 1) begin
            @(negedge clk);
            A = test_a[i];
            B = test_b[i];
            in_valid = 1;

            @(posedge clk);
            #1;

            $display("[%0d] A=0x%0h B=0x%0h | hit=%0b miss=%0b | Y=0x%0h RA=0x%0h RD=0x%0h R0=0x%0h T=0x%0h | hits=%0d misses=%0d",
                      i, A, B, rmu_hit, rmu_miss, out_y, out_ra, out_rd, out_r0, out_t,
                      hit_count, miss_count);

            @(negedge clk);
            in_valid = 0;
        end

        @(posedge clk);

        $display("=========================================================");
        $display("FINAL COUNTS: hits=%0d misses=%0d stores=%0d evicts=%0d",
                  hit_count, miss_count, store_count, evict_count);
        $display("Expected: hits=5 misses=7 (7 unique pairs + 5 repeats)");
        $display("Done. Open sim/v4/gtkwave_overall.vcd in GTKWave to inspect.");
        $display("=========================================================");
        $finish;
    end
endmodule
