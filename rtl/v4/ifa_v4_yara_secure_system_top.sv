//======================================================================
// IFÁ Processor V4
// Secure YÀRÁ Operating-System Top
//
// Integrates:
//   - YÀRÁ lifecycle manager
//   - independent YÀRÁ contexts
//   - independent local RMUs
//   - guarded shared General Memory
//
// Frame delegation remains the next integration stage.
//======================================================================

module ifa_v4_yara_secure_system_top #(
    parameter integer WIDTH      = 8,
    parameter integer IR_WIDTH   = 16,
    parameter integer RMU_DEPTH  = 16,
    parameter integer MEM_ADDR_W = 4,
    parameter integer YARA_COUNT = 2,
    parameter integer YARA_W =
        (YARA_COUNT <= 1) ? 1 : $clog2(YARA_COUNT)
)(
    input  logic                      clk,
    input  logic                      rst,

    // ---------------------------------------------------------------
    // Babaláwo / Onílẹ̀ lifecycle management
    // ---------------------------------------------------------------

    input  logic                      babalawo_mode,

    input  logic                      create_valid,
    input  logic                      select_valid,
    input  logic                      pause_valid,
    input  logic                      resume_valid,
    input  logic                      destroy_valid,

    input  logic [YARA_W-1:0]         command_yara,

    // ---------------------------------------------------------------
    // Active context update
    // ---------------------------------------------------------------

    input  logic                      context_write,

    input  logic [WIDTH-1:0]          write_pc,
    input  logic [IR_WIDTH-1:0]       write_ir,
    input  logic [WIDTH-1:0]          write_a,
    input  logic [WIDTH-1:0]          write_b,
    input  logic [WIDTH-1:0]          write_address,
    input  logic [WIDTH-1:0]          write_flags,

    // ---------------------------------------------------------------
    // Active YÀRÁ relation execution
    // ---------------------------------------------------------------

    input  logic                      execute_valid,
    input  logic [WIDTH-1:0]          execute_a,
    input  logic [WIDTH-1:0]          execute_b,

    // ---------------------------------------------------------------
    // Shared General Memory request
    // ---------------------------------------------------------------

    input  logic                      mem_request,
    input  logic                      mem_write,
    input  logic [MEM_ADDR_W-1:0]     mem_address,
    input  logic [WIDTH-1:0]          mem_write_data,

    output logic [WIDTH-1:0]          mem_read_data,
    output logic                      mem_allowed,
    output logic                      mem_denied,

    // ---------------------------------------------------------------
    // Onílẹ̀ General Memory permission administration
    // ---------------------------------------------------------------

    input  logic                      grant_read_valid,
    input  logic                      grant_write_valid,
    input  logic                      revoke_read_valid,
    input  logic                      revoke_write_valid,

    input  logic [MEM_ADDR_W-1:0]     admin_address,
    input  logic [YARA_W-1:0]         admin_yara,

    // ---------------------------------------------------------------
    // System state
    // ---------------------------------------------------------------

    output logic [YARA_W-1:0]         active_yara,
    output logic                      active_valid,
    output logic                      active_running,

    output logic [YARA_COUNT-1:0]     yara_valid,
    output logic [YARA_COUNT-1:0]     yara_running,

    output logic                      command_allowed,
    output logic                      command_denied,

    output logic [31:0]               switch_count,
    output logic [31:0]               manager_denied_count,

    // ---------------------------------------------------------------
    // Active context
    // ---------------------------------------------------------------

    output logic [WIDTH-1:0]          active_pc,
    output logic [IR_WIDTH-1:0]       active_ir,
    output logic [WIDTH-1:0]          active_a,
    output logic [WIDTH-1:0]          active_b,
    output logic [WIDTH-1:0]          active_address,
    output logic [WIDTH-1:0]          active_flags,

    // ---------------------------------------------------------------
    // Active relation result
    // ---------------------------------------------------------------

    output logic                      rmu_hit,
    output logic                      rmu_miss,

    output logic [WIDTH-1:0]          out_y,
    output logic [WIDTH-1:0]          out_ra,
    output logic [WIDTH-1:0]          out_rd,
    output logic [WIDTH-1:0]          out_r0,
    output logic [WIDTH-1:0]          out_t,

    output logic [31:0]               active_hit_count,
    output logic [31:0]               active_miss_count,

    output logic [31:0]               yara0_hit_count,
    output logic [31:0]               yara0_miss_count,
    output logic [31:0]               yara1_hit_count,
    output logic [31:0]               yara1_miss_count,

    // ---------------------------------------------------------------
    // General Memory statistics
    // ---------------------------------------------------------------

    output logic [31:0]               memory_read_count,
    output logic [31:0]               memory_write_count,
    output logic [31:0]               memory_denied_count
);

    logic [31:0] active_store_count;
    logic [31:0] active_evict_count;

    logic address_owned;
    logic [YARA_W-1:0] address_owner;
    logic active_read_permission;
    logic active_write_permission;

    logic guarded_mem_request;

    //------------------------------------------------------------------
    // Existing integrated YÀRÁ execution system
    //------------------------------------------------------------------

    ifa_v4_yara_system_top #(
        .WIDTH(WIDTH),
        .IR_WIDTH(IR_WIDTH),
        .DEPTH(RMU_DEPTH),
        .YARA_COUNT(YARA_COUNT)
    ) yara_system (
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

    //------------------------------------------------------------------
    // Memory access is valid only from a live, running room.
    //------------------------------------------------------------------

    assign guarded_mem_request =
        mem_request &&
        active_valid &&
        active_running;

    //------------------------------------------------------------------
    // Shared General Memory Guard
    //------------------------------------------------------------------

    ifa_general_memory_guard #(
        .WIDTH(WIDTH),
        .ADDR_W(MEM_ADDR_W),
        .YARA_COUNT(YARA_COUNT)
    ) memory_guard (
        .clk(clk),
        .rst(rst),

        .active_yara(active_yara),

        .mem_request(guarded_mem_request),
        .mem_write(mem_write),
        .mem_address(mem_address),
        .mem_write_data(mem_write_data),

        .mem_read_data(mem_read_data),
        .mem_allowed(mem_allowed),
        .mem_denied(mem_denied),

        .babalawo_mode(babalawo_mode),

        .grant_read_valid(grant_read_valid),
        .grant_write_valid(grant_write_valid),
        .revoke_read_valid(revoke_read_valid),
        .revoke_write_valid(revoke_write_valid),

        .admin_address(admin_address),
        .admin_yara(admin_yara),

        .address_owned(address_owned),
        .address_owner(address_owner),
        .active_read_permission(active_read_permission),
        .active_write_permission(active_write_permission),

        .read_count(memory_read_count),
        .write_count(memory_write_count),
        .denied_count(memory_denied_count)
    );

endmodule
