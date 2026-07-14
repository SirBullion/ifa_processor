//======================================================================
// IFÁ Processor V4
// Operation-aware Local Relation Memory Unit
//
// Stored frame:
//
//     {OP, Y, RA, RD, R0, T}
//
// Lookup key:
//
//     {OP, RA, RD, T}
//
// YARA_ID is not part of the key.
// Each YÀRÁ owns a separate instance of this RMU.
//======================================================================

module ifa_relation_memory_controller_admin #(
    parameter integer WIDTH    = 8,
    parameter integer OP_WIDTH = 4,
    parameter integer DEPTH    = 16,
    parameter integer PTR_W    = (DEPTH <= 1) ? 1 : $clog2(DEPTH)
)(
    input  wire                     clk,
    input  wire                     rst,

    // Normal lookup/store request.
    input  wire                     req_valid,
    input  wire [OP_WIDTH-1:0]      in_op,
    input  wire [WIDTH-1:0]         in_y,
    input  wire [WIDTH-1:0]         in_ra,
    input  wire [WIDTH-1:0]         in_rd,
    input  wire [WIDTH-1:0]         in_r0,
    input  wire [WIDTH-1:0]         in_t,

    // Privileged ONÍLẸ̀ frame import.
    input  wire                     admin_import_valid,
    input  wire [OP_WIDTH-1:0]      admin_op,
    input  wire [WIDTH-1:0]         admin_y,
    input  wire [WIDTH-1:0]         admin_ra,
    input  wire [WIDTH-1:0]         admin_rd,
    input  wire [WIDTH-1:0]         admin_r0,
    input  wire [WIDTH-1:0]         admin_t,

    // Request result.
    output reg                      hit,
    output reg                      miss,
    output reg                      import_done,

    output reg  [OP_WIDTH-1:0]      out_op,
    output reg  [WIDTH-1:0]         out_y,
    output reg  [WIDTH-1:0]         out_ra,
    output reg  [WIDTH-1:0]         out_rd,
    output reg  [WIDTH-1:0]         out_r0,
    output reg  [WIDTH-1:0]         out_t,

    // Statistics.
    output reg  [31:0]              hit_count,
    output reg  [31:0]              miss_count,
    output reg  [31:0]              store_count,
    output reg  [31:0]              evict_count,
    output reg  [31:0]              import_count
);

    //==================================================================
    // Parameter checks
    //==================================================================

    initial begin
        if (WIDTH < 1) begin
            $display(
                "ERROR: ifa_relation_memory_controller_admin WIDTH must be >= 1"
            );
            $finish;
        end

        if (OP_WIDTH < 1) begin
            $display(
                "ERROR: ifa_relation_memory_controller_admin OP_WIDTH must be >= 1"
            );
            $finish;
        end

        if (DEPTH < 1) begin
            $display(
                "ERROR: ifa_relation_memory_controller_admin DEPTH must be >= 1"
            );
            $finish;
        end
    end

    //==================================================================
    // RMU entry arrays
    //==================================================================

    reg                      entry_valid [0:DEPTH-1];

    reg [OP_WIDTH-1:0]       entry_op    [0:DEPTH-1];

    reg [WIDTH-1:0]          entry_y     [0:DEPTH-1];
    reg [WIDTH-1:0]          entry_ra    [0:DEPTH-1];
    reg [WIDTH-1:0]          entry_rd    [0:DEPTH-1];
    reg [WIDTH-1:0]          entry_r0    [0:DEPTH-1];
    reg [WIDTH-1:0]          entry_t     [0:DEPTH-1];

    reg [PTR_W-1:0]          write_ptr;

    //==================================================================
    // Normal lookup
    //==================================================================

    reg                      lookup_found;
    reg [PTR_W-1:0]          lookup_index;

    integer lookup_i;

    always @* begin
        lookup_found = 1'b0;
        lookup_index = {PTR_W{1'b0}};

        for (
            lookup_i = 0;
            lookup_i < DEPTH;
            lookup_i = lookup_i + 1
        ) begin
            if (
                (lookup_found == 1'b0) &&
                (entry_valid[lookup_i] == 1'b1) &&
                (entry_op[lookup_i] == in_op) &&
                (entry_ra[lookup_i] == in_ra) &&
                (entry_rd[lookup_i] == in_rd) &&
                (entry_t[lookup_i] == in_t)
            ) begin
                lookup_found = 1'b1;
                lookup_index = lookup_i;
            end
        end
    end

    //==================================================================
    // Administrative import duplicate lookup
    //==================================================================

    reg                      admin_found;
    reg [PTR_W-1:0]          admin_index;

    integer admin_i;

    always @* begin
        admin_found = 1'b0;
        admin_index = {PTR_W{1'b0}};

        for (
            admin_i = 0;
            admin_i < DEPTH;
            admin_i = admin_i + 1
        ) begin
            if (
                (admin_found == 1'b0) &&
                (entry_valid[admin_i] == 1'b1) &&
                (entry_op[admin_i] == admin_op) &&
                (entry_ra[admin_i] == admin_ra) &&
                (entry_rd[admin_i] == admin_rd) &&
                (entry_t[admin_i] == admin_t)
            ) begin
                admin_found = 1'b1;
                admin_index = admin_i;
            end
        end
    end

    //==================================================================
    // Sequential state
    //==================================================================

    integer reset_i;

    always @(posedge clk) begin
        if (rst) begin
            hit         <= 1'b0;
            miss        <= 1'b0;
            import_done <= 1'b0;

            out_op <= {OP_WIDTH{1'b0}};

            out_y  <= {WIDTH{1'b0}};
            out_ra <= {WIDTH{1'b0}};
            out_rd <= {WIDTH{1'b0}};
            out_r0 <= {WIDTH{1'b0}};
            out_t  <= {WIDTH{1'b0}};

            hit_count    <= 32'd0;
            miss_count   <= 32'd0;
            store_count  <= 32'd0;
            evict_count  <= 32'd0;
            import_count <= 32'd0;

            write_ptr <= {PTR_W{1'b0}};

            for (
                reset_i = 0;
                reset_i < DEPTH;
                reset_i = reset_i + 1
            ) begin
                entry_valid[reset_i] <= 1'b0;

                entry_op[reset_i] <= {OP_WIDTH{1'b0}};

                entry_y[reset_i]  <= {WIDTH{1'b0}};
                entry_ra[reset_i] <= {WIDTH{1'b0}};
                entry_rd[reset_i] <= {WIDTH{1'b0}};
                entry_r0[reset_i] <= {WIDTH{1'b0}};
                entry_t[reset_i]  <= {WIDTH{1'b0}};
            end
        end else begin
            hit         <= 1'b0;
            miss        <= 1'b0;
            import_done <= 1'b0;

            //----------------------------------------------------------
            // ONÍLẸ̀ administrative import has priority.
            //----------------------------------------------------------

            if (admin_import_valid) begin
                import_done  <= 1'b1;
                import_count <= import_count + 32'd1;

                out_op <= admin_op;

                out_y  <= admin_y;
                out_ra <= admin_ra;
                out_rd <= admin_rd;
                out_r0 <= admin_r0;
                out_t  <= admin_t;

                if (admin_found) begin
                    entry_op[admin_index] <= admin_op;

                    entry_y[admin_index]  <= admin_y;
                    entry_ra[admin_index] <= admin_ra;
                    entry_rd[admin_index] <= admin_rd;
                    entry_r0[admin_index] <= admin_r0;
                    entry_t[admin_index]  <= admin_t;
                end else begin
                    if (entry_valid[write_ptr]) begin
                        evict_count <= evict_count + 32'd1;
                    end

                    entry_valid[write_ptr] <= 1'b1;

                    entry_op[write_ptr] <= admin_op;

                    entry_y[write_ptr]  <= admin_y;
                    entry_ra[write_ptr] <= admin_ra;
                    entry_rd[write_ptr] <= admin_rd;
                    entry_r0[write_ptr] <= admin_r0;
                    entry_t[write_ptr]  <= admin_t;

                    store_count <= store_count + 32'd1;

                    if (write_ptr == DEPTH - 1) begin
                        write_ptr <= {PTR_W{1'b0}};
                    end else begin
                        write_ptr <= write_ptr + 1'b1;
                    end
                end
            end

            //----------------------------------------------------------
            // Normal local request.
            //----------------------------------------------------------

            else if (req_valid) begin
                if (lookup_found) begin
                    hit       <= 1'b1;
                    hit_count <= hit_count + 32'd1;

                    out_op <= entry_op[lookup_index];

                    out_y  <= entry_y[lookup_index];
                    out_ra <= entry_ra[lookup_index];
                    out_rd <= entry_rd[lookup_index];
                    out_r0 <= entry_r0[lookup_index];
                    out_t  <= entry_t[lookup_index];
                end else begin
                    miss       <= 1'b1;
                    miss_count <= miss_count + 32'd1;

                    out_op <= in_op;

                    out_y  <= in_y;
                    out_ra <= in_ra;
                    out_rd <= in_rd;
                    out_r0 <= in_r0;
                    out_t  <= in_t;

                    if (entry_valid[write_ptr]) begin
                        evict_count <= evict_count + 32'd1;
                    end

                    entry_valid[write_ptr] <= 1'b1;

                    entry_op[write_ptr] <= in_op;

                    entry_y[write_ptr]  <= in_y;
                    entry_ra[write_ptr] <= in_ra;
                    entry_rd[write_ptr] <= in_rd;
                    entry_r0[write_ptr] <= in_r0;
                    entry_t[write_ptr]  <= in_t;

                    store_count <= store_count + 32'd1;

                    if (write_ptr == DEPTH - 1) begin
                        write_ptr <= {PTR_W{1'b0}};
                    end else begin
                        write_ptr <= write_ptr + 1'b1;
                    end
                end
            end
        end
    end

endmodule
