//======================================================================
// IFÁ Processor V4
// ONÍLẸ̀ Kernel
//
// Official architecture:
//
//                        OHÙN IFÁ
//                            │
//                            ▼
//                       ONÍLẸ̀ Kernel
//          ┌─────────────────┼─────────────────┐
//          │                 │                 │
//          ▼                 ▼                 ▼
//     YÀRÁ Manager      Context Bank      Supervisor
//          │                 │                 │
//          └────────────┬────┴─────┬──────────┘
//                       │          │
//                       ▼          ▼
//                  Active YÀRÁ   Permissions
//                       │
//                       ▼
//                  One Shared RPC
//                       │
//                       ▼
//                Local RMU[active_yara]
//
// The RPC is shared.
// Each YÀRÁ owns independent context and local RMU state.
//======================================================================

module ifa_onile_kernel_v45 #(
    parameter integer WIDTH      = 8,
    parameter integer OP_WIDTH   = 4,
    parameter integer IR_WIDTH   = 16,
    parameter integer RMU_DEPTH   = 16,
    parameter integer MEM_ADDR_W  = 4,
    parameter integer STACK_DEPTH = 16,

    parameter integer MAX_YARA    = 2,

    parameter integer YARA_W =
        (MAX_YARA <= 1) ? 1 : $clog2(MAX_YARA),

    parameter integer STACK_SP_W =
        (STACK_DEPTH <= 1) ? 1 : $clog2(STACK_DEPTH),

    // Canonical IFÁ call/relation-stack frame:
    //
    // RETURN_PC
    // OP
    // Y, RA, RD, R0, T
    // VALID
    // EXC, EXC_CODE
    // STATE, STATE_CODE
    // EQ, GT, LT
    // Caller A, B, Address (V4.5 language-call extension)
    //
    parameter integer RELATION_STACK_WIDTH =
        (9 * WIDTH) + OP_WIDTH + 14
)(
    input  logic                       clk,
    input  logic                       rst,

    //==================================================================
    // Babaláwo privilege
    //==================================================================

    input  logic                       babalawo_mode,

    //==================================================================
    // YÀRÁ lifecycle commands
    //==================================================================

    input  logic                       create_valid,
    input  logic                       select_valid,
    input  logic                       pause_valid,
    input  logic                       resume_valid,
    input  logic                       destroy_valid,

    input  logic [YARA_W-1:0]          command_yara,

    //==================================================================
    // Context update
    //==================================================================

    input  logic                       context_write,

    input  logic [WIDTH-1:0]           write_pc,
    input  logic [IR_WIDTH-1:0]        write_ir,
    input  logic [WIDTH-1:0]           write_a,
    input  logic [WIDTH-1:0]           write_b,
    input  logic [WIDTH-1:0]           write_address,
    input  logic [WIDTH-1:0]           write_flags,
    input  logic [WIDTH-1:0]           write_sp,

    //==================================================================
    // Shared stack request
    //==================================================================

    input  logic                       stack_write_valid,
    input  logic                       stack_read_valid,

    // Address selected by the executor for this transaction:
    // RPUSH uses active_sp; RPOP uses active_sp - 1.
    input  logic [WIDTH-1:0]           stack_access_sp,

    input  logic [RELATION_STACK_WIDTH-1:0]
                                              stack_write_data,

    output logic [RELATION_STACK_WIDTH-1:0]
                                              stack_read_data,

    output logic                       stack_write_done,
    output logic                       stack_read_done,
    output logic                       stack_allowed,
    output logic                       stack_denied,

    //==================================================================
    // Relation execution
    //==================================================================

    input  logic                       execute_valid,

    // Native IFÁ mathematical operation identity.
    //
    // OP is part of the local RMU key:
    //
    //     K = {OP, RA, RD, T}
    //
    input  logic [OP_WIDTH-1:0]        execute_op,

    input  logic [WIDTH-1:0]           execute_a,
    input  logic [WIDTH-1:0]           execute_b,

    //==================================================================
    // Frame permission administration
    //==================================================================

    input  logic                       frame_grant_valid,
    input  logic                       frame_revoke_valid,

    input  logic [YARA_W-1:0]          frame_admin_source,
    input  logic [YARA_W-1:0]          frame_admin_destination,

    //==================================================================
    // Frame delegation request
    //==================================================================

    input  logic                       frame_share_request,
    input  logic [YARA_W-1:0]          frame_share_source,
    input  logic [YARA_W-1:0]          frame_share_destination,

    //==================================================================
    // Active-YÀRÁ relation restoration
    //==================================================================

    input  logic                       restore_valid,

    input  logic [OP_WIDTH-1:0]        restore_op,

    input  logic [WIDTH-1:0]           restore_y,
    input  logic [WIDTH-1:0]           restore_ra,
    input  logic [WIDTH-1:0]           restore_rd,
    input  logic [WIDTH-1:0]           restore_r0,
    input  logic [WIDTH-1:0]           restore_t,

    output logic                       restore_done,

    //==================================================================
    // General Memory request
    //==================================================================

    input  logic                       mem_request,
    input  logic                       mem_write,
    input  logic [MEM_ADDR_W-1:0]      mem_address,
    input  logic [WIDTH-1:0]           mem_write_data,

    output logic [WIDTH-1:0]           mem_read_data,
    output logic                       mem_allowed,
    output logic                       mem_denied,

    //==================================================================
    // General Memory permission administration
    //==================================================================

    input  logic                       mem_grant_read_valid,
    input  logic                       mem_grant_write_valid,
    input  logic                       mem_revoke_read_valid,
    input  logic                       mem_revoke_write_valid,

    input  logic [MEM_ADDR_W-1:0]      mem_admin_address,
    input  logic [YARA_W-1:0]          mem_admin_yara,

    //==================================================================
    // Active YÀRÁ state
    //==================================================================

    output logic [YARA_W-1:0]          active_yara,
    output logic                       active_valid,
    output logic                       active_running,

    output logic [MAX_YARA-1:0]        yara_valid,
    output logic [MAX_YARA-1:0]        yara_running,

    output logic                       command_allowed,
    output logic                       command_denied,

    //==================================================================
    // Active context
    //==================================================================

    output logic [WIDTH-1:0]           active_pc,
    output logic [IR_WIDTH-1:0]        active_ir,
    output logic [WIDTH-1:0]           active_a,
    output logic [WIDTH-1:0]           active_b,
    output logic [WIDTH-1:0]           active_address,
    output logic [WIDTH-1:0]           active_flags,
    output logic [WIDTH-1:0]           active_sp,

    //==================================================================
    // Active relation result
    //==================================================================

    output logic                       rmu_hit,
    output logic                       rmu_miss,

    // Operation identity belonging to the returned Relation Frame.
    output logic [OP_WIDTH-1:0]        out_op,

    output logic [WIDTH-1:0]           out_y,
    output logic [WIDTH-1:0]           out_ra,
    output logic [WIDTH-1:0]           out_rd,
    output logic [WIDTH-1:0]           out_r0,
    output logic [WIDTH-1:0]           out_t,

    // Native IFÁ operation status.
    // These remain outside:
    //
    //     FRAME = {Y, RA, RD, R0, T}
    //     KEY   = {OP, RA, RD, T}
    //
    output logic                       operation_valid,

    output logic                       exception_valid,
    output logic [3:0]                 exception_code,

    output logic                       state_valid,
    output logic [3:0]                 state_code,

    output logic                       eq_flag,
    output logic                       gt_flag,
    output logic                       lt_flag,

    //==================================================================
    // Frame delegation result
    //==================================================================

    output logic                       frame_share_allowed,
    output logic                       frame_share_denied,
    output logic                       frame_share_done,

    //==================================================================
    // Statistics
    //==================================================================

    output logic [31:0]                switch_count,
    output logic [31:0]                manager_denied_count,

    output logic [31:0]                frame_allowed_count,
    output logic [31:0]                frame_denied_count,

    output logic [31:0]                memory_read_count,
    output logic [31:0]                memory_write_count,
    output logic [31:0]                memory_denied_count,

    // Temporary two-YÀRÁ RMU statistics.
    output logic [31:0]                yara0_hits,
    output logic [31:0]                yara0_misses,
    output logic [31:0]                yara0_imports,

    output logic [31:0]                yara1_hits,
    output logic [31:0]                yara1_misses,
    output logic [31:0]                yara1_imports
);

    //==================================================================
    // Internal signals
    //==================================================================

    logic [MAX_YARA-1:0] clear_yara;

    logic execute_guarded;
    logic context_write_guarded;
    logic mem_request_guarded;
    logic stack_write_guarded;
    logic stack_read_guarded;

    logic frame_explicit_permission;

    logic frame_fabric_denied;

    logic fabric_operation_valid;

    logic fabric_exception_valid;
    logic [3:0] fabric_exception_code;

    logic fabric_state_valid;
    logic [3:0] fabric_state_code;

    logic fabric_eq_flag;
    logic fabric_gt_flag;
    logic fabric_lt_flag;

    logic address_owned;
    logic [YARA_W-1:0] address_owner;

    logic active_read_permission;
    logic active_write_permission;

    //==================================================================
    // YÀRÁ Manager
    //==================================================================

    ifa_yara_manager #(
        .MAX_YARA(MAX_YARA)
    ) yara_manager (
        .clk              (clk),
        .rst              (rst),

        .babalawo_mode    (babalawo_mode),

        .create_valid     (create_valid),
        .select_valid     (select_valid),
        .pause_valid      (pause_valid),
        .resume_valid     (resume_valid),
        .destroy_valid    (destroy_valid),

        .command_yara     (command_yara),

        .active_yara      (active_yara),
        .active_valid     (active_valid),
        .active_running   (active_running),

        .yara_valid       (yara_valid),
        .yara_running     (yara_running),

        .clear_yara       (clear_yara),

        .command_allowed  (command_allowed),
        .command_denied   (command_denied),

        .switch_count     (switch_count),
        .denied_count     (manager_denied_count)
    );

    //==================================================================
    // Execution guards
    //
    // A paused, destroyed or uncreated YÀRÁ cannot:
    //
    //   - update context
    //   - execute through the RPC
    //   - access General Memory
    //==================================================================

    always_comb begin
        context_write_guarded =
            context_write &&
            active_valid &&
            active_running;

        execute_guarded =
            execute_valid &&
            active_valid &&
            active_running;

        mem_request_guarded =
            mem_request &&
            active_valid &&
            active_running;

        stack_write_guarded =
            stack_write_valid &&
            active_valid &&
            active_running;

        stack_read_guarded =
            stack_read_valid &&
            active_valid &&
            active_running;
    end

    //==================================================================
    // Context Bank
    //==================================================================

    ifa_yara_context_bank #(
        .WIDTH      (WIDTH),
        .IR_WIDTH   (IR_WIDTH),
        .MAX_YARA   (MAX_YARA)
    ) context_bank (
        .clk            (clk),
        .rst            (rst),

        .active_yara    (active_yara),

        .context_write  (context_write_guarded),

        .write_pc       (write_pc),
        .write_ir       (write_ir),
        .write_a        (write_a),
        .write_b        (write_b),
        .write_address  (write_address),
        .write_flags    (write_flags),
        .write_sp       (write_sp),

        .clear_yara     (clear_yara),

        .read_pc        (active_pc),
        .read_ir        (active_ir),
        .read_a         (active_a),
        .read_b         (active_b),
        .read_address   (active_address),
        .read_flags     (active_flags),
        .read_sp        (active_sp)
    );

    //==================================================================
    // Onílẹ̀ Frame-Permission Supervisor
    //
    // Babaláwo modifies the permission matrix.
    // Onílẹ̀ enforces stored permissions during normal operation.
    //==================================================================

    ifa_onile_supervisor #(
        .MAX_YARA(MAX_YARA)
    ) frame_supervisor (
        .clk                      (clk),
        .rst                      (rst),

        .babalawo_mode            (babalawo_mode),

        .grant_valid              (frame_grant_valid),
        .revoke_valid             (frame_revoke_valid),

        .admin_source_yara        (frame_admin_source),
        .admin_destination_yara   (
            frame_admin_destination
        ),

        .share_request            (frame_share_request),
        .request_source_yara      (frame_share_source),
        .request_destination_yara (
            frame_share_destination
        ),

        .share_allowed            (frame_share_allowed),
        .share_denied             (frame_share_denied),

        .explicit_permission      (
            frame_explicit_permission
        ),

        .allowed_count            (frame_allowed_count),
        .denied_count             (frame_denied_count)
    );

    //==================================================================
    // Shared RPC and Local RMU Bank
    //
    // The supervisor's result becomes the authorization input to the
    // delegation fabric.
    //==================================================================

    ifa_yara_frame_share_core_v45 #(
        .WIDTH      (WIDTH),
        .OP_WIDTH   (OP_WIDTH),
        .DEPTH      (RMU_DEPTH),
        .MAX_YARA   (MAX_YARA)
    ) relation_fabric (
        .clk                       (clk),
        .rst                       (rst),

        .active_yara               (active_yara),

        .in_valid                  (execute_guarded),
        .execute_op                (execute_op),

        .A                         (execute_a),
        .B                         (execute_b),

        .clear_yara                (clear_yara),

        .share_commit              (frame_share_request),
        .share_source_yara         (frame_share_source),
        .share_destination_yara    (
            frame_share_destination
        ),

        .share_authorized          (frame_share_allowed),

        .restore_valid             (restore_valid),

        .restore_op                (restore_op),

        .restore_y                 (restore_y),
        .restore_ra                (restore_ra),
        .restore_rd                (restore_rd),
        .restore_r0                (restore_r0),
        .restore_t                 (restore_t),

        .restore_done              (restore_done),

        .rmu_hit                   (rmu_hit),
        .rmu_miss                  (rmu_miss),

        .share_done                (frame_share_done),
        .share_denied              (frame_fabric_denied),

        .out_op                    (out_op),

        .out_y                     (out_y),
        .out_ra                    (out_ra),
        .out_rd                    (out_rd),
        .out_r0                    (out_r0),
        .out_t                     (out_t),

        .operation_valid           (fabric_operation_valid),

        .exception_valid           (fabric_exception_valid),
        .exception_code            (fabric_exception_code),

        .state_valid               (fabric_state_valid),
        .state_code                (fabric_state_code),

        .eq_flag                   (fabric_eq_flag),
        .gt_flag                   (fabric_gt_flag),
        .lt_flag                   (fabric_lt_flag),

        .yara0_hits                (yara0_hits),
        .yara0_misses              (yara0_misses),
        .yara0_imports             (yara0_imports),

        .yara1_hits                (yara1_hits),
        .yara1_misses              (yara1_misses),
        .yara1_imports             (yara1_imports)
    );

    //==================================================================
    // Shared General Memory Guard
    //==================================================================

    ifa_general_memory_guard #(
        .WIDTH      (WIDTH),
        .ADDR_W     (MEM_ADDR_W),
        .MAX_YARA   (MAX_YARA)
    ) memory_guard (
        .clk                     (clk),
        .rst                     (rst),
        .clear_yara              (clear_yara),

        .active_yara             (active_yara),

        .mem_request             (mem_request_guarded),
        .mem_write               (mem_write),
        .mem_address             (mem_address),
        .mem_write_data          (mem_write_data),

        .mem_read_data           (mem_read_data),
        .mem_allowed             (mem_allowed),
        .mem_denied              (mem_denied),

        .babalawo_mode           (babalawo_mode),

        .grant_read_valid        (mem_grant_read_valid),
        .grant_write_valid       (mem_grant_write_valid),
        .revoke_read_valid       (mem_revoke_read_valid),
        .revoke_write_valid      (mem_revoke_write_valid),

        .admin_address           (mem_admin_address),
        .admin_yara              (mem_admin_yara),

        .address_owned           (address_owned),
        .address_owner           (address_owner),

        .active_read_permission  (
            active_read_permission
        ),

        .active_write_permission (
            active_write_permission
        ),

        .read_count              (memory_read_count),
        .write_count             (memory_write_count),
        .denied_count            (memory_denied_count)
    );


    //==================================================================
    // Shared Physical Stack RAM
    //
    // One physical RAM, logically partitioned by:
    //
    //     physical_address =
    //         (active_yara * STACK_DEPTH) + active_sp
    //
    // Access is allowed only for an active, running YÀRÁ.
    //==================================================================

    ifa_stack_memory_v4 #(
        .WIDTH       (WIDTH),
        .ENTRY_WIDTH (RELATION_STACK_WIDTH),
        .MAX_YARA    (MAX_YARA),
        .STACK_DEPTH (STACK_DEPTH)
    ) stack_memory (
        .clk           (clk),
        .rst           (rst),

        .active_yara   (active_yara),
        .stack_pointer (stack_access_sp[STACK_SP_W-1:0]),

        .write_valid   (stack_write_guarded),
        .read_valid    (stack_read_guarded),
        .write_data    (stack_write_data),

        .read_data     (stack_read_data),
        .write_done    (stack_write_done),
        .read_done     (stack_read_done),

        .stack_allowed (stack_allowed),
        .stack_denied  (stack_denied)
    );

    //==================================================================
    // Native IFÁ operation status export
    //
    // The request is a one-cycle pulse.  The fabric response arrives later,
    // so keep completion visible while the selected YARA remains runnable;
    // do not require execute_valid to stay asserted while waiting.
    //==================================================================

    always_comb begin
        operation_valid = 1'b0;

        exception_valid = 1'b0;
        exception_code  = 4'h0;

        state_valid = 1'b0;
        state_code  = 4'h0;

        eq_flag = 1'b0;
        gt_flag = 1'b0;
        lt_flag = 1'b0;

        if (active_valid && active_running) begin
            operation_valid = fabric_operation_valid;

            exception_valid = fabric_exception_valid;
            exception_code  = fabric_exception_code;

            state_valid = fabric_state_valid;
            state_code  = fabric_state_code;

            eq_flag = fabric_eq_flag;
            gt_flag = fabric_gt_flag;
            lt_flag = fabric_lt_flag;
        end
    end

endmodule
