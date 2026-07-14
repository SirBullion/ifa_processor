`timescale 1ns/1ps

module tb_ifa_v4_yara_secure_system_top;

    localparam integer WIDTH      = 8;
    localparam integer IR_WIDTH   = 16;
    localparam integer RMU_DEPTH  = 16;
    localparam integer MEM_ADDR_W = 4;
    localparam integer YARA_COUNT = 2;

    logic clk;
    logic rst;

    logic babalawo_mode;

    logic create_valid;
    logic select_valid;
    logic pause_valid;
    logic resume_valid;
    logic destroy_valid;
    logic command_yara;

    logic context_write;
    logic [7:0] write_pc;
    logic [15:0] write_ir;
    logic [7:0] write_a;
    logic [7:0] write_b;
    logic [7:0] write_address;
    logic [7:0] write_flags;

    logic execute_valid;
    logic [7:0] execute_a;
    logic [7:0] execute_b;

    logic mem_request;
    logic mem_write;
    logic [3:0] mem_address;
    logic [7:0] mem_write_data;

    logic [7:0] mem_read_data;
    logic mem_allowed;
    logic mem_denied;

    logic grant_read_valid;
    logic grant_write_valid;
    logic revoke_read_valid;
    logic revoke_write_valid;

    logic [3:0] admin_address;
    logic admin_yara;

    logic active_yara;
    logic active_valid;
    logic active_running;

    logic [1:0] yara_valid;
    logic [1:0] yara_running;

    logic command_allowed;
    logic command_denied;

    logic [31:0] switch_count;
    logic [31:0] manager_denied_count;

    logic [7:0] active_pc;
    logic [15:0] active_ir;
    logic [7:0] active_a;
    logic [7:0] active_b;
    logic [7:0] active_address;
    logic [7:0] active_flags;

    logic rmu_hit;
    logic rmu_miss;

    logic [7:0] out_y;
    logic [7:0] out_ra;
    logic [7:0] out_rd;
    logic [7:0] out_r0;
    logic [7:0] out_t;

    logic [31:0] active_hit_count;
    logic [31:0] active_miss_count;

    logic [31:0] yara0_hit_count;
    logic [31:0] yara0_miss_count;
    logic [31:0] yara1_hit_count;
    logic [31:0] yara1_miss_count;

    logic [31:0] memory_read_count;
    logic [31:0] memory_write_count;
    logic [31:0] memory_denied_count;

    ifa_v4_yara_secure_system_top dut (
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

        .mem_request(mem_request),
        .mem_write(mem_write),
        .mem_address(mem_address),
        .mem_write_data(mem_write_data),

        .mem_read_data(mem_read_data),
        .mem_allowed(mem_allowed),
        .mem_denied(mem_denied),

        .grant_read_valid(grant_read_valid),
        .grant_write_valid(grant_write_valid),
        .revoke_read_valid(revoke_read_valid),
        .revoke_write_valid(revoke_write_valid),

        .admin_address(admin_address),
        .admin_yara(admin_yara),

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

        .yara0_hit_count(yara0_hit_count),
        .yara0_miss_count(yara0_miss_count),
        .yara1_hit_count(yara1_hit_count),
        .yara1_miss_count(yara1_miss_count),

        .memory_read_count(memory_read_count),
        .memory_write_count(memory_write_count),
        .memory_denied_count(memory_denied_count)
    );

    always #5 clk = ~clk;

    task automatic clear_commands;
    begin
        create_valid  = 0;
        select_valid  = 0;
        pause_valid   = 0;
        resume_valid  = 0;
        destroy_valid = 0;
    end
    endtask

    task automatic manager_command(
        input logic [2:0] operation,
        input logic room
    );
    begin
        @(negedge clk);

        clear_commands();
        command_yara = room;

        case (operation)
            3'd0: create_valid  = 1;
            3'd1: select_valid  = 1;
            3'd2: pause_valid   = 1;
            3'd3: resume_valid  = 1;
            3'd4: destroy_valid = 1;
        endcase

        @(posedge clk);
        #1;

        @(negedge clk);
        clear_commands();
    end
    endtask

    task automatic write_memory(
        input logic [3:0] address,
        input logic [7:0] data
    );
    begin
        @(negedge clk);

        mem_address    = address;
        mem_write_data = data;
        mem_write      = 1;
        mem_request    = 1;

        @(posedge clk);
        #1;

        $display("WRITE YARA=%0d ADDR=%0h DATA=%02h allowed=%0d denied=%0d",
                 active_yara, address, data, mem_allowed, mem_denied);

        @(negedge clk);
        mem_request = 0;
        mem_write   = 0;
    end
    endtask

    task automatic read_memory(input logic [3:0] address);
    begin
        @(negedge clk);

        mem_address = address;
        mem_write   = 0;
        mem_request = 1;

        @(posedge clk);
        #1;

        $display("READ  YARA=%0d ADDR=%0h DATA=%02h allowed=%0d denied=%0d",
                 active_yara, address, mem_read_data, mem_allowed, mem_denied);

        @(negedge clk);
        mem_request = 0;
    end
    endtask

    task automatic grant_read(
        input logic room,
        input logic [3:0] address
    );
    begin
        @(negedge clk);

        admin_yara       = room;
        admin_address    = address;
        grant_read_valid = 1;

        @(posedge clk);
        #1;

        @(negedge clk);
        grant_read_valid = 0;
    end
    endtask

    initial begin
        $dumpfile("sim/v4/ifa_v4_yara_secure_system_top.vcd");
        $dumpvars(0, tb_ifa_v4_yara_secure_system_top);

        clk = 0;
        rst = 1;

        babalawo_mode = 0;

        clear_commands();
        command_yara = 0;

        context_write = 0;
        write_pc = 0;
        write_ir = 0;
        write_a = 0;
        write_b = 0;
        write_address = 0;
        write_flags = 0;

        execute_valid = 0;
        execute_a = 0;
        execute_b = 0;

        mem_request = 0;
        mem_write = 0;
        mem_address = 0;
        mem_write_data = 0;

        grant_read_valid = 0;
        grant_write_valid = 0;
        revoke_read_valid = 0;
        revoke_write_valid = 0;

        admin_address = 0;
        admin_yara = 0;

        repeat (3) @(negedge clk);
        rst = 0;

        $display("============================================================");
        $display("IFÁ V4 INTEGRATED YÀRÁ + GENERAL MEMORY TEST");
        $display("============================================================");

        babalawo_mode = 1;

        manager_command(3'd0, 0);
        manager_command(3'd1, 0);

        babalawo_mode = 0;

        // YÀRÁ 0 owns address 3.
        write_memory(4'h3, 8'hAA);

        if (mem_allowed !== 1'b1)
            $fatal(1, "YARA 0 initial write should be allowed");

        babalawo_mode = 1;

        manager_command(3'd0, 1);
        manager_command(3'd1, 1);

        babalawo_mode = 0;

        // YÀRÁ 1 cannot read it yet.
        read_memory(4'h3);

        if (mem_denied !== 1'b1)
            $fatal(1, "YARA 1 read should be denied");

        // Onílẹ̀ grants read access.
        babalawo_mode = 1;
        grant_read(1, 4'h3);
        babalawo_mode = 0;

        read_memory(4'h3);

        if (
            mem_allowed !== 1'b1 ||
            mem_read_data !== 8'hAA
        )
            $fatal(1, "Granted shared-memory read failed");

        // Pause active room. Memory request must not execute.
        babalawo_mode = 1;
        manager_command(3'd2, 1);
        babalawo_mode = 0;

        read_memory(4'h3);

        if (
            mem_allowed !== 1'b0 ||
            mem_denied !== 1'b0
        )
            $fatal(1, "Paused YARA must not issue memory access");

        // Resume it and confirm access returns.
        babalawo_mode = 1;
        manager_command(3'd3, 1);
        manager_command(3'd1, 1);
        babalawo_mode = 0;

        read_memory(4'h3);

        if (
            mem_allowed !== 1'b1 ||
            mem_read_data !== 8'hAA
        )
            $fatal(1, "Resumed YARA should regain granted access");

        $display("");
        $display("FINAL STATE");
        $display("------------------------------------------------------------");
        $display("Valid rooms    = %b", yara_valid);
        $display("Running rooms  = %b", yara_running);
        $display("Active YARA    = %0d", active_yara);
        $display("Memory reads   = %0d", memory_read_count);
        $display("Memory writes  = %0d", memory_write_count);
        $display("Memory denied  = %0d", memory_denied_count);

        $display("============================================================");
        $display("PASS: YÀRÁ execution and General Memory are integrated");
        $display("PASS: Shared memory is denied by default");
        $display("PASS: Onílẹ̀ grants controlled read access");
        $display("PASS: Paused YÀRÁ cannot access General Memory");
        $display("PASS: Resumed YÀRÁ retains its permission");
        $display("============================================================");

        $finish;
    end

endmodule
