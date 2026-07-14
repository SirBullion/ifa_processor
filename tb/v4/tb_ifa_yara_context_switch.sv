`timescale 1ns/1ps

module tb_ifa_yara_context_switch;

    localparam integer WIDTH      = 8;
    localparam integer IR_WIDTH   = 16;
    localparam integer YARA_COUNT = 2;
    localparam integer YARA_W     = 1;

    logic clk;
    logic rst;

    logic [YARA_W-1:0] active_yara;
    logic context_write;

    logic [WIDTH-1:0]    write_pc;
    logic [IR_WIDTH-1:0] write_ir;
    logic [WIDTH-1:0]    write_a;
    logic [WIDTH-1:0]    write_b;
    logic [WIDTH-1:0]    write_address;
    logic [WIDTH-1:0]    write_flags;

    logic [YARA_COUNT-1:0] clear_yara;

    logic [WIDTH-1:0]    read_pc;
    logic [IR_WIDTH-1:0] read_ir;
    logic [WIDTH-1:0]    read_a;
    logic [WIDTH-1:0]    read_b;
    logic [WIDTH-1:0]    read_address;
    logic [WIDTH-1:0]    read_flags;

    ifa_yara_context_bank #(
        .WIDTH(WIDTH),
        .IR_WIDTH(IR_WIDTH),
        .YARA_COUNT(YARA_COUNT)
    ) dut (
        .clk(clk),
        .rst(rst),

        .active_yara(active_yara),
        .context_write(context_write),

        .write_pc(write_pc),
        .write_ir(write_ir),
        .write_a(write_a),
        .write_b(write_b),
        .write_address(write_address),
        .write_flags(write_flags),

        .clear_yara(clear_yara),

        .read_pc(read_pc),
        .read_ir(read_ir),
        .read_a(read_a),
        .read_b(read_b),
        .read_address(read_address),
        .read_flags(read_flags)
    );

    always #5 clk = ~clk;

    task automatic write_context(
        input logic yara,
        input logic [7:0] pc,
        input logic [15:0] ir,
        input logic [7:0] a,
        input logic [7:0] b,
        input logic [7:0] address,
        input logic [7:0] flags
    );
    begin
        @(negedge clk);

        active_yara = yara;

        write_pc      = pc;
        write_ir      = ir;
        write_a       = a;
        write_b       = b;
        write_address = address;
        write_flags   = flags;

        context_write = 1'b1;

        @(negedge clk);
        context_write = 1'b0;

        #1;

        $display(
            "WRITE YARA=%0d PC=%02h IR=%04h A=%02h B=%02h ADDR=%02h FLAGS=%02h",
            yara, pc, ir, a, b, address, flags
        );
    end
    endtask

    task automatic select_context(input logic yara);
    begin
        @(negedge clk);
        active_yara = yara;

        #1;

        $display(
            "READ  YARA=%0d PC=%02h IR=%04h A=%02h B=%02h ADDR=%02h FLAGS=%02h",
            yara,
            read_pc,
            read_ir,
            read_a,
            read_b,
            read_address,
            read_flags
        );
    end
    endtask

    task automatic clear_context(input logic yara);
    begin
        @(negedge clk);

        clear_yara = '0;
        clear_yara[yara] = 1'b1;

        @(negedge clk);
        clear_yara = '0;

        #1;

        $display("CLEARED YARA=%0d", yara);
    end
    endtask

    initial begin
        $dumpfile("sim/v4/ifa_yara_context_switch.vcd");
        $dumpvars(0, tb_ifa_yara_context_switch);

        clk = 0;
        rst = 1;

        active_yara = 0;
        context_write = 0;

        write_pc = 0;
        write_ir = 0;
        write_a = 0;
        write_b = 0;
        write_address = 0;
        write_flags = 0;

        clear_yara = '0;

        repeat (3) @(negedge clk);
        rst = 0;

        $display("============================================================");
        $display("IFÁ V4 YÀRÁ CONTEXT-SWITCH TEST");
        $display("============================================================");

        // Independent state for YÀRÁ 0.
        write_context(
            0,
            8'h12,
            16'hA100,
            8'h0D,
            8'h06,
            8'h20,
            8'h05
        );

        // Independent state for YÀRÁ 1.
        write_context(
            1,
            8'h44,
            16'hB200,
            8'h21,
            8'h42,
            8'h80,
            8'hA0
        );

        // Restore YÀRÁ 0.
        select_context(0);

        if (
            read_pc      !== 8'h12 ||
            read_ir      !== 16'hA100 ||
            read_a       !== 8'h0D ||
            read_b       !== 8'h06 ||
            read_address !== 8'h20 ||
            read_flags   !== 8'h05
        )
            $fatal(1, "YARA 0 context restore failed");

        // Restore YÀRÁ 1.
        select_context(1);

        if (
            read_pc      !== 8'h44 ||
            read_ir      !== 16'hB200 ||
            read_a       !== 8'h21 ||
            read_b       !== 8'h42 ||
            read_address !== 8'h80 ||
            read_flags   !== 8'hA0
        )
            $fatal(1, "YARA 1 context restore failed");

        // Clear only YÀRÁ 0.
        clear_context(0);

        select_context(0);

        if (
            read_pc      !== 0 ||
            read_ir      !== 0 ||
            read_a       !== 0 ||
            read_b       !== 0 ||
            read_address !== 0 ||
            read_flags   !== 0
        )
            $fatal(1, "YARA 0 context did not clear");

        // YÀRÁ 1 must remain unchanged.
        select_context(1);

        if (
            read_pc      !== 8'h44 ||
            read_ir      !== 16'hB200 ||
            read_a       !== 8'h21 ||
            read_b       !== 8'h42 ||
            read_address !== 8'h80 ||
            read_flags   !== 8'hA0
        )
            $fatal(1, "YARA 1 was corrupted by YARA 0 clear");

        $display("============================================================");
        $display("PASS: Each YÀRÁ preserves independent processor state");
        $display("PASS: Onílẹ̀ can switch and restore contexts");
        $display("PASS: Local context clear does not affect another YÀRÁ");
        $display("============================================================");

        $finish;
    end

endmodule
