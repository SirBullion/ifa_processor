`timescale 1ns/1ps

module tb_ifa_v4_yara_system_top;

    localparam integer WIDTH      = 8;
    localparam integer IR_WIDTH   = 16;
    localparam integer DEPTH      = 16;
    localparam integer YARA_COUNT = 2;
    localparam integer YARA_W     = 1;

    logic clk;
    logic rst;

    logic babalawo_mode;

    logic create_valid;
    logic select_valid;
    logic pause_valid;
    logic resume_valid;
    logic destroy_valid;

    logic [YARA_W-1:0] command_yara;

    logic context_write;

    logic [WIDTH-1:0]    write_pc;
    logic [IR_WIDTH-1:0] write_ir;
    logic [WIDTH-1:0]    write_a;
    logic [WIDTH-1:0]    write_b;
    logic [WIDTH-1:0]    write_address;
    logic [WIDTH-1:0]    write_flags;

    logic execute_valid;
    logic [WIDTH-1:0] execute_a;
    logic [WIDTH-1:0] execute_b;

    logic [YARA_W-1:0] active_yara;
    logic active_valid;
    logic active_running;

    logic [YARA_COUNT-1:0] yara_valid;
    logic [YARA_COUNT-1:0] yara_running;

    logic command_allowed;
    logic command_denied;

    logic [31:0] switch_count;
    logic [31:0] manager_denied_count;

    logic [WIDTH-1:0]    active_pc;
    logic [IR_WIDTH-1:0] active_ir;
    logic [WIDTH-1:0]    active_a;
    logic [WIDTH-1:0]    active_b;
    logic [WIDTH-1:0]    active_address;
    logic [WIDTH-1:0]    active_flags;

    logic rmu_hit;
    logic rmu_miss;

    logic [WIDTH-1:0] out_y;
    logic [WIDTH-1:0] out_ra;
    logic [WIDTH-1:0] out_rd;
    logic [WIDTH-1:0] out_r0;
    logic [WIDTH-1:0] out_t;

    logic [31:0] active_hit_count;
    logic [31:0] active_miss_count;
    logic [31:0] active_store_count;
    logic [31:0] active_evict_count;

    logic [31:0] yara0_hit_count;
    logic [31:0] yara0_miss_count;
    logic [31:0] yara1_hit_count;
    logic [31:0] yara1_miss_count;

    ifa_v4_yara_system_top #(
        .WIDTH(WIDTH),
        .IR_WIDTH(IR_WIDTH),
        .DEPTH(DEPTH),
        .YARA_COUNT(YARA_COUNT)
    ) dut (
        .clk(clk),
        .rst(rst),

        .babalawo_mode(babalawo_mode),

        .create_valid(create_valid),
        .select_valid(select_valid),
        .pause_valid(pause_valid),
        .resume_valid(resume_valid),
        .destroy_valid(destroy_valid),

        .command_yara(command_yara),

        .context_write(context_write),

        .write_pc(write_pc),
        .write_ir(write_ir),
        .write_a(write_a),
        .write_b(write_b),
        .write_address(write_address),
        .write_flags(write_flags),

        .execute_valid(execute_valid),
        .execute_a(execute_a),
        .execute_b(execute_b),

        .active_yara(active_yara),
        .active_valid(active_valid),
        .active_running(active_running),

        .yara_valid(yara_valid),
        .yara_running(yara_running),

        .command_allowed(command_allowed),
        .command_denied(command_denied),

        .switch_count(switch_count),
        .manager_denied_count(manager_denied_count),

        .active_pc(active_pc),
        .active_ir(active_ir),
        .active_a(active_a),
        .active_b(active_b),
        .active_address(active_address),
        .active_flags(active_flags),

        .rmu_hit(rmu_hit),
        .rmu_miss(rmu_miss),

        .out_y(out_y),
        .out_ra(out_ra),
        .out_rd(out_rd),
        .out_r0(out_r0),
        .out_t(out_t),

        .active_hit_count(active_hit_count),
        .active_miss_count(active_miss_count),
        .active_store_count(active_store_count),
        .active_evict_count(active_evict_count),

        .yara0_hit_count(yara0_hit_count),
        .yara0_miss_count(yara0_miss_count),
        .yara1_hit_count(yara1_hit_count),
        .yara1_miss_count(yara1_miss_count)
    );

    always #5 clk = ~clk;

    task automatic manager_command(
        input logic [2:0] operation,
        input logic room
    );
    begin
        @(negedge clk);

        command_yara = room;

        create_valid  = 1'b0;
        select_valid  = 1'b0;
        pause_valid   = 1'b0;
        resume_valid  = 1'b0;
        destroy_valid = 1'b0;

        case (operation)
            3'd0: create_valid  = 1'b1;
            3'd1: select_valid  = 1'b1;
            3'd2: pause_valid   = 1'b1;
            3'd3: resume_valid  = 1'b1;
            3'd4: destroy_valid = 1'b1;
        endcase

        @(posedge clk);
        #1;

        $display("MANAGER OP=%0d YARA=%0d allowed=%0d denied=%0d valid=%b running=%b active=%0d",
                 operation, room, command_allowed, command_denied,
                 yara_valid, yara_running, active_yara);

        @(negedge clk);

        create_valid  = 1'b0;
        select_valid  = 1'b0;
        pause_valid   = 1'b0;
        resume_valid  = 1'b0;
        destroy_valid = 1'b0;
    end
    endtask

    task automatic write_active_context(
        input logic [7:0] pc,
        input logic [15:0] ir,
        input logic [7:0] a,
        input logic [7:0] b,
        input logic [7:0] address_value,
        input logic [7:0] flags
    );
    begin
        @(negedge clk);

        write_pc      = pc;
        write_ir      = ir;
        write_a       = a;
        write_b       = b;
        write_address = address_value;
        write_flags   = flags;

        context_write = 1'b1;

        @(negedge clk);
        context_write = 1'b0;

        #1;

        $display("CONTEXT YARA=%0d PC=%02h IR=%04h A=%02h B=%02h ADDR=%02h FLAGS=%02h",
                 active_yara, active_pc, active_ir,
                 active_a, active_b, active_address, active_flags);
    end
    endtask

    task automatic execute_relation(
        input logic [7:0] a,
        input logic [7:0] b
    );
    begin
        @(negedge clk);

        execute_a     = a;
        execute_b     = b;
        execute_valid = 1'b1;

        @(negedge clk);
        execute_valid = 1'b0;

        #1;

        $display("EXEC YARA=%0d A=%02h B=%02h hit=%0d miss=%0d Y=%02h RA=%02h RD=%02h R0=%02h T=%02h",
                 active_yara, a, b, rmu_hit, rmu_miss,
                 out_y, out_ra, out_rd, out_r0, out_t);
    end
    endtask

    initial begin
        $dumpfile("sim/v4/ifa_v4_yara_system_top.vcd");
        $dumpvars(0, tb_ifa_v4_yara_system_top);

        clk = 0;
        rst = 1;

        babalawo_mode = 0;

        create_valid  = 0;
        select_valid  = 0;
        pause_valid   = 0;
        resume_valid  = 0;
        destroy_valid = 0;

        command_yara = 0;

        context_write = 0;

        write_pc      = 0;
        write_ir      = 0;
        write_a       = 0;
        write_b       = 0;
        write_address = 0;
        write_flags   = 0;

        execute_valid = 0;
        execute_a = 0;
        execute_b = 0;

        repeat (3) @(negedge clk);
        rst = 0;

        $display("============================================================");
        $display("IFÁ V4 INTEGRATED YÀRÁ SYSTEM TEST");
        $display("============================================================");

        babalawo_mode = 1;

        // Create and select YÀRÁ 0.
        manager_command(3'd0, 0);
        manager_command(3'd1, 0);

        write_active_context(
            8'h12,
            16'hA100,
            8'h0D,
            8'h06,
            8'h20,
            8'h05
        );

        execute_relation(8'h0D, 8'h06);

        if (rmu_miss !== 1'b1)
            $fatal(1, "YARA 0 first access should MISS");

        execute_relation(8'h0D, 8'h06);

        if (rmu_hit !== 1'b1)
            $fatal(1, "YARA 0 second access should HIT");

        // Create and select YÀRÁ 1.
        manager_command(3'd0, 1);
        manager_command(3'd1, 1);

        write_active_context(
            8'h44,
            16'hB200,
            8'h21,
            8'h42,
            8'h80,
            8'hA0
        );

        // Same relation must MISS because YÀRÁ 1 has its own RMU.
        execute_relation(8'h0D, 8'h06);

        if (rmu_miss !== 1'b1)
            $fatal(1, "YARA 1 incorrectly reused YARA 0 frame");

        execute_relation(8'h0D, 8'h06);

        if (rmu_hit !== 1'b1)
            $fatal(1, "YARA 1 second access should HIT locally");

        // Switch back to YÀRÁ 0 and verify restored context and RMU.
        manager_command(3'd1, 0);

        if (
            active_pc      !== 8'h12 ||
            active_ir      !== 16'hA100 ||
            active_a       !== 8'h0D ||
            active_b       !== 8'h06 ||
            active_address !== 8'h20 ||
            active_flags   !== 8'h05
        )
            $fatal(1, "YARA 0 context was not restored");

        execute_relation(8'h0D, 8'h06);

        if (rmu_hit !== 1'b1)
            $fatal(1, "YARA 0 local RMU was not preserved");

        // Destroy YÀRÁ 0.
        manager_command(3'd4, 0);

        if (yara_valid[0] !== 1'b0)
            $fatal(1, "YARA 0 should be invalid after destroy");

        // Switch to YÀRÁ 1 and prove it survived.
        manager_command(3'd1, 1);

        if (
            active_pc      !== 8'h44 ||
            active_ir      !== 16'hB200 ||
            active_a       !== 8'h21 ||
            active_b       !== 8'h42 ||
            active_address !== 8'h80 ||
            active_flags   !== 8'hA0
        )
            $fatal(1, "YARA 1 context was corrupted");

        execute_relation(8'h0D, 8'h06);

        if (rmu_hit !== 1'b1)
            $fatal(1, "YARA 1 RMU was corrupted by YARA 0 destroy");

        $display("");
        $display("FINAL STATE");
        $display("------------------------------------------------------------");
        $display("Valid rooms       = %b", yara_valid);
        $display("Running rooms     = %b", yara_running);
        $display("Active YARA       = %0d", active_yara);
        $display("Context PC        = %02h", active_pc);
        $display("YARA 0 hits/miss  = %0d/%0d",
                 yara0_hit_count, yara0_miss_count);
        $display("YARA 1 hits/miss  = %0d/%0d",
                 yara1_hit_count, yara1_miss_count);

        $display("============================================================");
        $display("PASS: Onílẹ̀ manages room lifecycle and selection");
        $display("PASS: YÀRÁ contexts switch and restore correctly");
        $display("PASS: Each YÀRÁ retains an independent local RMU");
        $display("PASS: Destroying one room does not corrupt another");
        $display("============================================================");

        $finish;
    end

endmodule
