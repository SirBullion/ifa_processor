`timescale 1ns/1ps

module tb_ifa_onile_kernel_v4_scale_smoke #(
    parameter integer MAX_YARA = 32,
    parameter integer WIDTH = 8,
    parameter integer IR_WIDTH = 16,
    parameter integer RMU_DEPTH = 4,
    parameter integer MEM_ADDR_W = 4,
    parameter integer YARA_W =
        (MAX_YARA <= 1) ? 1 : $clog2(MAX_YARA)
);

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

    logic [WIDTH-1:0] write_pc;
    logic [IR_WIDTH-1:0] write_ir;
    logic [WIDTH-1:0] write_a;
    logic [WIDTH-1:0] write_b;
    logic [WIDTH-1:0] write_address;
    logic [WIDTH-1:0] write_flags;

    logic execute_valid;
    logic [WIDTH-1:0] execute_a;
    logic [WIDTH-1:0] execute_b;

    logic frame_grant_valid;
    logic frame_revoke_valid;

    logic [YARA_W-1:0] frame_admin_source;
    logic [YARA_W-1:0] frame_admin_destination;

    logic frame_share_request;

    logic [YARA_W-1:0] frame_share_source;
    logic [YARA_W-1:0] frame_share_destination;

    logic mem_request;
    logic mem_write;

    logic [MEM_ADDR_W-1:0] mem_address;
    logic [WIDTH-1:0] mem_write_data;

    logic [WIDTH-1:0] mem_read_data;
    logic mem_allowed;
    logic mem_denied;

    logic mem_grant_read_valid;
    logic mem_grant_write_valid;
    logic mem_revoke_read_valid;
    logic mem_revoke_write_valid;

    logic [MEM_ADDR_W-1:0] mem_admin_address;
    logic [YARA_W-1:0] mem_admin_yara;

    logic [YARA_W-1:0] active_yara;
    logic active_valid;
    logic active_running;

    logic [MAX_YARA-1:0] yara_valid;
    logic [MAX_YARA-1:0] yara_running;

    logic command_allowed;
    logic command_denied;

    logic [WIDTH-1:0] active_pc;
    logic [IR_WIDTH-1:0] active_ir;
    logic [WIDTH-1:0] active_a;
    logic [WIDTH-1:0] active_b;
    logic [WIDTH-1:0] active_address;
    logic [WIDTH-1:0] active_flags;

    logic rmu_hit;
    logic rmu_miss;

    logic [WIDTH-1:0] out_y;
    logic [WIDTH-1:0] out_ra;
    logic [WIDTH-1:0] out_rd;
    logic [WIDTH-1:0] out_r0;
    logic [WIDTH-1:0] out_t;

    logic frame_share_allowed;
    logic frame_share_denied;
    logic frame_share_done;

    logic [31:0] switch_count;
    logic [31:0] manager_denied_count;

    logic [31:0] frame_allowed_count;
    logic [31:0] frame_denied_count;

    logic [31:0] memory_read_count;
    logic [31:0] memory_write_count;
    logic [31:0] memory_denied_count;

    logic [31:0] yara0_hits;
    logic [31:0] yara0_misses;
    logic [31:0] yara0_imports;

    logic [31:0] yara1_hits;
    logic [31:0] yara1_misses;
    logic [31:0] yara1_imports;

    logic last_command_allowed;

    localparam logic [YARA_W-1:0] LOW_ID =
        {YARA_W{1'b0}};

    localparam logic [YARA_W-1:0] MID_ID =
        MAX_YARA / 2;

    localparam logic [YARA_W-1:0] HIGH_ID =
        MAX_YARA - 1;

    //==================================================================
    // DUT
    //==================================================================

    ifa_onile_kernel_v4 #(
        .WIDTH(WIDTH),
        .IR_WIDTH(IR_WIDTH),
        .RMU_DEPTH(RMU_DEPTH),
        .MEM_ADDR_W(MEM_ADDR_W),
        .MAX_YARA(MAX_YARA)
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

        .frame_grant_valid(frame_grant_valid),
        .frame_revoke_valid(frame_revoke_valid),
        .frame_admin_source(frame_admin_source),
        .frame_admin_destination(frame_admin_destination),

        .frame_share_request(frame_share_request),
        .frame_share_source(frame_share_source),
        .frame_share_destination(frame_share_destination),

        .mem_request(mem_request),
        .mem_write(mem_write),
        .mem_address(mem_address),
        .mem_write_data(mem_write_data),

        .mem_read_data(mem_read_data),
        .mem_allowed(mem_allowed),
        .mem_denied(mem_denied),

        .mem_grant_read_valid(mem_grant_read_valid),
        .mem_grant_write_valid(mem_grant_write_valid),
        .mem_revoke_read_valid(mem_revoke_read_valid),
        .mem_revoke_write_valid(mem_revoke_write_valid),

        .mem_admin_address(mem_admin_address),
        .mem_admin_yara(mem_admin_yara),

        .active_yara(active_yara),
        .active_valid(active_valid),
        .active_running(active_running),

        .yara_valid(yara_valid),
        .yara_running(yara_running),

        .command_allowed(command_allowed),
        .command_denied(command_denied),

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

        .frame_share_allowed(frame_share_allowed),
        .frame_share_denied(frame_share_denied),
        .frame_share_done(frame_share_done),

        .switch_count(switch_count),
        .manager_denied_count(manager_denied_count),

        .frame_allowed_count(frame_allowed_count),
        .frame_denied_count(frame_denied_count),

        .memory_read_count(memory_read_count),
        .memory_write_count(memory_write_count),
        .memory_denied_count(memory_denied_count),

        .yara0_hits(yara0_hits),
        .yara0_misses(yara0_misses),
        .yara0_imports(yara0_imports),

        .yara1_hits(yara1_hits),
        .yara1_misses(yara1_misses),
        .yara1_imports(yara1_imports)
    );

    always #5 clk = ~clk;

    //==================================================================
    // Lifecycle command
    //==================================================================

    task automatic lifecycle_command(
        input logic do_create,
        input logic do_select,
        input logic do_pause,
        input logic do_resume,
        input logic do_destroy,
        input logic [YARA_W-1:0] room
    );
    begin
        @(negedge clk);

        command_yara = room;

        create_valid = do_create;
        select_valid = do_select;
        pause_valid = do_pause;
        resume_valid = do_resume;
        destroy_valid = do_destroy;

        @(posedge clk);
        #1;

        last_command_allowed = command_allowed;

        @(negedge clk);

        create_valid = 1'b0;
        select_valid = 1'b0;
        pause_valid = 1'b0;
        resume_valid = 1'b0;
        destroy_valid = 1'b0;
    end
    endtask

    //==================================================================
    // Write active context
    //==================================================================

    task automatic write_active_context(
        input logic [WIDTH-1:0] value
    );
    begin
        @(negedge clk);

        write_pc = value;
        write_ir = {8'hA5, value};
        write_a = value + 8'h01;
        write_b = value + 8'h02;
        write_address = value + 8'h03;
        write_flags = value + 8'h04;

        context_write = 1'b1;

        @(posedge clk);
        #1;

        @(negedge clk);

        context_write = 1'b0;
    end
    endtask

    //==================================================================
    // Verify active context
    //==================================================================

    task automatic verify_active_context(
        input logic [WIDTH-1:0] value,
        input logic [YARA_W-1:0] expected_room
    );
    begin
        #1;

        if (
            active_yara !== expected_room ||
            active_pc !== value ||
            active_ir !== {8'hA5, value} ||
            active_a !== value + 8'h01 ||
            active_b !== value + 8'h02 ||
            active_address !== value + 8'h03 ||
            active_flags !== value + 8'h04
        ) begin
            $fatal(
                1,
                "Context mismatch for YARA %0d",
                expected_room
            );
        end
    end
    endtask

    //==================================================================
    // Execute relation
    //==================================================================

    task automatic execute_relation(
        input logic [WIDTH-1:0] a,
        input logic [WIDTH-1:0] b
    );
    begin
        @(negedge clk);

        execute_a = a;
        execute_b = b;
        execute_valid = 1'b1;

        @(posedge clk);
        #1;

        @(negedge clk);

        execute_valid = 1'b0;

        #1;
    end
    endtask

    //==================================================================
    // Main smoke test
    //==================================================================

    initial begin
        clk = 1'b0;
        rst = 1'b1;

        babalawo_mode = 1'b0;

        create_valid = 1'b0;
        select_valid = 1'b0;
        pause_valid = 1'b0;
        resume_valid = 1'b0;
        destroy_valid = 1'b0;

        command_yara = '0;

        context_write = 1'b0;

        write_pc = '0;
        write_ir = '0;
        write_a = '0;
        write_b = '0;
        write_address = '0;
        write_flags = '0;

        execute_valid = 1'b0;
        execute_a = '0;
        execute_b = '0;

        frame_grant_valid = 1'b0;
        frame_revoke_valid = 1'b0;
        frame_admin_source = '0;
        frame_admin_destination = '0;

        frame_share_request = 1'b0;
        frame_share_source = '0;
        frame_share_destination = '0;

        mem_request = 1'b0;
        mem_write = 1'b0;
        mem_address = '0;
        mem_write_data = '0;

        mem_grant_read_valid = 1'b0;
        mem_grant_write_valid = 1'b0;
        mem_revoke_read_valid = 1'b0;
        mem_revoke_write_valid = 1'b0;

        mem_admin_address = '0;
        mem_admin_yara = '0;

        last_command_allowed = 1'b0;

        repeat (3) @(negedge clk);

        rst = 1'b0;
        babalawo_mode = 1'b1;

        $display(
            "============================================================"
        );

        $display(
            "IFÁ V4 SCALE SMOKE TEST MAX_YARA=%0d",
            MAX_YARA
        );

        $display(
            "LOW=%0d MID=%0d HIGH=%0d YARA_W=%0d",
            LOW_ID,
            MID_ID,
            HIGH_ID,
            YARA_W
        );

        $display(
            "============================================================"
        );

        //==============================================================
        // Create low, middle and highest YÀRÁ IDs
        //==============================================================

        lifecycle_command(
            1,0,0,0,0,
            LOW_ID
        );

        if (!last_command_allowed) begin
            $fatal(
                1,
                "CREATE failed for LOW_ID"
            );
        end

        lifecycle_command(
            1,0,0,0,0,
            MID_ID
        );

        if (!last_command_allowed) begin
            $fatal(
                1,
                "CREATE failed for MID_ID"
            );
        end

        lifecycle_command(
            1,0,0,0,0,
            HIGH_ID
        );

        if (!last_command_allowed) begin
            $fatal(
                1,
                "CREATE failed for HIGH_ID"
            );
        end

        $display(
            "PASS: Created low, middle and high YARA IDs"
        );

        //==============================================================
        // Write unique context to each selected room
        //==============================================================

        lifecycle_command(
            0,1,0,0,0,
            LOW_ID
        );

        write_active_context(
            8'h10
        );

        lifecycle_command(
            0,1,0,0,0,
            MID_ID
        );

        write_active_context(
            8'h40
        );

        lifecycle_command(
            0,1,0,0,0,
            HIGH_ID
        );

        write_active_context(
            8'h70
        );

        //==============================================================
        // Restore each context
        //==============================================================

        lifecycle_command(
            0,1,0,0,0,
            LOW_ID
        );

        verify_active_context(
            8'h10,
            LOW_ID
        );

        lifecycle_command(
            0,1,0,0,0,
            MID_ID
        );

        verify_active_context(
            8'h40,
            MID_ID
        );

        lifecycle_command(
            0,1,0,0,0,
            HIGH_ID
        );

        verify_active_context(
            8'h70,
            HIGH_ID
        );

        $display(
            "PASS: Indexed context selection works"
        );

        //==============================================================
        // Same relation must MISS independently
        //==============================================================

        lifecycle_command(
            0,1,0,0,0,
            LOW_ID
        );

        execute_relation(
            8'h0D,
            8'h06
        );

        if (rmu_miss !== 1'b1) begin
            $fatal(
                1,
                "LOW_ID first relation should MISS"
            );
        end

        lifecycle_command(
            0,1,0,0,0,
            MID_ID
        );

        execute_relation(
            8'h0D,
            8'h06
        );

        if (rmu_miss !== 1'b1) begin
            $fatal(
                1,
                "MID_ID first relation should MISS"
            );
        end

        lifecycle_command(
            0,1,0,0,0,
            HIGH_ID
        );

        execute_relation(
            8'h0D,
            8'h06
        );

        if (rmu_miss !== 1'b1) begin
            $fatal(
                1,
                "HIGH_ID first relation should MISS"
            );
        end

        $display(
            "PASS: Local RMU isolation works at scaled IDs"
        );

        //==============================================================
        // Repeat relation in highest room
        //==============================================================

        execute_relation(
            8'h0D,
            8'h06
        );

        if (rmu_hit !== 1'b1) begin
            $fatal(
                1,
                "HIGH_ID repeated relation should HIT"
            );
        end

        //==============================================================
        // Destroy middle room only
        //==============================================================

        lifecycle_command(
            0,0,0,0,1,
            MID_ID
        );

        if (!last_command_allowed) begin
            $fatal(
                1,
                "DESTROY failed for MID_ID"
            );
        end

        if (yara_valid[MID_ID] !== 1'b0) begin
            $fatal(
                1,
                "MID_ID remained valid after DESTROY"
            );
        end

        //==============================================================
        // Highest room must still retain its RMU
        //==============================================================

        lifecycle_command(
            0,1,0,0,0,
            HIGH_ID
        );

        execute_relation(
            8'h0D,
            8'h06
        );

        if (rmu_hit !== 1'b1) begin
            $fatal(
                1,
                "Destroying MID_ID affected HIGH_ID RMU"
            );
        end

        $display(
            "PASS: Indexed destroy clears only selected YARA"
        );

        $display(
            "============================================================"
        );

        $display(
            "PASS: SCALE SMOKE TEST MAX_YARA=%0d COMPLETE",
            MAX_YARA
        );

        $display(
            "============================================================"
        );

        $finish;
    end

endmodule
