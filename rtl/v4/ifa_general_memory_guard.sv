//======================================================================
// IFÁ Processor V4
// Generic Shared General Memory Guard
//
// General memory is physically shared, but every address maintains:
//
//   - ownership state
//   - owner YÀRÁ ID
//   - per-YÀRÁ read permission
//   - per-YÀRÁ write permission
//
// Locked rules:
//
//   1. The first successful write to an unowned address claims it.
//   2. The owner may always read and write its address.
//   3. Another YÀRÁ requires explicit permission.
//   4. Read and write permissions are independent.
//   5. Babaláwo privilege is required to grant or revoke permissions.
//   6. Once granted, Onílẹ̀ enforces permissions during normal use.
//   7. Invalid YÀRÁ IDs cannot access or administer memory.
//======================================================================

module ifa_general_memory_guard #(
    parameter integer WIDTH      = 8,
    parameter integer ADDR_W     = 4,

    // Retained temporarily for compatibility.
    parameter integer YARA_COUNT = 2,

    // Official V4 operating-system capacity parameter.
    parameter integer MAX_YARA   = YARA_COUNT,

    parameter integer YARA_W =
        (MAX_YARA <= 1) ? 1 : $clog2(MAX_YARA),

    parameter integer DEPTH =
        (1 << ADDR_W)
)(
    input  logic                     clk,
    input  logic                     rst,

    // Destroy/reset cleanup for each YÀRÁ.
    input  logic [MAX_YARA-1:0]      clear_yara,

    // Active YÀRÁ requesting normal memory access.
    input  logic [YARA_W-1:0]        active_yara,

    input  logic                     mem_request,
    input  logic                     mem_write,
    input  logic [ADDR_W-1:0]        mem_address,
    input  logic [WIDTH-1:0]         mem_write_data,

    output logic [WIDTH-1:0]         mem_read_data,
    output logic                     mem_allowed,
    output logic                     mem_denied,

    // Privileged Onílẹ̀ permission administration.
    input  logic                     babalawo_mode,

    input  logic                     grant_read_valid,
    input  logic                     grant_write_valid,
    input  logic                     revoke_read_valid,
    input  logic                     revoke_write_valid,

    input  logic [ADDR_W-1:0]        admin_address,
    input  logic [YARA_W-1:0]        admin_yara,

    // Debug visibility for the currently requested address.
    output logic                     address_owned,
    output logic [YARA_W-1:0]        address_owner,
    output logic                     active_read_permission,
    output logic                     active_write_permission,

    // Statistics.
    output logic [31:0]              read_count,
    output logic [31:0]              write_count,
    output logic [31:0]              denied_count
);

    //==================================================================
    // Parameter validation
    //==================================================================

    initial begin
        if (WIDTH < 1) begin
            $error(
                "ifa_general_memory_guard: WIDTH must be at least 1"
            );
            $finish;
        end

        if (ADDR_W < 1) begin
            $error(
                "ifa_general_memory_guard: ADDR_W must be at least 1"
            );
            $finish;
        end

        if (MAX_YARA < 1) begin
            $error(
                "ifa_general_memory_guard: MAX_YARA must be at least 1"
            );
            $finish;
        end

        if (DEPTH < 1) begin
            $error(
                "ifa_general_memory_guard: DEPTH must be at least 1"
            );
            $finish;
        end
    end

    //==================================================================
    // General memory storage
    //==================================================================

    logic [WIDTH-1:0] memory [0:DEPTH-1];

    //==================================================================
    // Address ownership
    //==================================================================

    logic owner_valid [0:DEPTH-1];

    logic [YARA_W-1:0] owner [0:DEPTH-1];

    //==================================================================
    // Permission tables
    //
    // read_permission[address][yara]
    // write_permission[address][yara]
    //==================================================================

    logic read_permission
        [0:DEPTH-1]
        [0:MAX_YARA-1];

    logic write_permission
        [0:DEPTH-1]
        [0:MAX_YARA-1];

    //==================================================================
    // Safe YÀRÁ identifier validation
    //
    // Required when MAX_YARA is not a power of two.
    //
    // Example:
    //
    //   MAX_YARA = 5
    //   YARA_W    = 3
    //
    // IDs 5, 6 and 7 must never index the permission arrays.
    //==================================================================

    logic active_yara_valid;
    logic admin_yara_valid;

    always_comb begin
        active_yara_valid =
            (active_yara < MAX_YARA);

        admin_yara_valid =
            (admin_yara < MAX_YARA);
    end

    //==================================================================
    // Current-address policy
    //==================================================================

    logic request_is_owner;
    logic request_can_read;
    logic request_can_write;

    always_comb begin
        address_owned = owner_valid[mem_address];
        address_owner = owner[mem_address];

        active_read_permission  = 1'b0;
        active_write_permission = 1'b0;

        request_is_owner = 1'b0;
        request_can_read = 1'b0;
        request_can_write = 1'b0;

        if (active_yara_valid) begin
            active_read_permission =
                read_permission[mem_address][active_yara];

            active_write_permission =
                write_permission[mem_address][active_yara];

            request_is_owner =
                owner_valid[mem_address] &&
                (owner[mem_address] == active_yara);

            //----------------------------------------------------------
            // Reading an unowned address is allowed.
            //
            // Because reset initializes memory to zero, an unowned
            // address returns zero until first written.
            //----------------------------------------------------------

            request_can_read =
                !owner_valid[mem_address] ||
                request_is_owner ||
                read_permission[mem_address][active_yara];

            //----------------------------------------------------------
            // First successful writer claims an unowned address.
            //----------------------------------------------------------

            request_can_write =
                !owner_valid[mem_address] ||
                request_is_owner ||
                write_permission[mem_address][active_yara];
        end
    end

    //==================================================================
    // Privileged administration acceptance
    //==================================================================

    logic grant_read_accepted;
    logic grant_write_accepted;
    logic revoke_read_accepted;
    logic revoke_write_accepted;

    always_comb begin
        grant_read_accepted =
            babalawo_mode &&
            grant_read_valid &&
            admin_yara_valid;

        grant_write_accepted =
            babalawo_mode &&
            grant_write_valid &&
            admin_yara_valid;

        revoke_read_accepted =
            babalawo_mode &&
            revoke_read_valid &&
            admin_yara_valid;

        revoke_write_accepted =
            babalawo_mode &&
            revoke_write_valid &&
            admin_yara_valid;
    end

    //==================================================================
    // Memory, ownership, permission and statistics state
    //==================================================================

    integer address_index;
    integer yara_index;

    always_ff @(posedge clk) begin
        if (rst) begin
            mem_read_data <= '0;

            mem_allowed <= 1'b0;
            mem_denied  <= 1'b0;

            read_count   <= 32'd0;
            write_count  <= 32'd0;
            denied_count <= 32'd0;

            for (
                address_index = 0;
                address_index < DEPTH;
                address_index = address_index + 1
            ) begin
                memory[address_index]      <= '0;
                owner_valid[address_index] <= 1'b0;
                owner[address_index]       <= '0;

                for (
                    yara_index = 0;
                    yara_index < MAX_YARA;
                    yara_index = yara_index + 1
                ) begin
                    read_permission
                        [address_index]
                        [yara_index] <= 1'b0;

                    write_permission
                        [address_index]
                        [yara_index] <= 1'b0;
                end
            end
        end else begin

            //----------------------------------------------------------
            // One-cycle request result defaults
            //----------------------------------------------------------

            mem_allowed <= 1'b0;
            mem_denied  <= 1'b0;

            //----------------------------------------------------------
            // Destroyed YÀRÁ cleanup
            //
            // A destroyed context must not retain delegated memory
            // permissions or ownership when the same ID is recreated.
            //----------------------------------------------------------

            for (
                address_index = 0;
                address_index < DEPTH;
                address_index = address_index + 1
            ) begin
                for (
                    yara_index = 0;
                    yara_index < MAX_YARA;
                    yara_index = yara_index + 1
                ) begin
                    if (clear_yara[yara_index]) begin
                        read_permission
                            [address_index]
                            [yara_index] <= 1'b0;

                        write_permission
                            [address_index]
                            [yara_index] <= 1'b0;
                    end
                end

                if (
                    owner_valid[address_index]
                    && clear_yara[owner[address_index]]
                ) begin
                    owner_valid[address_index] <= 1'b0;
                    owner[address_index]       <= '0;
                end
            end

            //----------------------------------------------------------
            // Onílẹ̀ permission administration
            //
            // Babaláwo privilege is required only when modifying the
            // permission tables.
            //----------------------------------------------------------

            if (grant_read_accepted) begin
                read_permission
                    [admin_address]
                    [admin_yara] <= 1'b1;
            end

            if (grant_write_accepted) begin
                write_permission
                    [admin_address]
                    [admin_yara] <= 1'b1;
            end

            if (revoke_read_accepted) begin
                read_permission
                    [admin_address]
                    [admin_yara] <= 1'b0;
            end

            if (revoke_write_accepted) begin
                write_permission
                    [admin_address]
                    [admin_yara] <= 1'b0;
            end

            //----------------------------------------------------------
            // Normal General Memory request
            //----------------------------------------------------------

            if (mem_request) begin

                //------------------------------------------------------
                // Invalid YÀRÁ IDs are always denied.
                //------------------------------------------------------

                if (!active_yara_valid) begin
                    mem_read_data <= '0;
                    mem_denied    <= 1'b1;
                    denied_count  <= denied_count + 32'd1;
                end

                //------------------------------------------------------
                // Write request
                //------------------------------------------------------

                else if (mem_write) begin
                    if (request_can_write) begin

                        //------------------------------------------------
                        // The first writer becomes owner.
                        //------------------------------------------------

                        if (!owner_valid[mem_address]) begin
                            owner_valid[mem_address] <= 1'b1;
                            owner[mem_address]       <= active_yara;
                        end

                        memory[mem_address] <= mem_write_data;

                        mem_allowed <= 1'b1;
                        write_count <= write_count + 32'd1;
                    end else begin
                        mem_denied   <= 1'b1;
                        denied_count <= denied_count + 32'd1;
                    end
                end

                //------------------------------------------------------
                // Read request
                //------------------------------------------------------

                else begin
                    if (request_can_read) begin
                        mem_read_data <= memory[mem_address];

                        mem_allowed <= 1'b1;
                        read_count  <= read_count + 32'd1;
                    end else begin
                        mem_read_data <= '0;
                        mem_denied    <= 1'b1;
                        denied_count  <= denied_count + 32'd1;
                    end
                end
            end
        end
    end

endmodule
