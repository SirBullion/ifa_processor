`timescale 1ns/1ps

module tb_call_stack;

    logic clk = 0;
    logic reset = 1;
    logic push = 0;
    logic pop = 0;
    logic [7:0] push_data;
    logic [7:0] top;
    logic empty;
    logic full;

    always #5 clk = ~clk;

    ifa_call_stack dut (
        .clk(clk),
        .reset(reset),
        .push(push),
        .pop(pop),
        .push_data(push_data),
        .top(top),
        .empty(empty),
        .full(full)
    );

    task do_push(input [7:0] value);
        begin
            @(negedge clk);
            push_data = value;
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
        $dumpfile("sim/call_stack.vcd");
        $dumpvars(0, tb_call_stack);

        repeat (3) @(posedge clk);
        reset = 0;

        do_push(8'h12);
        $display("After push 12: sp=%0d top=%02h empty=%0b full=%0b", dut.sp, top, empty, full);

        do_push(8'h34);
        $display("After push 34: sp=%0d top=%02h empty=%0b full=%0b", dut.sp, top, empty, full);

        do_pop();
        $display("After pop: sp=%0d top=%02h empty=%0b full=%0b", dut.sp, top, empty, full);

        do_pop();
        $display("After pop: sp=%0d top=%02h empty=%0b full=%0b", dut.sp, top, empty, full);

        $finish;
    end

endmodule
