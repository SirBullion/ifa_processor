`timescale 1ns/1ps

module tb_odu_v2_core;

    logic clk = 0;
    logic reset = 1;
    logic start = 0;

    logic [1:0] mode;

    logic [7:0] a;
    logic [7:0] b;
    logic [3:0] mem_addr;

    logic done;

    logic [7:0] y, ra, rd, r0, t;
    logic [7:0] fb_y, fb_ra, fb_rd, fb_r0, fb_t;
    logic [7:0] out_y, out_ra, out_rd, out_r0, out_t;

    always #5 clk = ~clk;

    ifa_odu_v2_core dut (
        .clk(clk),
        .reset(reset),
        .start(start),
        .mode(mode),
        .a(a),
        .b(b),
        .mem_addr(mem_addr),
        .done(done),

        .y(y),
        .ra(ra),
        .rd(rd),
        .r0(r0),
        .t(t),

        .fb_y(fb_y),
        .fb_ra(fb_ra),
        .fb_rd(fb_rd),
        .fb_r0(fb_r0),
        .fb_t(fb_t),

        .out_y(out_y),
        .out_ra(out_ra),
        .out_rd(out_rd),
        .out_r0(out_r0),
        .out_t(out_t)
    );

    function string mode_name(input [1:0] m);
        case (m)
            2'd0: mode_name = "RAW";
            2'd1: mode_name = "FEEDBACK";
            2'd2: mode_name = "STORE_ONLY";
            2'd3: mode_name = "RECALL_ONLY";
            default: mode_name = "UNKNOWN";
        endcase
    endfunction

    task run_case(input [7:0] aa, input [7:0] bb, input [3:0] addr, input [1:0] mm);
        begin
            a = aa;
            b = bb;
            mem_addr = addr;
            mode = mm;

            @(posedge clk);
            start = 1;

            @(posedge clk);
            start = 0;

            @(posedge clk);

            $display("MODE=%s A=%08b B=%08b ADDR=%0d", mode_name(mode), a, b, mem_addr);
            $display("RAW:       Y=%08b RA=%08b RD=%08b R0=%08b T=%08b", y, ra, rd, r0, t);
            $display("FEEDBACK:  Y=%08b RA=%08b RD=%08b R0=%08b T=%08b", fb_y, fb_ra, fb_rd, fb_r0, fb_t);
            $display("OUTPUT:    Y=%08b RA=%08b RD=%08b R0=%08b T=%08b", out_y, out_ra, out_rd, out_r0, out_t);
            $display("----------------------------------------");
        end
    endtask

    initial begin
        $dumpfile("sim/odu_v2_core.vcd");
        $dumpvars(0, tb_odu_v2_core);

        a = 0;
        b = 0;
        mem_addr = 0;
        mode = 0;

        #20;
        reset = 0;

        // 1. Store raw state at address 0
        run_case(8'b10101010, 8'b01010101, 4'd0, 2'd0);

        // 2. Recall address 0
        run_case(8'b00000000, 8'b00000000, 4'd0, 2'd3);

        // 3. Feedback mode using previous address 0
        run_case(8'b11110000, 8'b10100101, 4'd0, 2'd1);

        // 4. Store only at address 1
        run_case(8'b00001111, 8'b11110000, 4'd1, 2'd2);

        // 5. Recall address 1
        run_case(8'b00000000, 8'b00000000, 4'd1, 2'd3);

        $display("ODU V2 core mode-control test complete.");
        $finish;
    end

endmodule
