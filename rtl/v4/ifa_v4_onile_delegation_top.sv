//======================================================================
// IFÁ Processor V4
// Onílẹ̀-Authorized Cross-YÀRÁ Relation Frame Delegation
//
// Integrates:
//   - Onílẹ̀ permission supervisor
//   - Two isolated YÀRÁ RMUs
//   - Real Relation Frame import/delegation
//
// Cross-YÀRÁ sharing requires:
//   BABALÁWO mode
//   AND explicit directional permission.
//======================================================================

module ifa_v4_onile_delegation_top #(
    parameter integer WIDTH = 8,
    parameter integer DEPTH = 16
)(
    input  logic                     clk,
    input  logic                     rst,

    // Active execution room
    input  logic                     active_yara,
    input  logic                     in_valid,
    input  logic [WIDTH-1:0]         A,
    input  logic [WIDTH-1:0]         B,

    // Privilege
    input  logic                     babalawo_mode,

    // Onílẹ̀ permission administration
    input  logic                     grant_valid,
    input  logic                     revoke_valid,
    input  logic                     admin_source_yara,
    input  logic                     admin_destination_yara,

    // Frame delegation request
    input  logic                     share_commit,
    input  logic                     share_source_yara,
    input  logic                     share_destination_yara,

    // Relation execution output
    output logic                     rmu_hit,
    output logic                     rmu_miss,

    output logic [WIDTH-1:0]         out_y,
    output logic [WIDTH-1:0]         out_ra,
    output logic [WIDTH-1:0]         out_rd,
    output logic [WIDTH-1:0]         out_r0,
    output logic [WIDTH-1:0]         out_t,

    // Delegation result
    output logic                     share_allowed,
    output logic                     share_denied,
    output logic                     share_done,
    output logic                     explicit_permission,

    // Statistics
    output logic [31:0]              allowed_share_count,
    output logic [31:0]              denied_share_count,

    output logic [31:0]              yara0_hits,
    output logic [31:0]              yara0_misses,
    output logic [31:0]              yara0_imports,

    output logic [31:0]              yara1_hits,
    output logic [31:0]              yara1_misses,
    output logic [31:0]              yara1_imports
);

    logic authorized_share_commit;
    logic internal_share_denied;

    //------------------------------------------------------------------
    // Onílẹ̀ permission decision
    //------------------------------------------------------------------

    ifa_onile_supervisor #(
        .YARA_COUNT(2)
    ) onile (
        .clk(clk),
        .rst(rst),

        .babalawo_mode(babalawo_mode),

        .grant_valid(grant_valid),
        .revoke_valid(revoke_valid),

        .admin_source_yara(admin_source_yara),
        .admin_destination_yara(admin_destination_yara),

        .share_request(share_commit),
        .request_source_yara(share_source_yara),
        .request_destination_yara(share_destination_yara),

        .share_allowed(share_allowed),
        .share_denied(share_denied),

        .explicit_permission(explicit_permission),

        .allowed_count(allowed_share_count),
        .denied_count(denied_share_count)
    );

    assign authorized_share_commit =
        share_commit && share_allowed;

    //------------------------------------------------------------------
    // Actual frame copy between isolated local RMUs
    //------------------------------------------------------------------

    ifa_yara_frame_share_core #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH)
    ) rooms (
        .clk(clk),
        .rst(rst),

        .active_yara(active_yara),
        .in_valid(in_valid),

        .A(A),
        .B(B),

        .share_commit(authorized_share_commit),
        .share_source_yara(share_source_yara),
        .share_destination_yara(share_destination_yara),
        .share_authorized(share_allowed),

        .rmu_hit(rmu_hit),
        .rmu_miss(rmu_miss),

        .share_done(share_done),
        .share_denied(internal_share_denied),

        .out_y(out_y),
        .out_ra(out_ra),
        .out_rd(out_rd),
        .out_r0(out_r0),
        .out_t(out_t),

        .yara0_hits(yara0_hits),
        .yara0_misses(yara0_misses),
        .yara0_imports(yara0_imports),

        .yara1_hits(yara1_hits),
        .yara1_misses(yara1_misses),
        .yara1_imports(yara1_imports)
    );

endmodule
