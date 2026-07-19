//======================================================================
// IFÁ Processor V4
// Operation-Aware Shared RPC and Local RMU Fabric
//
// One shared RPC.
// One independent local RMU per YÀRÁ.
//
// Universal Relation Frame:
//
//     Ψ = {Y, RA, RD, R0, T}
//
// Operation-aware RMU key:
//
//     K = {OP, RA, RD, T}
//
// YARA_ID is not part of the key.
// Isolation is provided by selecting a separate local RMU.
//======================================================================

module ifa_yara_frame_share_core_v45 #(
    parameter integer WIDTH      = 8,
    parameter integer OP_WIDTH   = 4,
    parameter integer DEPTH      = 16,
    parameter integer YARA_COUNT = 2,
    parameter integer MAX_YARA   = YARA_COUNT,
    parameter integer YARA_W =
        (MAX_YARA <= 1) ? 1 : $clog2(MAX_YARA)
)(
    input  wire                     clk,
    input  wire                     rst,

    // Active execution context.
    input  wire [YARA_W-1:0]        active_yara,

    // Shared RPC request.
    input  wire                     in_valid,
    input  wire [OP_WIDTH-1:0]      execute_op,
    input  wire [WIDTH-1:0]         A,
    input  wire [WIDTH-1:0]         B,

    // Independent local-RMU clear.
    input  wire [MAX_YARA-1:0]      clear_yara,

    // Authorized ONÍLẸ̀ frame delegation.
    input  wire                     share_commit,
    input  wire [YARA_W-1:0]        share_source_yara,
    input  wire [YARA_W-1:0]        share_destination_yara,
    input  wire                     share_authorized,

    // ONÍLẸ̀ relation restoration for RPOP/RET.
    //
    // Restoration targets the active YÀRÁ local RMU and reuses the
    // existing administrative-import mechanism.
    input  wire                     restore_valid,

    input  wire [OP_WIDTH-1:0]      restore_op,

    input  wire [WIDTH-1:0]         restore_y,
    input  wire [WIDTH-1:0]         restore_ra,
    input  wire [WIDTH-1:0]         restore_rd,
    input  wire [WIDTH-1:0]         restore_r0,
    input  wire [WIDTH-1:0]         restore_t,

    output reg                      restore_done,

    output reg                      rmu_hit,
    output reg                      rmu_miss,

    output reg                      share_done,
    output reg                      share_denied,

    output reg  [OP_WIDTH-1:0]      out_op,

    output reg  [WIDTH-1:0]         out_y,
    output reg  [WIDTH-1:0]         out_ra,
    output reg  [WIDTH-1:0]         out_rd,
    output reg  [WIDTH-1:0]         out_r0,
    output reg  [WIDTH-1:0]         out_t,

    // Native IFÁ status remains outside the relation frame and RMU key.
    output reg                      operation_valid,

    output reg                      exception_valid,
    output reg  [3:0]               exception_code,

    output reg                      state_valid,
    output reg  [3:0]               state_code,

    output reg                      eq_flag,
    output reg                      gt_flag,
    output reg                      lt_flag,


    // Temporary MAX_YARA=2 compatibility outputs.
    output reg  [31:0]              yara0_hits,
    output reg  [31:0]              yara0_misses,
    output reg  [31:0]              yara0_imports,

    output reg  [31:0]              yara1_hits,
    output reg  [31:0]              yara1_misses,
    output reg  [31:0]              yara1_imports
);

    //==================================================================
    // Parameter checks
    //==================================================================

    initial begin
        if (WIDTH < 1) begin
            $display(
                "ERROR: ifa_yara_frame_share_core WIDTH must be >= 1"
            );
            $finish;
        end

        if (OP_WIDTH < 1) begin
            $display(
                "ERROR: ifa_yara_frame_share_core OP_WIDTH must be >= 1"
            );
            $finish;
        end

        if (DEPTH < 1) begin
            $display(
                "ERROR: ifa_yara_frame_share_core DEPTH must be >= 1"
            );
            $finish;
        end

        if (MAX_YARA < 1) begin
            $display(
                "ERROR: ifa_yara_frame_share_core MAX_YARA must be >= 1"
            );
            $finish;
        end
    end

    //==================================================================
    // Safe YÀRÁ-ID validation
    //==================================================================

    reg active_yara_valid;
    reg source_yara_valid;
    reg destination_yara_valid;

    always @* begin
        active_yara_valid =
            (active_yara < MAX_YARA);

        source_yara_valid =
            (share_source_yara < MAX_YARA);

        destination_yara_valid =
            (share_destination_yara < MAX_YARA);
    end

    //==================================================================
    // One shared native Relation Arithmetic Unit
    //
    // The native RAU computes the universal relation frame from A/B.
    // execute_op selects the native mathematical function that
    // produces the operation-specific Y and T values.
    //==================================================================

    wire [WIDTH-1:0] rau_y;
    wire [WIDTH-1:0] rau_ra;
    wire [WIDTH-1:0] rau_rd;
    wire [WIDTH-1:0] rau_r0;
    wire [WIDTH-1:0] rau_t;

wire [OP_WIDTH-1:0] rau_op;
wire rau_busy;
wire rau_done;

    wire             rau_valid;

    wire             rau_exception_valid;
    wire [3:0]       rau_exception_code;

    wire             rau_state_valid;
    wire [3:0]       rau_state_code;

    wire             rau_eq_flag;
    wire             rau_gt_flag;
    wire             rau_lt_flag;

    //==================================================================
    // One shared native Relation Arithmetic Unit
    //
    // Universal:
    //
    //     RA = A & B
    //     RD = A ^ B
    //     R0 = ~(A | B)
    //
    // Operation-specific:
    //
    //     Y = Y_op(A,B)
    //     T = T_op(A,B)
    //==================================================================


ifa_yara_pe_bank4 #(
    .WIDTH       (WIDTH),
    .OP_WIDTH    (OP_WIDTH),
    .VALUE_WIDTH (32),
    .MAX_YARA    (MAX_YARA),
    .YARA_W      (YARA_W)
) shared_v45_pe_bank (
    .clk               (clk),
    .rst               (rst),

    .start_i           (in_valid),
    .active_yara_i     (active_yara),

    .operation_i       (execute_op),
    .operand_a_i       (A),
    .operand_b_i       (B),

    .busy_o            (rau_busy),
    .done_o            (rau_done),

    .operation_o       (rau_op),

    .y_o               (rau_y),
    .ra_o              (rau_ra),
    .rd_o              (rau_rd),
    .r0_o              (rau_r0),
    .t_o               (rau_t),

    .operation_valid_o (rau_valid),

    .exception_valid_o (rau_exception_valid),
    .exception_code_o  (rau_exception_code),

    .state_valid_o     (rau_state_valid),
    .state_code_o      (rau_state_code),

    .eq_o              (rau_eq_flag),
    .gt_o              (rau_gt_flag),
    .lt_o              (rau_lt_flag)
);


    //==================================================================
    // Indexed local-RMU signals
    //==================================================================

    reg  [MAX_YARA-1:0] room_req_valid;
    reg  [MAX_YARA-1:0] room_import_valid;

    wire [MAX_YARA-1:0] room_hit;
    wire [MAX_YARA-1:0] room_miss;
    wire [MAX_YARA-1:0] room_import_done;

    wire [OP_WIDTH-1:0] room_op [0:MAX_YARA-1];

    wire [WIDTH-1:0] room_y  [0:MAX_YARA-1];
    wire [WIDTH-1:0] room_ra [0:MAX_YARA-1];
    wire [WIDTH-1:0] room_rd [0:MAX_YARA-1];
    wire [WIDTH-1:0] room_r0 [0:MAX_YARA-1];
    wire [WIDTH-1:0] room_t  [0:MAX_YARA-1];

    wire [31:0] room_hit_count    [0:MAX_YARA-1];
    wire [31:0] room_miss_count   [0:MAX_YARA-1];
    wire [31:0] room_store_count  [0:MAX_YARA-1];
    wire [31:0] room_evict_count  [0:MAX_YARA-1];
    wire [31:0] room_import_count [0:MAX_YARA-1];

    //==================================================================
    // Normal active-YÀRÁ request decoder
    //==================================================================

    integer request_index;

    always @* begin
        room_req_valid = {MAX_YARA{1'b0}};

        if (
            rau_done &&
        active_yara_valid &&
        rau_valid &&
        !rau_exception_valid
        ) begin
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
    // Delegation authorization
    //
    // Delegation requires:
    //
    //     valid source
    //     valid destination
    //     source != destination
    //     ONÍLẸ̀ authorization
    //==================================================================

    reg delegation_allowed;

    always @* begin
        delegation_allowed =
            share_commit &&
            share_authorized &&
            source_yara_valid &&
            destination_yara_valid &&
            (share_source_yara != share_destination_yara);

        share_denied =
            share_commit &&
            !delegation_allowed;
    end

    //==================================================================
    // Select complete source frame, including OP
    //==================================================================

    reg [OP_WIDTH-1:0] share_op;

    reg [WIDTH-1:0] share_y;
    reg [WIDTH-1:0] share_ra;
    reg [WIDTH-1:0] share_rd;
    reg [WIDTH-1:0] share_r0;
    reg [WIDTH-1:0] share_t;

    always @* begin
        share_op = {OP_WIDTH{1'b0}};

        share_y  = {WIDTH{1'b0}};
        share_ra = {WIDTH{1'b0}};
        share_rd = {WIDTH{1'b0}};
        share_r0 = {WIDTH{1'b0}};
        share_t  = {WIDTH{1'b0}};

        if (source_yara_valid) begin
            share_op = room_op[share_source_yara];

            share_y  = room_y[share_source_yara];
            share_ra = room_ra[share_source_yara];
            share_rd = room_rd[share_source_yara];
            share_r0 = room_r0[share_source_yara];
            share_t  = room_t[share_source_yara];
        end
    end

    //==================================================================
    // Administrative-import selection
    //
    // Relation restoration has priority over inter-YÀRÁ delegation.
    // Both operations reuse the same local-RMU import mechanism.
    //==================================================================

    reg [OP_WIDTH-1:0] admin_selected_op;

    reg [WIDTH-1:0] admin_selected_y;
    reg [WIDTH-1:0] admin_selected_ra;
    reg [WIDTH-1:0] admin_selected_rd;
    reg [WIDTH-1:0] admin_selected_r0;
    reg [WIDTH-1:0] admin_selected_t;

    always @* begin
        admin_selected_op = share_op;

        admin_selected_y  = share_y;
        admin_selected_ra = share_ra;
        admin_selected_rd = share_rd;
        admin_selected_r0 = share_r0;
        admin_selected_t  = share_t;

        if (restore_valid && active_yara_valid) begin
            admin_selected_op = restore_op;

            admin_selected_y  = restore_y;
            admin_selected_ra = restore_ra;
            admin_selected_rd = restore_rd;
            admin_selected_r0 = restore_r0;
            admin_selected_t  = restore_t;
        end
    end

    //==================================================================
    // Destination import decoder
    //==================================================================

    integer destination_index;

    always @* begin
        room_import_valid = {MAX_YARA{1'b0}};

        // Restoration has priority and can affect only the active YÀRÁ.
        if (restore_valid && active_yara_valid) begin
            for (
                destination_index = 0;
                destination_index < MAX_YARA;
                destination_index = destination_index + 1
            ) begin
                if (
                    active_yara ==
                    destination_index
                ) begin
                    room_import_valid[destination_index] = 1'b1;
                end
            end
        end
        else if (delegation_allowed) begin
            for (
                destination_index = 0;
                destination_index < MAX_YARA;
                destination_index = destination_index + 1
            ) begin
                if (
                    share_destination_yara ==
                    destination_index
                ) begin
                    room_import_valid[destination_index] = 1'b1;
                end
            end
        end
    end

    //==================================================================
    // Generic local-RMU bank
    //==================================================================

    genvar yara_index;

    generate
        for (
            yara_index = 0;
            yara_index < MAX_YARA;
            yara_index = yara_index + 1
        ) begin : generate_local_rmu

            wire room_reset;

            assign room_reset =
                rst | clear_yara[yara_index];

            ifa_relation_memory_controller_admin #(
                .WIDTH    (WIDTH),
                .OP_WIDTH (OP_WIDTH),
                .DEPTH    (DEPTH)
            ) local_rmu (
                .clk                (clk),
                .rst                (room_reset),

                .req_valid          (
                    room_req_valid[yara_index]
                ),

                .in_op              (execute_op),

                .in_y               (rau_y),
                .in_ra              (rau_ra),
                .in_rd              (rau_rd),
                .in_r0              (rau_r0),
                .in_t               (rau_t),

                .admin_import_valid (
                    room_import_valid[yara_index]
                ),

                .admin_op           (admin_selected_op),

                .admin_y            (admin_selected_y),
                .admin_ra           (admin_selected_ra),
                .admin_rd           (admin_selected_rd),
                .admin_r0           (admin_selected_r0),
                .admin_t            (admin_selected_t),

                .hit                (room_hit[yara_index]),
                .miss               (room_miss[yara_index]),

                .import_done        (
                    room_import_done[yara_index]
                ),

                .out_op             (room_op[yara_index]),

                .out_y              (room_y[yara_index]),
                .out_ra             (room_ra[yara_index]),
                .out_rd             (room_rd[yara_index]),
                .out_r0             (room_r0[yara_index]),
                .out_t              (room_t[yara_index]),

                .hit_count          (
                    room_hit_count[yara_index]
                ),

                .miss_count         (
                    room_miss_count[yara_index]
                ),

                .store_count        (
                    room_store_count[yara_index]
                ),

                .evict_count        (
                    room_evict_count[yara_index]
                ),

                .import_count       (
                    room_import_count[yara_index]
                )
            );
        end
    endgenerate

    //==================================================================
    // Delegation completion
    //==================================================================

    integer done_index;

    always @* begin
        share_done   = 1'b0;
        restore_done = 1'b0;

        for (
            done_index = 0;
            done_index < MAX_YARA;
            done_index = done_index + 1
        ) begin
            if (room_import_done[done_index]) begin
                if (
                    restore_valid &&
                    active_yara_valid &&
                    active_yara == done_index
                ) begin
                    restore_done = 1'b1;
                end
                else begin
                    share_done = 1'b1;
                end
            end
        end
    end

    //==================================================================
    // Native IFÁ operation status export
    //
    // Status is not stored in:
    //
    //     FRAME = {Y, RA, RD, R0, T}
    //     KEY   = {OP, RA, RD, T}
    //==================================================================

    always @* begin
        operation_valid = 1'b0;

        exception_valid = 1'b0;
        exception_code  = 4'h0;

        state_valid = 1'b0;
        state_code  = 4'h0;

        eq_flag = 1'b0;
        gt_flag = 1'b0;
        lt_flag = 1'b0;

        if (rau_done && active_yara_valid) begin
            operation_valid = rau_valid;

            exception_valid = rau_exception_valid;
            exception_code  = rau_exception_code;

            state_valid = rau_state_valid;
            state_code  = rau_state_code;

            eq_flag = rau_eq_flag;
            gt_flag = rau_gt_flag;
            lt_flag = rau_lt_flag;
        end
    end

    //==================================================================
    // Active-YÀRÁ output selection
    //==================================================================

    always @* begin
        rmu_hit  = 1'b0;
        rmu_miss = 1'b0;

        out_op = {OP_WIDTH{1'b0}};

        out_y  = {WIDTH{1'b0}};
        out_ra = {WIDTH{1'b0}};
        out_rd = {WIDTH{1'b0}};
        out_r0 = {WIDTH{1'b0}};
        out_t  = {WIDTH{1'b0}};

        if (active_yara_valid) begin
            rmu_hit  = room_hit[active_yara];
            rmu_miss = room_miss[active_yara];

            out_op = room_op[active_yara];

            out_y  = room_y[active_yara];
            out_ra = room_ra[active_yara];
            out_rd = room_rd[active_yara];
            out_r0 = room_r0[active_yara];
            out_t  = room_t[active_yara];
        end
    end

    //==================================================================
    // Temporary two-YÀRÁ statistics compatibility
    //==================================================================

    generate
        if (MAX_YARA >= 1) begin : generate_yara0_stats
            always @* begin
                yara0_hits =
                    room_hit_count[0];

                yara0_misses =
                    room_miss_count[0];

                yara0_imports =
                    room_import_count[0];
            end
        end else begin : generate_no_yara0_stats
            always @* begin
                yara0_hits    = 32'd0;
                yara0_misses  = 32'd0;
                yara0_imports = 32'd0;
            end
        end
    endgenerate

    generate
        if (MAX_YARA >= 2) begin : generate_yara1_stats
            always @* begin
                yara1_hits =
                    room_hit_count[1];

                yara1_misses =
                    room_miss_count[1];

                yara1_imports =
                    room_import_count[1];
            end
        end else begin : generate_no_yara1_stats
            always @* begin
                yara1_hits    = 32'd0;
                yara1_misses  = 32'd0;
                yara1_imports = 32'd0;
            end
        end
    endgenerate

endmodule
