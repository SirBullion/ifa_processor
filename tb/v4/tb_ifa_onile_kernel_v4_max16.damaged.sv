`timescale 1ns/1ps

module tb_ifa_onile_kernel_v4_max16;

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

    // Native IFÁ status codes used by this testbench.
    localparam logic [3:0] EXC_DIV_ZERO =
        4'h2;

    localparam logic [3:0] STATE_POWER_EXTENDED =
        4'h1;

    localparam integer RMU_DEPTH  = 16;
    localparam integer MEM_ADDR_W = 4;
    localparam integer MAX_YARA   = 16;
    localparam integer YARA_W     = 4;

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

    // Sampled while execute_valid remains active.
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
    logic last_share_allowed;
    logic last_share_denied;
    logic last_share_done;

    integer i;

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

    task automatic execute_native_status(
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

        // The frame is returned by the sequential local RMU.
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
            "MAX16 STATUS YARA=%0d OP=%0h A=%02h B=%02h | valid=%0d exc=%0d code=%0h state=%0d state_code=%0h EQ=%0d GT=%0d LT=%0d | OUT_OP=%0h Y=%02h T=%02h",
            active_yara,
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
    end
    endtask


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

        @(negedge clk);

        create_valid  = 1'b0;
        select_valid  = 1'b0;
        pause_valid   = 1'b0;
        resume_valid  = 1'b0;
        destroy_valid = 1'b0;
    end
    endtask

    task automatic write_context_for_room(
        input logic [YARA_W-1:0] room
    );
    begin
        lifecycle_command(0,1,0,0,0,room);

                if (sampled_operation_valid !== 1'b1) begin
            $fatal(
                1,
                "MAX16 DAGBA operation_valid failed"
            );
        end

        if (sampled_out_op !== OP_DAGBA) begin
            $fatal(
                1,
                "MAX16 DAGBA operation identity failed"
            );
        end

        if (sampled_out_y !== 8'h82) begin
            $fatal(
                1,
                "MAX16 DAGBA Y failed: expected 82 got %02h",
                sampled_out_y
            );
        end

        if (sampled_out_t !== 8'h08) begin
            $fatal(
                1,
                "MAX16 DAGBA T failed: expected 08 got %02h",
                sampled_out_t
            );
        end


        $display(
            "PASS: YARA 3 DAGBA native frame verified"
        );

        //--------------------------------------------------------------
        // YÀRÁ 7 — PIN
        //
        // 29 / 6 = quotient 4, remainder 5
        //--------------------------------------------------------------

        lifecycle_command(
            0,1,0,0,0,
            4'd7
        );

        execute_native_status(
            OP_PIN,
            8'd29,
            8'd6
        );

        if (
            sampled_operation_valid !== 1'b1 ||
            sampled_out_op !== OP_PIN ||
            sampled_out_y !== 8'd4 ||
            sampled_out_t !== 8'd5
        ) begin
            $fatal(
                1,
                "MAX16 PIN failed in YARA 7"
            );
        end

        $display(
            "PASS: YARA 7 PIN native frame verified"
        );

        //--------------------------------------------------------------
        // YÀRÁ 7 — PIN division-by-zero exception
        //--------------------------------------------------------------

        execute_native_status(
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
                "MAX16 PIN division-zero status failed"
            );
        end

        $display(
            "PASS: YARA 7 PIN exception verified"
        );

        //--------------------------------------------------------------
        // YÀRÁ 9 — GBÉ extended state
        //--------------------------------------------------------------

        lifecycle_command(
            0,1,0,0,0,
            4'd9
        );

        execute_native_status(
            OP_GBE,
            8'hFF,
            8'd3
        );

        if (
            sampled_operation_valid !== 1'b1 ||
            sampled_state_valid !== 1'b1 ||
            sampled_state_code !== STATE_POWER_EXTENDED
        ) begin
            $fatal(
                1,
                "MAX16 GBE extended state failed in YARA 9"
            );
        end

        $display(
            "PASS: YARA 9 GBE extended state verified"
        );

        //--------------------------------------------------------------
        // YÀRÁ 12 — SẸ̀DÁ greater relation
        //--------------------------------------------------------------

        lifecycle_command(
            0,1,0,0,0,
            4'd12
        );

        execute_native_status(
            OP_SEDA,
            8'd20,
            8'd10
        );

        if (
            sampled_operation_valid !== 1'b1 ||
            sampled_eq_flag !== 1'b0 ||
            sampled_gt_flag !== 1'b1 ||
            sampled_lt_flag !== 1'b0
        ) begin
            $fatal(
                1,
                "MAX16 SEDA flags failed in YARA 12"
            );
        end

        $display(
            "PASS: YARA 12 SEDA flags verified"
        );

        //--------------------------------------------------------------
        // YÀRÁ 15 — KERÉ
        //--------------------------------------------------------------

        lifecycle_command(
            0,1,0,0,0,
            4'd15
        );

        execute_native_status(
            OP_KERE,
            8'd5,
            8'd10
        );

        if (
            sampled_operation_valid !== 1'b1 ||
            sampled_out_op !== OP_KERE ||
            sampled_out_y !== 8'h01 ||
            sampled_lt_flag !== 1'b1
        ) begin
            $fatal(
                1,
                "MAX16 KERE failed in YARA 15"
            );
        end

        $display(
            "PASS: YARA 15 KERE predicate verified"
        );

        $display(
            "============================================================"
        );

        $display(
            "PASS: MAX16 COMPLETE NATIVE MATHEMATICS VERIFIED"
        );

        $display(
            "PASS: NATIVE STATUS WORKS ACROSS ARBITRARY YARA IDS"
        );

        $display(
            "============================================================"
        );

        $finish;
    end

endmodule
