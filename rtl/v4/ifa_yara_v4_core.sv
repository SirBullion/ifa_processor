//======================================================================
// IFÁ Processor V4
// Generic YÀRÁ Isolated Execution Core
//
// Architecture:
//
//                  A, B
//                    │
//                    ▼
//              One Shared RPC
//                    │
//                    ▼
//          Candidate Relation Frame
//                    │
//                    ▼
//       Selected Local RMU[active_yara]
//
// Each YÀRÁ owns an independent local RMU.
//
// Relation key:
//
//      K = {RA, RD, T}
//
// YARA_ID is NOT included in the relation key.
// Isolation is provided by physically separate local RMUs.
//======================================================================

module ifa_yara_v4_core #(
    parameter integer WIDTH      = 8,
    parameter integer DEPTH      = 16,

    // Kept temporarily for compatibility with existing modules.
    parameter integer YARA_COUNT = 2,

    // Official V4 operating-system capacity parameter.
    parameter integer MAX_YARA   = YARA_COUNT,

    parameter integer YARA_W =
        (MAX_YARA <= 1) ? 1 : $clog2(MAX_YARA)
)(
    input  logic                    clk,
    input  logic                    rst,

    // YÀRÁ selected by the Onílẹ̀ kernel.
    input  logic [YARA_W-1:0]       active_yara,

    // Execute a relation operation inside the active YÀRÁ.
    input  logic                    in_valid,
    input  logic [WIDTH-1:0]        A,
    input  logic [WIDTH-1:0]        B,

    // Independent clear signal for every YÀRÁ.
    input  logic [MAX_YARA-1:0]     clear_yara,

    // Result from the active local RMU.
    output logic                    rmu_hit,
    output logic                    rmu_miss,

    output logic [WIDTH-1:0]        out_y,
    output logic [WIDTH-1:0]        out_ra,
    output logic [WIDTH-1:0]        out_rd,
    output logic [WIDTH-1:0]        out_r0,
    output logic [WIDTH-1:0]        out_t,

    // Statistics from the active YÀRÁ.
    output logic [31:0]             hit_count,
    output logic [31:0]             miss_count,
    output logic [31:0]             store_count,
    output logic [31:0]             evict_count,

    // Temporary compatibility outputs for current two-YÀRÁ tests.
    output logic [31:0]             yara0_hit_count,
    output logic [31:0]             yara0_miss_count,
    output logic [31:0]             yara1_hit_count,
    output logic [31:0]             yara1_miss_count
);

    //==================================================================
    // Active-YÀRÁ validity
    //==================================================================

    logic active_yara_valid;

    always_comb begin
        active_yara_valid = (active_yara < MAX_YARA);
    end

    //==================================================================
    // Shared Relation Processor Core
    //
    // The RPC computes one candidate relation frame.
    // The selected local RMU decides whether that frame is reused
    // or stored.
    //==================================================================

    logic [WIDTH-1:0] candidate_y;
    logic [WIDTH-1:0] candidate_ra;
    logic [WIDTH-1:0] candidate_rd;
    logic [WIDTH-1:0] candidate_r0;
    logic [WIDTH-1:0] candidate_t;

    ifa_rpc_stub #(
        .WIDTH(WIDTH)
    ) shared_rpc (
        .A  (A),
        .B  (B),

        .Y  (candidate_y),
        .RA (candidate_ra),
        .RD (candidate_rd),
        .R0 (candidate_r0),
        .T  (candidate_t)
    );

    //==================================================================
    // Indexed local-RMU signals
    //==================================================================

    logic [MAX_YARA-1:0] room_req_valid;
    logic [MAX_YARA-1:0] room_reset;

    logic [MAX_YARA-1:0] room_hit;
    logic [MAX_YARA-1:0] room_miss;

    logic [WIDTH-1:0] room_y  [0:MAX_YARA-1];
    logic [WIDTH-1:0] room_ra [0:MAX_YARA-1];
    logic [WIDTH-1:0] room_rd [0:MAX_YARA-1];
    logic [WIDTH-1:0] room_r0 [0:MAX_YARA-1];
    logic [WIDTH-1:0] room_t  [0:MAX_YARA-1];

    logic [31:0] room_hit_count   [0:MAX_YARA-1];
    logic [31:0] room_miss_count  [0:MAX_YARA-1];
    logic [31:0] room_store_count [0:MAX_YARA-1];
    logic [31:0] room_evict_count [0:MAX_YARA-1];

    //==================================================================
    // Active-RMU request decoder
    //
    // Exactly one RMU may receive req_valid.
    // Inactive RMUs receive req_valid = 0 and cannot update.
    //==================================================================

    integer request_index;

    always_comb begin
        room_req_valid = '0;

        if (in_valid && active_yara_valid) begin
            for (
                request_index = 0;
                request_index < MAX_YARA;
                request_index = request_index + 1
            ) begin
                if (active_yara == request_index) begin
                    room_req_valid[request_index] = 1'b1;
                end
            end
        end
    end

    //==================================================================
    // Local RMU bank
    //
    // Every YÀRÁ owns a physically separate RMU.
    // All RMUs see the shared candidate frame.
    // Only the selected RMU receives req_valid.
    //==================================================================

    generate
        for (
            genvar yara_index = 0;
            yara_index < MAX_YARA;
            yara_index = yara_index + 1
        ) begin : generate_local_rmu

            assign room_reset[yara_index] =
                rst | clear_yara[yara_index];

            ifa_relation_memory_controller #(
                .WIDTH(WIDTH),
                .DEPTH(DEPTH)
            ) local_rmu (
                .clk         (clk),
                .rst         (room_reset[yara_index]),

                .req_valid   (room_req_valid[yara_index]),

                .in_y        (candidate_y),
                .in_ra       (candidate_ra),
                .in_rd       (candidate_rd),
                .in_r0       (candidate_r0),
                .in_t        (candidate_t),

                .hit         (room_hit[yara_index]),
                .miss        (room_miss[yara_index]),

                .out_y       (room_y[yara_index]),
                .out_ra      (room_ra[yara_index]),
                .out_rd      (room_rd[yara_index]),
                .out_r0      (room_r0[yara_index]),
                .out_t       (room_t[yara_index]),

                .hit_count   (room_hit_count[yara_index]),
                .miss_count  (room_miss_count[yara_index]),
                .store_count (room_store_count[yara_index]),
                .evict_count (room_evict_count[yara_index])
            );

        end
    endgenerate

    //==================================================================
    // Active-YÀRÁ result selection
    //==================================================================

    always_comb begin
        rmu_hit  = 1'b0;
        rmu_miss = 1'b0;

        out_y  = '0;
        out_ra = '0;
        out_rd = '0;
        out_r0 = '0;
        out_t  = '0;

        hit_count   = 32'd0;
        miss_count  = 32'd0;
        store_count = 32'd0;
        evict_count = 32'd0;

        if (active_yara_valid) begin
            rmu_hit  = room_hit[active_yara];
            rmu_miss = room_miss[active_yara];

            out_y  = room_y[active_yara];
            out_ra = room_ra[active_yara];
            out_rd = room_rd[active_yara];
            out_r0 = room_r0[active_yara];
            out_t  = room_t[active_yara];

            hit_count   = room_hit_count[active_yara];
            miss_count  = room_miss_count[active_yara];
            store_count = room_store_count[active_yara];
            evict_count = room_evict_count[active_yara];
        end
    end

    //==================================================================
    // Temporary compatibility outputs
    //
    // These preserve the current two-YÀRÁ testbench interface while
    // the internal implementation becomes fully generic.
    //==================================================================

    generate
        if (MAX_YARA >= 1) begin : generate_yara0_debug
            always_comb begin
                yara0_hit_count  = room_hit_count[0];
                yara0_miss_count = room_miss_count[0];
            end
        end
        else begin : generate_no_yara0_debug
            always_comb begin
                yara0_hit_count  = 32'd0;
                yara0_miss_count = 32'd0;
            end
        end
    endgenerate

    generate
        if (MAX_YARA >= 2) begin : generate_yara1_debug
            always_comb begin
                yara1_hit_count  = room_hit_count[1];
                yara1_miss_count = room_miss_count[1];
            end
        end
        else begin : generate_no_yara1_debug
            always_comb begin
                yara1_hit_count  = 32'd0;
                yara1_miss_count = 32'd0;
            end
        end
    endgenerate

endmodule
