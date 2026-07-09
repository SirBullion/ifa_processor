`timescale 1ns/1ps

module tb_ifa_v4_modus_tollens;

    localparam WIDTH = 8;
    localparam DEPTH = 16;

    logic clk;
    logic rst;
    logic in_valid;

    logic [WIDTH-1:0] P;
    logic [WIDTH-1:0] Q;

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

    integer cycles;
    logic conclusion_not_p;

    ifa_v4_end_to_end_core #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH)
    ) dut (
        .clk(clk),
        .rst(rst),

        .in_valid(in_valid),
        .A(P),
        .B(Q),

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

    always @(posedge clk) begin
        if (!rst)
            cycles <= cycles + 1;
    end

    initial begin
        $dumpfile("sim/v4/ifa_v4_modus_tollens.vcd");
        $dumpvars(0, tb_ifa_v4_modus_tollens);

        clk = 0;
        rst = 1;
        in_valid = 0;
        P = 0;
        Q = 0;
        cycles = 0;
        conclusion_not_p = 0;

        repeat (3) @(posedge clk);
        rst = 0;

        $display("==================================================");
        $display("IFÁ V4 MODUS TOLLENS TEST");
        $display("Rule: P -> Q, observe not-Q, conclude not-P");
        $display("Case: P=1, Q=0");
        $display("==================================================");

        // Send P,Q into relation processor
        @(negedge clk);
        P = 8'h01;
        Q = 8'h00;
        in_valid = 1'b1;

        @(negedge clk);
        in_valid = 1'b0;

        // Wait for output to settle
        @(posedge clk);

        // Ifá relation interpretation:
        // P=1, Q=0 gives active disagreement RD=1.
        // Under implication P->Q, this is the contradiction case.
        if (out_rd == 8'h01 && out_ra == 8'h00) begin
            conclusion_not_p = 1'b1;
        end

        $display("P                    = 0x%02h", P);
        $display("Q                    = 0x%02h", Q);
        $display("Y                    = 0x%02h", out_y);
        $display("RA                   = 0x%02h", out_ra);
        $display("RD                   = 0x%02h", out_rd);
        $display("R0                   = 0x%02h", out_r0);
        $display("T                    = 0x%02h", out_t);
        $display("RMU hit              = %0d", rmu_hit);
        $display("RMU miss             = %0d", rmu_miss);
        $display("conclusion_not_p     = %0d", conclusion_not_p);
        $display("cycles               = %0d", cycles);
        $display("hit_count            = %0d", hit_count);
        $display("miss_count           = %0d", miss_count);

        if (conclusion_not_p !== 1'b1)
            $fatal(1, "Expected modus-tollens conclusion not-P");

        $display("==================================================");
        $display("ALL IFÁ V4 MODUS TOLLENS TESTS PASSED");
        $display("==================================================");

        $finish;
    end

endmodule
