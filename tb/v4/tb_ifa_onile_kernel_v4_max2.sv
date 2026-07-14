`timescale 1ns/1ps

module tb_ifa_onile_kernel_v4_max2;

    localparam integer WIDTH      = 8;
    localparam integer OP_WIDTH   = 4;
    localparam integer IR_WIDTH   = 16;

    localparam logic [OP_WIDTH-1:0] OP_PAPO  = 4'h0;
    localparam logic [OP_WIDTH-1:0] OP_YO    = 4'h1;
    localparam logic [OP_WIDTH-1:0] OP_DAGBA = 4'h2;
    localparam logic [OP_WIDTH-1:0] OP_PIN   = 4'h3;
    localparam logic [OP_WIDTH-1:0] OP_KU    = 4'h4;
    localparam logic [OP_WIDTH-1:0] OP_GBE   = 4'h5;
    localparam logic [OP_WIDTH-1:0] OP_SEDA  = 4'h6;
    localparam logic [OP_WIDTH-1:0] OP_JU    = 4'h7;
    localparam logic [OP_WIDTH-1:0] OP_KERE  = 4'h8;

    localparam logic [3:0] EXC_DIV_ZERO =
        4'h2;

    localparam logic [3:0] STATE_POWER_EXTENDED =
        4'h1;
    localparam integer RMU_DEPTH  = 16;
    localparam integer MEM_ADDR_W = 4;
    localparam integer MAX_YARA   = 2;
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
    logic [OP_WIDTH-1:0] execute_op;
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

    logic [OP_WIDTH-1:0] out_op;

    logic [WIDTH-1:0] out_y;
    logic [WIDTH-1:0] out_ra;
    logic [WIDTH-1:0] out_rd;
    logic [WIDTH-1:0] out_r0;
    logic [WIDTH-1:0] out_t;

    logic operation_valid;

    logic exception_valid;
    logic [3:0] exception_code;

    logic state_valid;
    logic [3:0] state_code;

    logic eq_flag;
    logic gt_flag;
    logic lt_flag;

    // Status captured while execute_valid is asserted.
    logic sampled_operation_valid;

    logic sampled_exception_valid;
    logic [3:0] sampled_exception_code;

    logic sampled_state_valid;
    logic [3:0] sampled_state_code;

    logic sampled_eq_flag;
    logic sampled_gt_flag;
    logic sampled_lt_flag;

    logic [OP_WIDTH-1:0] sampled_out_op;
    logic [WIDTH-1:0] sampled_out_y;
    logic [WIDTH-1:0] sampled_out_t;

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
    logic last_command_denied;

    logic last_share_allowed;
    logic last_share_denied;
    logic last_share_done;

    logic last_mem_allowed;
    logic last_mem_denied;
    logic [WIDTH-1:0] last_mem_read_data;

    //==================================================================
    // DUT
    //==================================================================

    ifa_onile_kernel_v4 #(
        .WIDTH      (WIDTH),
        .OP_WIDTH   (OP_WIDTH),
        .IR_WIDTH   (IR_WIDTH),
        .RMU_DEPTH  (RMU_DEPTH),
        .MEM_ADDR_W (MEM_ADDR_W),
        .MAX_YARA   (MAX_YARA)
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
        .execute_op(execute_op),
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

        .out_op(out_op),

        .out_y(out_y),
        .out_ra(out_ra),
        .out_rd(out_rd),
        .out_r0(out_r0),
        .out_t(out_t),

        .operation_valid(operation_valid),

        .exception_valid(exception_valid),
        .exception_code(exception_code),

        .state_valid(state_valid),
        .state_code(state_code),

        .eq_flag(eq_flag),
        .gt_flag(gt_flag),
        .lt_flag(lt_flag),

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

        create_valid  = do_create;
        select_valid  = do_select;
        pause_valid   = do_pause;
        resume_valid  = do_resume;
        destroy_valid = do_destroy;

        @(posedge clk);
        #1;

        last_command_allowed = command_allowed;
        last_command_denied  = command_denied;

        @(negedge clk);

        create_valid  = 1'b0;
        select_valid  = 1'b0;
        pause_valid   = 1'b0;
        resume_valid  = 1'b0;
        destroy_valid = 1'b0;
    end
    endtask

    //==================================================================
    // Context write
    //==================================================================

    task automatic write_context(
        input logic [WIDTH-1:0] pc,
        input logic [IR_WIDTH-1:0] ir,
        input logic [WIDTH-1:0] a,
        input logic [WIDTH-1:0] b,
        input logic [WIDTH-1:0] address,
        input logic [WIDTH-1:0] flags
    );
    begin
        @(negedge clk);

        write_pc      = pc;
        write_ir      = ir;
        write_a       = a;
        write_b       = b;
        write_address = address;
        write_flags   = flags;

        context_write = 1'b1;

        @(posedge clk);
        #1;

        @(negedge clk);

        context_write = 1'b0;
    end
    endtask

    //==================================================================
    // Execute relation
    //==================================================================

    task automatic execute_relation(
        input logic [OP_WIDTH-1:0] operation,
        input logic [WIDTH-1:0] a,
        input logic [WIDTH-1:0] b
    );
    begin
        @(negedge clk);

        execute_op = operation;
        execute_a = a;
        execute_b = b;
        execute_valid = 1'b1;

        @(posedge clk);
        #1;

        @(negedge clk);

        execute_valid = 1'b0;

        sampled_operation_valid = 1'b0;

        sampled_exception_valid = 1'b0;
        sampled_exception_code  = 4'h0;

        sampled_state_valid = 1'b0;
        sampled_state_code  = 4'h0;

        sampled_eq_flag = 1'b0;
        sampled_gt_flag = 1'b0;
        sampled_lt_flag = 1'b0;

        sampled_out_op = {OP_WIDTH{1'b0}};
        sampled_out_y  = {WIDTH{1'b0}};
        sampled_out_t  = {WIDTH{1'b0}};

        #1;

        $display(
            "EXEC YARA=%0d OP=%0h A=%02h B=%02h | hit=%0d miss=%0d | OUT_OP=%0h Y=%02h RA=%02h RD=%02h R0=%02h T=%02h",
            active_yara,
            operation,
            a,
            b,
            rmu_hit,
            rmu_miss,
            out_op,
            out_y,
            out_ra,
            out_rd,
            out_r0,
            out_t
        );
    end
    endtask


    task automatic execute_and_sample_status(
        input logic [OP_WIDTH-1:0] operation,
        input logic [WIDTH-1:0] a,
        input logic [WIDTH-1:0] b
    );
    begin
        //--------------------------------------------------------------
        // Present the native operation before the active clock edge.
        //--------------------------------------------------------------

        @(negedge clk);

        execute_op = operation;
        execute_a = a;
        execute_b = b;
        execute_valid = 1'b1;

        //--------------------------------------------------------------
        // The shared RAU status is combinational, but the returned RMU
        // frame is sequential. Sample both after the active edge while
        // execute_valid is still asserted.
        //--------------------------------------------------------------

        @(posedge clk);
        #1;

        sampled_operation_valid = operation_valid;

        sampled_exception_valid = exception_valid;
        sampled_exception_code  = exception_code;

        sampled_state_valid = state_valid;
        sampled_state_code  = state_code;

        sampled_eq_flag = eq_flag;
        sampled_gt_flag = gt_flag;
        sampled_lt_flag = lt_flag;

        sampled_out_op = out_op;
        sampled_out_y  = out_y;
        sampled_out_t  = out_t;

        $display(
            "STATUS OP=%0h A=%02h B=%02h | valid=%0d exc=%0d exc_code=%0h state=%0d state_code=%0h EQ=%0d GT=%0d LT=%0d | OUT_OP=%0h Y=%02h T=%02h",
            operation,
            a,
            b,
            sampled_operation_valid,
            sampled_exception_valid,
            sampled_exception_code,
            sampled_state_valid,
            sampled_state_code,
            sampled_eq_flag,
            sampled_gt_flag,
            sampled_lt_flag,
            sampled_out_op,
            sampled_out_y,
            sampled_out_t
        );

        //--------------------------------------------------------------
        // End the request only after all outputs have been sampled.
        //--------------------------------------------------------------

        @(negedge clk);

        execute_valid = 1'b0;

        #1;
    end
    endtask

    //==================================================================
    // Grant or revoke frame permission
    //==================================================================

    task automatic administer_frame_permission(
        input logic do_grant,
        input logic do_revoke,
        input logic [YARA_W-1:0] src,
        input logic [YARA_W-1:0] dst
    );
    begin
        @(negedge clk);

        frame_admin_source      = src;
        frame_admin_destination = dst;

        frame_grant_valid  = do_grant;
        frame_revoke_valid = do_revoke;

        @(posedge clk);
        #1;

        @(negedge clk);

        frame_grant_valid  = 1'b0;
        frame_revoke_valid = 1'b0;
    end
    endtask

    //==================================================================
    // Delegate frame
    //==================================================================

    task automatic share_frame(
        input logic [YARA_W-1:0] src,
        input logic [YARA_W-1:0] dst
    );
    begin
        @(negedge clk);

        frame_share_source      = src;
        frame_share_destination = dst;
        frame_share_request     = 1'b1;

        #1;

        last_share_allowed = frame_share_allowed;
        last_share_denied  = frame_share_denied;

        @(posedge clk);
        #1;

        last_share_done = frame_share_done;

        @(negedge clk);

        frame_share_request = 1'b0;
    end
    endtask

    //==================================================================
    // General Memory access
    //==================================================================

    task automatic memory_access(
        input logic do_write,
        input logic [MEM_ADDR_W-1:0] address,
        input logic [WIDTH-1:0] data
    );
    begin
        @(negedge clk);

        mem_write      = do_write;
        mem_address    = address;
        mem_write_data = data;
        mem_request    = 1'b1;

        @(posedge clk);
        #1;

        last_mem_allowed   = mem_allowed;
        last_mem_denied    = mem_denied;
        last_mem_read_data = mem_read_data;

        @(negedge clk);

        mem_request = 1'b0;
    end
    endtask

    //==================================================================
    // Main verification
    //==================================================================

    initial begin
        $dumpfile(
            "sim/v4/ifa_onile_kernel_v4_max2.vcd"
        );

        $dumpvars(
            0,
            tb_ifa_onile_kernel_v4_max2
        );

        clk = 1'b0;
        rst = 1'b1;

        babalawo_mode = 1'b0;

        create_valid  = 1'b0;
        select_valid  = 1'b0;
        pause_valid   = 1'b0;
        resume_valid  = 1'b0;
        destroy_valid = 1'b0;
        command_yara  = '0;

        context_write = 1'b0;

        write_pc      = '0;
        write_ir      = '0;
        write_a       = '0;
        write_b       = '0;
        write_address = '0;
        write_flags   = '0;

        execute_valid = 1'b0;
        execute_op    = OP_PAPO;
        execute_a     = '0;
        execute_b     = '0;

        frame_grant_valid       = 1'b0;
        frame_revoke_valid      = 1'b0;
        frame_admin_source      = '0;
        frame_admin_destination = '0;

        frame_share_request     = 1'b0;
        frame_share_source      = '0;
        frame_share_destination = '0;

        mem_request    = 1'b0;
        mem_write      = 1'b0;
        mem_address    = '0;
        mem_write_data = '0;

        mem_grant_read_valid   = 1'b0;
        mem_grant_write_valid  = 1'b0;
        mem_revoke_read_valid  = 1'b0;
        mem_revoke_write_valid = 1'b0;
        mem_admin_address      = '0;
        mem_admin_yara         = '0;

        last_command_allowed = 1'b0;
        last_command_denied  = 1'b0;

        last_share_allowed = 1'b0;
        last_share_denied  = 1'b0;
        last_share_done    = 1'b0;

        last_mem_allowed   = 1'b0;
        last_mem_denied    = 1'b0;
        last_mem_read_data = '0;

        repeat (3) @(negedge clk);

        rst = 1'b0;

        $display(
            "============================================================"
        );
        $display(
            "IFÁ V4 ONÍLẸ̀ KERNEL MAX_YARA=2 TEST"
        );
        $display(
            "============================================================"
        );

        //==============================================================
        // Create both YÀRÁ under Babaláwo privilege
        //==============================================================

        babalawo_mode = 1'b1;

        lifecycle_command(1,0,0,0,0,0);

        if (!last_command_allowed) begin
            $fatal(1, "CREATE YARA 0 failed");
        end

        lifecycle_command(1,0,0,0,0,1);

        if (!last_command_allowed) begin
            $fatal(1, "CREATE YARA 1 failed");
        end

        //==============================================================
        // Proof 1: independent context state
        //==============================================================

        lifecycle_command(0,1,0,0,0,0);

        if (!last_command_allowed) begin
            $fatal(1, "SELECT YARA 0 failed");
        end

        write_context(
            8'h10,
            16'hA001,
            8'h11,
            8'h22,
            8'h33,
            8'h44
        );

        lifecycle_command(0,1,0,0,0,1);

        if (!last_command_allowed) begin
            $fatal(1, "SELECT YARA 1 failed");
        end

        write_context(
            8'h20,
            16'hB002,
            8'h55,
            8'h66,
            8'h77,
            8'h88
        );

        lifecycle_command(0,1,0,0,0,0);

        if (
            active_pc      !== 8'h10   ||
            active_ir      !== 16'hA001 ||
            active_a       !== 8'h11   ||
            active_b       !== 8'h22   ||
            active_address !== 8'h33   ||
            active_flags   !== 8'h44
        ) begin
            $fatal(
                1,
                "YARA 0 context restore failed"
            );
        end

        lifecycle_command(0,1,0,0,0,1);

        if (
            active_pc      !== 8'h20   ||
            active_ir      !== 16'hB002 ||
            active_a       !== 8'h55   ||
            active_b       !== 8'h66   ||
            active_address !== 8'h77   ||
            active_flags   !== 8'h88
        ) begin
            $fatal(
                1,
                "YARA 1 context restore failed"
            );
        end

        $display(
            "PASS: YARA 0 and YARA 1 preserve independent context"
        );

        //==============================================================
        // Proof 2: same relation misses across rooms
        //==============================================================

        lifecycle_command(0,1,0,0,0,0);

        execute_relation(
            OP_PAPO,
            8'h0D,
            8'h06
        );

        if (rmu_miss !== 1'b1) begin
            $fatal(
                1,
                "YARA 0 first relation must MISS"
            );
        end

        execute_relation(
            OP_PAPO,
            8'h0D,
            8'h06
        );

        if (rmu_hit !== 1'b1) begin
            $fatal(
                1,
                "YARA 0 repeated relation must HIT"
            );
        end

        //==============================================================
        // Proof 2B:
        // The same operands and relation fields under a different
        // operation identity must MISS in the same local RMU.
        //
        // The current RPC stub still emits the same candidate frame,
        // but OP differentiates the relation identity.
        //==============================================================

        execute_relation(
            OP_YO,
            8'h0D,
            8'h06
        );

        if (rmu_miss !== 1'b1) begin
            $fatal(
                1,
                "Different OP with same RA/RD/T must MISS"
            );
        end

        if (out_op !== OP_YO) begin
            $fatal(
                1,
                "Returned operation identity was not preserved"
            );
        end

        execute_relation(
            OP_YO,
            8'h0D,
            8'h06
        );

        if (rmu_hit !== 1'b1) begin
            $fatal(
                1,
                "Repeated same OP relation must HIT"
            );
        end

        $display(
            "PASS: RMU key distinguishes identical relations by OP"
        );

        lifecycle_command(0,1,0,0,0,1);

        execute_relation(
            OP_PAPO,
            8'h0D,
            8'h06
        );

        if (rmu_miss !== 1'b1) begin
            $fatal(
                1,
                "Same relation must MISS in YARA 1"
            );
        end

        execute_relation(
            OP_PAPO,
            8'h0D,
            8'h06
        );

        if (rmu_hit !== 1'b1) begin
            $fatal(
                1,
                "Repeated relation must HIT in YARA 1"
            );
        end

        $display(
            "PASS: Same relation misses across rooms and hits locally"
        );

        //==============================================================
        // Proof 3: local clear isolation through destroy
        //==============================================================

        lifecycle_command(0,0,0,0,1,0);

        if (!last_command_allowed) begin
            $fatal(
                1,
                "DESTROY YARA 0 failed"
            );
        end

        if (yara_valid[0] !== 1'b0) begin
            $fatal(
                1,
                "Destroyed YARA 0 must become invalid"
            );
        end

        lifecycle_command(0,1,0,0,0,1);

        execute_relation(
            OP_PAPO,
            8'h0D,
            8'h06
        );

        if (rmu_hit !== 1'b1) begin
            $fatal(
                1,
                "Destroying YARA 0 affected YARA 1 RMU"
            );
        end

        $display(
            "PASS: Clearing/destroying YARA 0 does not affect YARA 1"
        );

        // Recreate YARA 0 for delegation tests.
        lifecycle_command(1,0,0,0,0,0);
        lifecycle_command(0,1,0,0,0,0);

        //==============================================================
        // Proof 4: permission-gated delegation
        //==============================================================

        execute_relation(
            OP_PAPO,
            8'h21,
            8'h42
        );

        if (rmu_miss !== 1'b1) begin
            $fatal(
                1,
                "YARA 0 relation Y should initially MISS"
            );
        end

        share_frame(0,1);

        if (
            last_share_allowed !== 1'b0 ||
            last_share_denied  !== 1'b1 ||
            last_share_done    !== 1'b0
        ) begin
            $fatal(
                1,
                "Unauthorized delegation was not denied"
            );
        end

        administer_frame_permission(
            1,
            0,
            0,
            1
        );

        // Babaláwo may now be disabled.
        babalawo_mode = 1'b0;

        share_frame(0,1);

        if (
            last_share_allowed !== 1'b1 ||
            last_share_denied  !== 1'b0 ||
            last_share_done    !== 1'b1
        ) begin
            $fatal(
                1,
                "Authorized delegation did not complete"
            );
        end

        if (yara1_imports !== 32'd1) begin
            $fatal(
                1,
                "YARA 1 import counter should be 1"
            );
        end

        babalawo_mode = 1'b1;

        lifecycle_command(0,1,0,0,0,1);

        execute_relation(
            OP_PAPO,
            8'h21,
            8'h42
        );

        if (rmu_hit !== 1'b1) begin
            $fatal(
                1,
                "YARA 1 did not reuse delegated frame"
            );
        end

        $display(
            "PASS: Delegation requires Babalawo-granted Onile permission"
        );

        //==============================================================
        // Proof 5: paused YÀRÁ cannot execute
        //==============================================================

        lifecycle_command(0,0,1,0,0,1);

        if (!last_command_allowed) begin
            $fatal(
                1,
                "PAUSE YARA 1 failed"
            );
        end

        execute_relation(
            OP_PAPO,
            8'h55,
            8'hAA
        );

        if (
            rmu_hit !== 1'b0 ||
            rmu_miss !== 1'b0
        ) begin
            $fatal(
                1,
                "Paused YARA must not execute"
            );
        end

        $display(
            "PASS: Paused YARA cannot execute"
        );

        lifecycle_command(0,0,0,1,0,1);

        //==============================================================
        // Proof 6: General Memory ownership isolation
        //==============================================================

        memory_access(
            1,
            4'h3,
            8'hA5
        );

        if (
            last_mem_allowed !== 1'b1 ||
            last_mem_denied  !== 1'b0
        ) begin
            $fatal(
                1,
                "YARA 1 initial memory write failed"
            );
        end

        lifecycle_command(0,1,0,0,0,0);

        memory_access(
            0,
            4'h3,
            8'h00
        );

        if (
            last_mem_allowed !== 1'b0 ||
            last_mem_denied  !== 1'b1
        ) begin
            $fatal(
                1,
                "Cross-YARA memory read should be denied"
            );
        end

        $display(
            "PASS: General Memory ownership isolation works"
        );

        //==============================================================
        // Final status
        //==============================================================

        $display("");
        $display("FINAL STATUS");
        $display(
            "YARA valid      = %b",
            yara_valid
        );
        $display(
            "YARA running    = %b",
            yara_running
        );
        $display(
            "Switch count    = %0d",
            switch_count
        );
        $display(
            "Manager denied  = %0d",
            manager_denied_count
        );
        $display(
            "Frame allowed   = %0d",
            frame_allowed_count
        );
        $display(
            "Frame denied    = %0d",
            frame_denied_count
        );
        $display(
            "YARA 0 RMU      hits=%0d misses=%0d imports=%0d",
            yara0_hits,
            yara0_misses,
            yara0_imports
        );
        $display(
            "YARA 1 RMU      hits=%0d misses=%0d imports=%0d",
            yara1_hits,
            yara1_misses,
            yara1_imports
        );

        $display(
            "============================================================"
        );
        //==============================================================
        // COMPLETE NATIVE STATUS PATH THROUGH ONÍLẸ̀
        //==============================================================

        lifecycle_command(
            0,1,0,0,0,
            0
        );

        //--------------------------------------------------------------
        // PIN division by zero
        //--------------------------------------------------------------

        execute_and_sample_status(
            OP_PIN,
            8'd29,
            8'd0
        );

        if (
            sampled_operation_valid !== 1'b0 ||
            sampled_exception_valid !== 1'b1 ||
            sampled_exception_code !== EXC_DIV_ZERO
        ) begin
            $fatal(
                1,
                "PIN division-by-zero status failed through kernel"
            );
        end

        $display(
            "PASS: PIN division-by-zero exception reached ONILE"
        );

        //--------------------------------------------------------------
        // GBÉ extended state
        //
        // 255^3 extends above the captured {T,Y} relation window.
        //--------------------------------------------------------------

        execute_and_sample_status(
            OP_GBE,
            8'hFF,
            8'd3
        );

        if (
            sampled_operation_valid !== 1'b1 ||
            sampled_exception_valid !== 1'b0 ||
            sampled_state_valid !== 1'b1 ||
            sampled_state_code !== STATE_POWER_EXTENDED
        ) begin
            $fatal(
                1,
                "GBE extended state failed through kernel"
            );
        end

        $display(
            "PASS: GBE extended IFÁ state reached ONILE"
        );

        //--------------------------------------------------------------
        // SẸ̀DÁ equality
        //--------------------------------------------------------------

        execute_and_sample_status(
            OP_SEDA,
            8'd20,
            8'd20
        );

        if (
            sampled_operation_valid !== 1'b1 ||
            sampled_eq_flag !== 1'b1 ||
            sampled_gt_flag !== 1'b0 ||
            sampled_lt_flag !== 1'b0
        ) begin
            $fatal(
                1,
                "SEDA equality flags failed through kernel"
            );
        end

        //--------------------------------------------------------------
        // SẸ̀DÁ greater relation
        //--------------------------------------------------------------

        execute_and_sample_status(
            OP_SEDA,
            8'd20,
            8'd10
        );

        if (
            sampled_eq_flag !== 1'b0 ||
            sampled_gt_flag !== 1'b1 ||
            sampled_lt_flag !== 1'b0
        ) begin
            $fatal(
                1,
                "SEDA greater flags failed through kernel"
            );
        end

        //--------------------------------------------------------------
        // SẸ̀DÁ lesser relation
        //--------------------------------------------------------------

        execute_and_sample_status(
            OP_SEDA,
            8'd10,
            8'd20
        );

        if (
            sampled_eq_flag !== 1'b0 ||
            sampled_gt_flag !== 1'b0 ||
            sampled_lt_flag !== 1'b1
        ) begin
            $fatal(
                1,
                "SEDA lesser flags failed through kernel"
            );
        end

        $display(
            "PASS: SEDA EQ/GT/LT reached ONILE"
        );

        //--------------------------------------------------------------
        // JÙ predicate
        //--------------------------------------------------------------

        execute_and_sample_status(
            OP_JU,
            8'd20,
            8'd10
        );

        if (
            sampled_operation_valid !== 1'b1 ||
            sampled_gt_flag !== 1'b1 ||
            sampled_out_y !== 8'h01
        ) begin
            $fatal(
                1,
                "JU predicate failed through kernel"
            );
        end

        $display(
            "PASS: JU greater predicate reached ONILE"
        );

        //--------------------------------------------------------------
        // KERÉ predicate
        //--------------------------------------------------------------

        execute_and_sample_status(
            OP_KERE,
            8'd5,
            8'd10
        );

        if (
            sampled_operation_valid !== 1'b1 ||
            sampled_lt_flag !== 1'b1 ||
            sampled_out_y !== 8'h01
        ) begin
            $fatal(
                1,
                "KERE predicate failed through kernel"
            );
        end

        $display(
            "PASS: KERE lesser predicate reached ONILE"
        );


        $display(
            "============================================================"
        );

        $display(
            "PASS: COMPLETE NATIVE IFÁ STATUS PATH VERIFIED"
        );

        $display(
            "PASS: PIN DIVISION-BY-ZERO EXCEPTION REACHED ONÍLẸ̀"
        );

        $display(
            "PASS: GBÉ EXTENDED STATE REACHED ONÍLẸ̀"
        );

        $display(
            "PASS: SẸ̀DÁ EQ/GT/LT REACHED ONÍLẸ̀"
        );

        $display(
            "PASS: JÙ AND KERÉ PREDICATES REACHED ONÍLẸ̀"
        );

        $display(
            "PASS: ONILE KERNEL MAX_YARA=2 VERIFICATION COMPLETE"
        );

        $display(
            "============================================================"
        );

        $finish;
    end

endmodule
