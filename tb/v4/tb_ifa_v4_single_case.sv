`timescale 1ns/1ps

module tb_ifa_v4_single_case;

    localparam WIDTH = 8;
    localparam DEPTH = 16;

    logic clk = 0;
    logic rst = 1;
    logic in_valid = 0;

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

    initial begin
        if (!$value$plusargs("A=%h", A)) A = 8'h00;
        if (!$value$plusargs("B=%h", B)) B = 8'h00;

        repeat (3) @(posedge clk);
        rst = 0;

        @(negedge clk);
        in_valid = 1'b1;

        @(negedge clk);
        in_valid = 1'b0;

        @(posedge clk);

        $display("RESULT A=%02h B=%02h Y=%02h RA=%02h RD=%02h R0=%02h T=%02h HIT=%0d MISS=%0d",
                 A, B, out_y, out_ra, out_rd, out_r0, out_t, rmu_hit, rmu_miss);

        $finish;
    end

endmodule
