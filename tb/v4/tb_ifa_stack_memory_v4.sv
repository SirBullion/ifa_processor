`timescale 1ns/1ps

module tb_ifa_stack_memory_v4;

    localparam integer WIDTH       = 8;
    localparam integer MAX_YARA    = 16;
    localparam integer STACK_DEPTH = 16;
    localparam integer YARA_W      = 4;
    localparam integer SP_W        = 4;

    logic clk;
    logic rst;

    logic [YARA_W-1:0] active_yara;
    logic [SP_W-1:0] stack_pointer;

    logic write_valid;
    logic read_valid;
    logic [WIDTH-1:0] write_data;

    logic [WIDTH-1:0] read_data;
    logic write_done;
    logic read_done;
    logic stack_allowed;
    logic stack_denied;

    ifa_stack_memory_v4 #(
        .WIDTH       (WIDTH),
        .MAX_YARA    (MAX_YARA),
        .STACK_DEPTH (STACK_DEPTH)
    ) dut (
        .clk           (clk),
        .rst           (rst),

        .active_yara   (active_yara),
        .stack_pointer (stack_pointer),

        .write_valid   (write_valid),
        .read_valid    (read_valid),
        .write_data    (write_data),

        .read_data     (read_data),
        .write_done    (write_done),
        .read_done     (read_done),

        .stack_allowed (stack_allowed),
        .stack_denied  (stack_denied)
    );

    always #5 clk = ~clk;

    task automatic stack_write(
        input integer yara,
        input integer sp,
        input integer data
    );
    begin
        @(negedge clk);

        active_yara   = yara[YARA_W-1:0];
        stack_pointer = sp[SP_W-1:0];
        write_data    = data[WIDTH-1:0];
        write_valid   = 1'b1;

        @(posedge clk);
        #1;

        if (!write_done || !stack_allowed || stack_denied) begin
            $fatal(
                1,
                "WRITE FAILED YARA=%0d SP=%0d DATA=%02h",
                yara,
                sp,
                data
            );
        end

        @(negedge clk);
        write_valid = 1'b0;
    end
    endtask

    task automatic stack_read_check(
        input integer yara,
        input integer sp,
        input integer expected
    );
    begin
        @(negedge clk);

        active_yara   = yara[YARA_W-1:0];
        stack_pointer = sp[SP_W-1:0];
        read_valid    = 1'b1;

        @(posedge clk);
        #1;

        if (!read_done || !stack_allowed || stack_denied) begin
            $fatal(
                1,
                "READ FAILED YARA=%0d SP=%0d",
                yara,
                sp
            );
        end

        if (read_data !== expected[WIDTH-1:0]) begin
            $fatal(
                1,
                "READ MISMATCH YARA=%0d SP=%0d GOT=%02h EXPECTED=%02h",
                yara,
                sp,
                read_data,
                expected
            );
        end

        @(negedge clk);
        read_valid = 1'b0;
    end
    endtask

    initial begin
        clk = 1'b0;
        rst = 1'b1;

        active_yara   = '0;
        stack_pointer = '0;
        write_valid   = 1'b0;
        read_valid    = 1'b0;
        write_data    = '0;

        repeat (2) @(posedge clk);
        rst = 1'b0;

        stack_write(0, 3, 8'hA5);
        stack_write(1, 3, 8'h5A);

        stack_read_check(0, 3, 8'hA5);
        stack_read_check(1, 3, 8'h5A);

        stack_write(0, 4, 8'hC7);

        stack_read_check(0, 4, 8'hC7);
        stack_read_check(1, 4, 8'h00);

        $display(
            "PASS: Shared stack RAM preserves per-YARA isolation"
        );

        $finish;
    end

endmodule
