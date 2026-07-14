//======================================================================
// IFÁ Processor V4
// ONÍLẸ̀ Supervisor
// Generic Cross-YÀRÁ Permission Controller
//
// Rules:
//
//   1. Local access is always allowed:
//
//          source_yara == destination_yara
//
//   2. Cross-YÀRÁ access requires explicit permission:
//
//          source_yara != destination_yara
//
//   3. Babaláwo mode is required only to grant or revoke permission.
//
//   4. Once granted, permission remains active until revoked.
//
//   5. Invalid source or destination IDs are denied.
//
// Permission matrix:
//
//      share_permission[source][destination]
//
// YÀRÁ identity is not added to the relation key.
//======================================================================

module ifa_onile_supervisor #(
    // Temporary compatibility parameter.
    parameter integer YARA_COUNT = 2,

    // Official V4 operating-system capacity parameter.
    parameter integer MAX_YARA = YARA_COUNT,

    parameter integer YARA_W =
        (MAX_YARA <= 1) ? 1 : $clog2(MAX_YARA)
)(
    input  logic                    clk,
    input  logic                    rst,

    // Administrative privilege level.
    input  logic                    babalawo_mode,

    // Permission administration.
    input  logic                    grant_valid,
    input  logic                    revoke_valid,

    input  logic [YARA_W-1:0]       admin_source_yara,
    input  logic [YARA_W-1:0]       admin_destination_yara,

    // Runtime access/delegation request.
    input  logic                    share_request,
    input  logic [YARA_W-1:0]       request_source_yara,
    input  logic [YARA_W-1:0]       request_destination_yara,

    output logic                    share_allowed,
    output logic                    share_denied,

    // Verification and statistics.
    output logic                    explicit_permission,
    output logic [31:0]             allowed_count,
    output logic [31:0]             denied_count
);

    //==================================================================
    // Parameter validation
    //==================================================================

    initial begin
        if (MAX_YARA < 1) begin
            $error(
                "ifa_onile_supervisor: MAX_YARA must be at least 1"
            );
            $finish;
        end
    end

    //==================================================================
    // Permission matrix
    //
    // permission[src][dst] authorizes cross-YÀRÁ transfer.
    // Self-access does not require an entry.
    //==================================================================

    logic share_permission
        [0:MAX_YARA-1]
        [0:MAX_YARA-1];

    integer source_index;
    integer destination_index;

    //==================================================================
    // ID validation
    //==================================================================

    logic admin_source_valid;
    logic admin_destination_valid;

    logic request_source_valid;
    logic request_destination_valid;

    always_comb begin
        admin_source_valid =
            (admin_source_yara < MAX_YARA);

        admin_destination_valid =
            (admin_destination_yara < MAX_YARA);

        request_source_valid =
            (request_source_yara < MAX_YARA);

        request_destination_valid =
            (request_destination_yara < MAX_YARA);
    end

    //==================================================================
    // Local-access detection
    //==================================================================

    logic local_access;

    always_comb begin
        local_access =
            request_source_valid &&
            request_destination_valid &&
            (request_source_yara == request_destination_yara);
    end

    //==================================================================
    // Administrative permission operations
    //
    // Permission entries are only needed between different YÀRÁ.
    //==================================================================

    logic grant_accepted;
    logic revoke_accepted;

    always_comb begin
        grant_accepted =
            babalawo_mode &&
            grant_valid &&
            admin_source_valid &&
            admin_destination_valid &&
            (admin_source_yara != admin_destination_yara);

        revoke_accepted =
            babalawo_mode &&
            revoke_valid &&
            admin_source_valid &&
            admin_destination_valid &&
            (admin_source_yara != admin_destination_yara);
    end

    //==================================================================
    // Explicit cross-YÀRÁ permission lookup
    //==================================================================

    always_comb begin
        explicit_permission = 1'b0;

        if (
            request_source_valid &&
            request_destination_valid &&
            (request_source_yara != request_destination_yara)
        ) begin
            explicit_permission =
                share_permission
                    [request_source_yara]
                    [request_destination_yara];
        end
    end

    //==================================================================
    // Runtime authorization
    //
    // Local request:
    //
    //      source == destination
    //
    // is always allowed.
    //
    // Cross-YÀRÁ request:
    //
    //      source != destination
    //
    // requires an explicit permission entry.
    //==================================================================

    always_comb begin
        share_allowed = 1'b0;
        share_denied  = 1'b0;

        if (share_request) begin
            if (
                !request_source_valid ||
                !request_destination_valid
            ) begin
                share_denied = 1'b1;
            end
            else if (local_access) begin
                // SHARE is reserved for cross-YÀRÁ delegation.
                // A room never delegates a frame to itself.
                share_denied = 1'b1;
            end
            else if (explicit_permission) begin
                share_allowed = 1'b1;
            end
            else begin
                share_denied = 1'b1;
            end
        end
    end

    //==================================================================
    // Permission matrix and statistics
    //==================================================================

    always_ff @(posedge clk) begin
        if (rst) begin
            allowed_count <= 32'd0;
            denied_count  <= 32'd0;

            for (
                source_index = 0;
                source_index < MAX_YARA;
                source_index = source_index + 1
            ) begin
                for (
                    destination_index = 0;
                    destination_index < MAX_YARA;
                    destination_index = destination_index + 1
                ) begin
                    share_permission
                        [source_index]
                        [destination_index] <= 1'b0;
                end
            end
        end
        else begin

            //----------------------------------------------------------
            // Grant permission
            //----------------------------------------------------------

            if (grant_accepted) begin
                share_permission
                    [admin_source_yara]
                    [admin_destination_yara] <= 1'b1;
            end

            //----------------------------------------------------------
            // Revoke permission
            //
            // Revoke wins if grant and revoke target the same entry
            // during the same clock cycle.
            //----------------------------------------------------------

            if (revoke_accepted) begin
                share_permission
                    [admin_source_yara]
                    [admin_destination_yara] <= 1'b0;
            end

            //----------------------------------------------------------
            // Runtime authorization counters
            //----------------------------------------------------------

            if (share_request) begin
                if (share_allowed) begin
                    allowed_count <= allowed_count + 32'd1;
                end
                else begin
                    denied_count <= denied_count + 32'd1;
                end
            end
        end
    end

endmodule
