`timescale 1ns/1ps

module tb_ifa_ram_complex_v2;

    parameter WIDTH      = 4;
    parameter DEPTH      = 32;
    parameter ADDR_WIDTH = 5;
    parameter NUM_STEPS  = 24;

    initial begin
        if (NUM_STEPS > DEPTH) begin
            $display("[FATAL] NUM_STEPS=%0d exceeds RAM DEPTH=%0d",
                     NUM_STEPS, DEPTH);
            $finish;
        end
    end

    logic clk, we;
    logic [ADDR_WIDTH-1:0] addr;

    logic [WIDTH-1:0] Y_in, R_primary_in, R_secondary_in;
    logic [1:0] mode_in;

    logic [WIDTH-1:0] Y_out, R_primary_out, R_secondary_out;
    logic [1:0] mode_out;

    logic [WIDTH-1:0] gold_A [0:NUM_STEPS-1];
    logic [WIDTH-1:0] gold_B [0:NUM_STEPS-1];
    logic [WIDTH-1:0] gold_Y [0:NUM_STEPS-1];
    logic [WIDTH-1:0] gold_RA[0:NUM_STEPS-1];
    logic [WIDTH-1:0] gold_RD[0:NUM_STEPS-1];
    logic [1:0]       gold_mode[0:NUM_STEPS-1];

    logic [3:0] modes_seen;

    integer i, j, errors;
    integer read_order [0:NUM_STEPS-1];

    ifa_relation_ram #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) dut (
        .clk(clk),
        .we(we),
        .addr(addr),

        .Y_in(Y_in),
        .R_primary_in(R_primary_in),
        .R_secondary_in(R_secondary_in),
        .mode_in(mode_in),

        .Y_out(Y_out),
        .R_primary_out(R_primary_out),
        .R_secondary_out(R_secondary_out),
        .mode_out(mode_out)
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

    function automatic [1:0] f_mode(input [WIDTH-1:0] ra, input [WIDTH-1:0] rd);
        begin
            if (rd == 4'h0)
                f_mode = 2'b10;
            else if ((ra ^ rd) <= 4'h3)
                f_mode = 2'b11;
            else if (rd[1:0] == 2'b00)
                f_mode = 2'b01;
            else
                f_mode = 2'b00;
        end
    endfunction

    task automatic build_trace;
    begin
        gold_A[0]=4'hF; gold_B[0]=4'hF;
        gold_A[1]=4'hF; gold_B[1]=4'h0;
        gold_A[2]=4'hA; gold_B[2]=4'h5;
        gold_A[3]=4'hC; gold_B[3]=4'hA;
        gold_A[4]=4'h1; gold_B[4]=4'h1;
        gold_A[5]=4'h8; gold_B[5]=4'h7;
        gold_A[6]=4'h6; gold_B[6]=4'h6;
        gold_A[7]=4'hE; gold_B[7]=4'h3;

        for (i = 0; i < 8; i = i + 1) begin
            gold_Y[i]    = f_Y(gold_A[i], gold_B[i]);
            gold_RA[i]   = f_RA(gold_A[i], gold_B[i]);
            gold_RD[i]   = f_RD(gold_A[i], gold_B[i]);
            gold_mode[i] = f_mode(gold_RA[i], gold_RD[i]);
        end

        for (i = 8; i < NUM_STEPS; i = i + 1) begin
            gold_A[i] = gold_Y[i-1] ^ i[WIDTH-1:0];
            gold_B[i] = (gold_A[i-1] ^ gold_B[i-1]) + i[WIDTH-1:0];

            gold_Y[i]    = f_Y(gold_A[i], gold_B[i]);
            gold_RA[i]   = f_RA(gold_A[i], gold_B[i]);
            gold_RD[i]   = f_RD(gold_A[i], gold_B[i]);
            gold_mode[i] = f_mode(gold_RA[i], gold_RD[i]);
        end
    end
endtask

    task automatic build_read_order;
        integer tmp, r;
        begin
            for (i = 0; i < NUM_STEPS; i = i + 1)
                read_order[i] = i;

            for (i = NUM_STEPS-1; i > 0; i = i - 1) begin
                r = $urandom_range(0, i);
                tmp = read_order[i];
                read_order[i] = read_order[r];
                read_order[r] = tmp;
            end
        end
    endtask

    initial begin
        $dumpfile("sim_v2/ifa_ram_complex_v2.vcd");
        $dumpvars(0, tb_ifa_ram_complex_v2);

        errors = 0;
        modes_seen = 4'b0000;
        we = 0;
        addr = 0;

        build_trace();
        build_read_order();

        // WRITE PHASE
        for (i = 0; i < NUM_STEPS; i = i + 1) begin
            addr = i[ADDR_WIDTH-1:0];

            Y_in           = gold_Y[i];
            R_primary_in   = gold_RA[i];
            R_secondary_in = gold_RD[i];
            mode_in        = gold_mode[i];

            modes_seen[mode_in] = 1'b1;

            @(posedge clk);
            we = 1;
            @(posedge clk);
            we = 0;

            $display("[WRITE] addr=%0d Y=%h RA=%h RD=%h mode=%b",
                     i, Y_in, R_primary_in, R_secondary_in, mode_in);
        end

        $display("--- write phase complete: %0d steps stored ---", NUM_STEPS);

        // READ PHASE OUT OF ORDER
        for (j = 0; j < NUM_STEPS; j = j + 1) begin
            i = read_order[j];
            addr = i[ADDR_WIDTH-1:0];

            @(posedge clk);
            @(posedge clk);

            if ($isunknown(Y_out)) begin
                $display("[FAIL] addr %0d : Y_out is X/unknown", i);
                errors++;
            end

            if ($isunknown(R_primary_out)) begin
                $display("[FAIL] addr %0d : R_primary_out is X/unknown", i);
                errors++;
            end

            if ($isunknown(R_secondary_out)) begin
                $display("[FAIL] addr %0d : R_secondary_out is X/unknown", i);
                errors++;
            end

            if ($isunknown(mode_out)) begin
                $display("[FAIL] addr %0d : mode_out is X/unknown", i);
                errors++;
            end

            if (!$isunknown(Y_out) && (Y_out !== gold_Y[i])) begin
                $display("[FAIL] addr %0d : Y expected=%h got=%h",
                         i, gold_Y[i], Y_out);
                errors++;
            end

            if (!$isunknown(R_primary_out) &&
                (R_primary_out !== gold_RA[i])) begin
                $display("[FAIL] addr %0d : R_A expected=%h got=%h",
                         i, gold_RA[i], R_primary_out);
                errors++;
            end

            if (!$isunknown(R_secondary_out) &&
                (R_secondary_out !== gold_RD[i])) begin
                $display("[FAIL] addr %0d : R_D expected=%h got=%h",
                         i, gold_RD[i], R_secondary_out);
                errors++;
            end

            if (!$isunknown(mode_out) &&
                (mode_out !== gold_mode[i])) begin
                $display("[FAIL] addr %0d : mode expected=%b got=%b",
                         i, gold_mode[i], mode_out);
                errors++;
            end
        end

        $display("Modes seen bitmap = %b", modes_seen);

        if ($countones(modes_seen) < 2)
            $display("[WARNING] weak mode coverage");

        if (errors == 0)
            $display("\n=== PASS: complex RSM/RAM round-trip survived chained writes and shuffled reads ===\n");
        else
            $display("\n=== FAIL: %0d mismatches ===\n", errors);

        $finish;
    end

endmodule
