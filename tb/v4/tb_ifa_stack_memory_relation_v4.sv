`timescale 1ns/1ps

module tb_ifa_stack_memory_relation_v4;

    localparam integer WIDTH       = 8;
    localparam integer OP_WIDTH    = 4;
    localparam integer ENTRY_WIDTH =
        (6 * WIDTH) + OP_WIDTH + 14;

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

    logic [ENTRY_WIDTH-1:0] write_data;
    logic [ENTRY_WIDTH-1:0] read_data;

    logic write_done;
    logic read_done;
    logic stack_allowed;
    logic stack_denied;

    logic [ENTRY_WIDTH-1:0] frame_yara0;
    logic [ENTRY_WIDTH-1:0] frame_yara1;

    ifa_stack_memory_v4 #(
        .WIDTH       (WIDTH),
        .ENTRY_WIDTH (ENTRY_WIDTH),
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

    task automatic write_frame(
        input integer yara,
        input integer sp,
        input logic [ENTRY_WIDTH-1:0] frame
    );
    begin
        @(negedge clk);

        active_yara   = yara[YARA_W-1:0];
        stack_pointer = sp[SP_W-1:0];
        write_data    = frame;
        write_valid   = 1'b1;

        @(posedge clk);
        #1;

        if (!write_done || !stack_allowed || stack_denied)
            $fatal(
                1,
                "RELATION WRITE FAILED YARA=%0d SP=%0d",
                yara,
                sp
            );

        @(negedge clk);
        write_valid = 1'b0;
    end
    endtask

    task automatic read_frame_check(
        input integer yara,
        input integer sp,
        input logic [ENTRY_WIDTH-1:0] expected
    );
    begin
        @(negedge clk);

        active_yara   = yara[YARA_W-1:0];
        stack_pointer = sp[SP_W-1:0];
        read_valid    = 1'b1;

        @(posedge clk);
        #1;

        if (!read_done || !stack_allowed || stack_denied)
            $fatal(
                1,
                "RELATION READ FAILED YARA=%0d SP=%0d",
                yara,
                sp
            );

        if (read_data !== expected)
            $fatal(
                1,
                "RELATION FRAME MISMATCH YARA=%0d SP=%0d",
                yara,
                sp
            );

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

        frame_yara0 = {
            8'h2A,
            4'h5,
            8'hB9,
            8'h04,
            8'h0B,
            8'hF0,
            8'hA6,
            1'b1,
            1'b0,
            4'h0,
            1'b1,
            4'h1,
            1'b0,
            1'b1,
            1'b0
        };

        frame_yara1 = {
            8'h7C,
            4'h3,
            8'h02,
            8'h04,
            8'h0B,
            8'hF0,
            8'h01,
            1'b1,
            1'b0,
            4'h0,
            1'b0,
            4'h0,
            1'b0,
            1'b0,
            1'b1
        };

        repeat (2) @(posedge clk);
        rst = 1'b0;

        write_frame(0, 3, frame_yara0);
        write_frame(1, 3, frame_yara1);

        read_frame_check(0, 3, frame_yara0);
        read_frame_check(1, 3, frame_yara1);

        if (ENTRY_WIDTH != 66)
            $fatal(1, "Expected ENTRY_WIDTH=66");

        $display(
            "PASS: Shared stack RAM stores 66-bit IFÁ relation frames"
        );

        $display(
            "PASS: 66-bit relation frames remain isolated per YARA"
        );

        $finish;
    end

endmodule
