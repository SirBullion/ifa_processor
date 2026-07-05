`timescale 1ns/1ps

module tb_ifa_ram_roundtrip;

    parameter WIDTH = 4;
    parameter NUM_TESTS = 50;

    logic clk, rst_n, start;
    logic [WIDTH-1:0] A_in, B_in;

    logic [WIDTH-1:0] Y_out;
    logic [WIDTH-1:0] R_primary_out;
    logic [WIDTH-1:0] R_secondary_out;
    logic [1:0] mode_out;
    logic [WIDTH-1:0] feedback_out;

    logic [WIDTH-1:0] y_golden, ra_golden, rd_golden;
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

    task automatic compute_golden(input [WIDTH-1:0] a, input [WIDTH-1:0] b);
        begin
            y_golden  = a + b;
            ra_golden = a & b;
            rd_golden = a ^ b;
        end
    endtask

    task automatic run_core_sequence;
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
        $dumpfile("sim_v2/ifa_ram_roundtrip.vcd");
        $dumpvars(0, tb_ifa_ram_roundtrip);

        errors = 0;
        rst_n = 0;
        start = 0;
        A_in = 0;
        B_in = 0;

        repeat (2) @(posedge clk);
        rst_n = 1;

        for (i = 0; i < NUM_TESTS; i = i + 1) begin
            case (i)
                0: begin A_in = '0;            B_in = '0;            end
                1: begin A_in = {WIDTH{1'b1}}; B_in = {WIDTH{1'b1}}; end
                2: begin A_in = '0;            B_in = {WIDTH{1'b1}}; end
                3: begin A_in = 4'hD;          B_in = 4'h6;          end
                default: begin
                    A_in = $urandom_range(0, (1<<WIDTH)-1);
                    B_in = $urandom_range(0, (1<<WIDTH)-1);
                end
            endcase

            compute_golden(A_in, B_in);

            run_core_sequence();

            if (Y_out !== y_golden) begin
                $display("[FAIL] %0d Y: A=%h B=%h expected=%h got=%h",
                         i, A_in, B_in, y_golden, Y_out);
                errors++;
            end

            if (R_primary_out !== ra_golden) begin
                $display("[FAIL] %0d R_A: A=%h B=%h expected=%h got=%h",
                         i, A_in, B_in, ra_golden, R_primary_out);
                errors++;
            end

            if (R_secondary_out !== rd_golden) begin
                $display("[FAIL] %0d R_D: A=%h B=%h expected=%h got=%h",
                         i, A_in, B_in, rd_golden, R_secondary_out);
                errors++;
            end
        end

        if (errors == 0)
            $display("\n=== PASS: all %0d RAM/RSM round-trip tests matched current compressed model ===\n", NUM_TESTS);
        else
            $display("\n=== FAIL: %0d mismatches out of %0d tests ===\n", errors, NUM_TESTS);

        $finish;
    end

endmodule
