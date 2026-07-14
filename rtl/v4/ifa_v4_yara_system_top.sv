//======================================================================
// IFÁ Processor V4
// Integrated YÀRÁ Operating-System Hardware Top
//
// Integrates:
//   - YÀRÁ lifecycle manager
//   - YÀRÁ context bank
//   - Active-room selector
//   - Independent local RPC + RMU for every YÀRÁ
//
// This stage does not yet integrate:
//   - General Memory Guard
//   - Cross-YÀRÁ frame delegation
//
// Those remain verified standalone blocks and will be connected next.
//======================================================================

module ifa_v4_yara_system_top #(
    parameter integer WIDTH      = 8,
    parameter integer IR_WIDTH   = 16,
    parameter integer DEPTH      = 16,
    parameter integer YARA_COUNT = 2,
    parameter integer YARA_W =
        (YARA_COUNT <= 1) ? 1 : $clog2(YARA_COUNT)
)(
    input  logic                      clk,
    input  logic                      rst,

    // ---------------------------------------------------------------
    // Onílẹ̀ / Babaláwo management interface
    // ---------------------------------------------------------------

    input  logic                      babalawo_mode,

    input  logic                      create_valid,
    input  logic                      select_valid,
    input  logic                      pause_valid,
    input  logic                      resume_valid,
    input  logic                      destroy_valid,

    input  logic [YARA_W-1:0]         command_yara,

    // ---------------------------------------------------------------
    // Context update interface
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
    // Manager state
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
    // Active YÀRÁ context
    // ---------------------------------------------------------------

    output logic [WIDTH-1:0]          active_pc,
    output logic [IR_WIDTH-1:0]       active_ir,
    output logic [WIDTH-1:0]          active_a,
    output logic [WIDTH-1:0]          active_b,
    output logic [WIDTH-1:0]          active_address,
    output logic [WIDTH-1:0]          active_flags,

    // ---------------------------------------------------------------
    // Active YÀRÁ relation result
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
    output logic [31:0]               active_store_count,
    output logic [31:0]               active_evict_count,

    // Two-room debug visibility
    output logic [31:0]               yara0_hit_count,
    output logic [31:0]               yara0_miss_count,
    output logic [31:0]               yara1_hit_count,
    output logic [31:0]               yara1_miss_count
);

    logic [YARA_COUNT-1:0] clear_yara;

    logic execute_allowed;

    //------------------------------------------------------------------
    // Onílẹ̀ YÀRÁ lifecycle manager
    //------------------------------------------------------------------

    ifa_yara_manager #(
        .YARA_COUNT(YARA_COUNT)
    ) manager (
        .clk(clk),
        .rst(rst),

        .babalawo_mode(babalawo_mode),

        .create_valid(create_valid),
        .select_valid(select_valid),
        .pause_valid(pause_valid),
        .resume_valid(resume_valid),
        .destroy_valid(destroy_valid),

        .command_yara(command_yara),

        .active_yara(active_yara),
        .active_valid(active_valid),
        .active_running(active_running),

        .yara_valid(yara_valid),
        .yara_running(yara_running),

        .clear_yara(clear_yara),

        .command_allowed(command_allowed),
        .command_denied(command_denied),

        .switch_count(switch_count),
        .denied_count(manager_denied_count)
    );

    //------------------------------------------------------------------
    // Independent resumable processor contexts
    //------------------------------------------------------------------

    ifa_yara_context_bank #(
        .WIDTH(WIDTH),
        .IR_WIDTH(IR_WIDTH),
        .YARA_COUNT(YARA_COUNT)
    ) context_bank (
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

        .read_pc(active_pc),
        .read_ir(active_ir),
        .read_a(active_a),
        .read_b(active_b),
        .read_address(active_address),
        .read_flags(active_flags)
    );

    //------------------------------------------------------------------
    // Execution is legal only inside a valid, running YÀRÁ.
    //------------------------------------------------------------------

    assign execute_allowed =
        execute_valid &&
        active_valid &&
        active_running;

    //------------------------------------------------------------------
    // Independent local RPC + RMU namespaces
    //------------------------------------------------------------------

    ifa_yara_v4_core #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH),
        .YARA_COUNT(YARA_COUNT)
    ) execution_rooms (
        .clk(clk),
        .rst(rst),

        .active_yara(active_yara),

        .in_valid(execute_allowed),
        .A(execute_a),
        .B(execute_b),

        .clear_yara(clear_yara),

        .rmu_hit(rmu_hit),
        .rmu_miss(rmu_miss),

        .out_y(out_y),
        .out_ra(out_ra),
        .out_rd(out_rd),
        .out_r0(out_r0),
        .out_t(out_t),

        .hit_count(active_hit_count),
        .miss_count(active_miss_count),
        .store_count(active_store_count),
        .evict_count(active_evict_count),

        .yara0_hit_count(yara0_hit_count),
        .yara0_miss_count(yara0_miss_count),
        .yara1_hit_count(yara1_hit_count),
        .yara1_miss_count(yara1_miss_count)
    );

endmodule
