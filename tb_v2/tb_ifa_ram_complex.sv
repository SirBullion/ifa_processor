`timescale 1ns/1ps

module tb_ifa_ram_complex;

    parameter WIDTH = 4;
    parameter NUM_STEPS = 16;

    logic clk, rst_n, start;
    logic [WIDTH-1:0] A_in, B_in;

    logic [WIDTH-1:0] Y_out;
    logic [WIDTH-1:0] R_primary_out;
    logic [WIDTH-1:0] R_secondary_out;
    logic [1:0] mode_out;
    logic [WIDTH-1:0] feedback_out;

    logic [WIDTH-1:0] gold_A  [0:NUM_STEPS-1];
    logic [WIDTH-1:0] gold_B  [0:NUM_STEPS-1];
    logic [WIDTH-1:0] gold_Y  [0:NUM_STEPS-1];
    logic [WIDTH-1:0] gold_RA [0:NUM_STEPS-1];
    logic [WIDTH-1:0] gold_RD [0:NUM_STEPS-1];

    integer errors;
    integer i;

    ifa_pipelined_core_v1_closed_loop #(
        .WIDTH(WIDTH)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .A_in(A_in),
        .B_in(B_in),
        .Y_out(Y_out),
        .R_primary_out(R_primary_out),
        .R_secondary_out(R_secondary_out),
        .mode_out(mode_out),
        .feedback_out(feedback_out)
    );

    initial clk = 0;
    always #5 clk = ~clk;

    function automatic [WIDTH-1:0] f_Y(input [WIDTH-1:0] a, input [WIDTH-1:0] b);
        f_Y = a + b;
    endfunction

    function automatic [WIDTH-1:0] f_RA(input [WIDTH-1:0] a, input [WIDTH-1:0] b);
        f_RA = a & b;
    endfunction

    function automatic [WIDTH-1:0] f_RD(input [WIDTH-1:0] a, input [WIDTH-1:0] b);
        f_RD = a ^ b;
    endfunction

    task automatic build_golden_trace;
        begin
            gold_A[0] = 4'b1011;
            gold_B[0] = 4'b0110;

            for (i = 0; i < NUM_STEPS; i = i + 1) begin
                if (i > 0) begin
                    gold_A[i] = gold_Y[i-1];
                    gold_B[i] = gold_A[i-1] ^ gold_B[i-1];
                end

                gold_Y[i]  = f_Y(gold_A[i], gold_B[i]);
                gold_RA[i] = f_RA(gold_A[i], gold_B[i]);
                gold_RD[i] = f_RD(gold_A[i], gold_B[i]);
            end
        end
    endtask

    task automatic run_pipeline_once;
        begin
            repeat (8) begin
                @(posedge clk);
                start = 1;
                @(posedge clk);
                start = 0;
            end
            repeat (4) @(posedge clk);
        end
    endtask

    initial begin
        $dumpfile("sim_v2/ifa_ram_complex.vcd");
        $dumpvars(0, tb_ifa_ram_complex);

        errors = 0;
        rst_n = 0;
        start = 0;
        A_in = 0;
        B_in = 0;

        repeat (2) @(posedge clk);
        rst_n = 1;

        build_golden_trace();

        for (i = 0; i < NUM_STEPS; i = i + 1) begin
            A_in = gold_A[i];
            B_in = gold_B[i];

            run_pipeline_once();

            if (Y_out !== gold_Y[i]) begin
                $display("[FAIL] step %0d Y expected=%h got=%h", i, gold_Y[i], Y_out);
                errors++;
            end

            if (R_primary_out !== gold_RA[i]) begin
                $display("[FAIL] step %0d R_A expected=%h got=%h", i, gold_RA[i], R_primary_out);
                errors++;
            end

            if (R_secondary_out !== gold_RD[i]) begin
                $display("[FAIL] step %0d R_D expected=%h got=%h", i, gold_RD[i], R_secondary_out);
                errors++;
            end

            $display("[OK] step %0d A=%h B=%h Y=%h RA=%h RD=%h feedback=%h mode=%b",
                     i, A_in, B_in, Y_out, R_primary_out, R_secondary_out,
                     feedback_out, mode_out);
        end

        if (errors == 0)
            $display("\n=== PASS: %0d-step chained Ifa RAM/RSM computation matched compressed golden trace ===\n", NUM_STEPS);
        else
            $display("\n=== FAIL: %0d mismatches across %0d steps ===\n", errors, NUM_STEPS);

        $finish;
    end

endmodule
