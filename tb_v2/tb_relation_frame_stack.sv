`timescale 1ns/1ps

module tb_relation_frame_stack;

    logic clk = 0;
    logic reset = 1;
    logic push = 0;
    logic pop = 0;

    logic [7:0] y_in, ra_in, rd_in, r0_in, t_in;
    logic [7:0] y_out, ra_out, rd_out, r0_out, t_out;
    logic empty, full;

    always #5 clk = ~clk;

    ifa_relation_frame_stack dut (
        .clk(clk),
        .reset(reset),
        .push(push),
        .pop(pop),
        .y_in(y_in),
        .ra_in(ra_in),
        .rd_in(rd_in),
        .r0_in(r0_in),
        .t_in(t_in),
        .y_out(y_out),
        .ra_out(ra_out),
        .rd_out(rd_out),
        .r0_out(r0_out),
        .t_out(t_out),
        .empty(empty),
        .full(full)
    );

    task do_push(input [7:0] y, input [7:0] ra, input [7:0] rd, input [7:0] r0, input [7:0] t);
        begin
            @(negedge clk);
            y_in = y; ra_in = ra; rd_in = rd; r0_in = r0; t_in = t;
            push = 1;
            @(negedge clk);
            push = 0;
            @(posedge clk);
            #1;
        end
    endtask

    task do_pop();
        begin
            @(negedge clk);
            pop = 1;
            @(negedge clk);
            pop = 0;
            @(posedge clk);
            #1;
        end
    endtask

    initial begin
        $dumpfile("sim/relation_frame_stack.vcd");
        $dumpvars(0, tb_relation_frame_stack);

        repeat (3) @(posedge clk);
        reset = 0;

        do_push(8'hAA, 8'h11, 8'h22, 8'h33, 8'h44);
        $display("After push 1: Y=%02h RA=%02h RD=%02h R0=%02h T=%02h empty=%0b",
                 y_out, ra_out, rd_out, r0_out, t_out, empty);

        do_push(8'hBB, 8'h55, 8'h66, 8'h77, 8'h88);
        $display("After push 2: Y=%02h RA=%02h RD=%02h R0=%02h T=%02h empty=%0b",
                 y_out, ra_out, rd_out, r0_out, t_out, empty);

        do_pop();
        $display("After pop:    Y=%02h RA=%02h RD=%02h R0=%02h T=%02h empty=%0b",
                 y_out, ra_out, rd_out, r0_out, t_out, empty);

        do_pop();
        $display("After pop:    Y=%02h RA=%02h RD=%02h R0=%02h T=%02h empty=%0b",
                 y_out, ra_out, rd_out, r0_out, t_out, empty);

        $finish;
    end

endmodule
