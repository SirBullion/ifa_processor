//======================================================================
// IFÁ Processor V4
// Shared Physical Stack RAM with Per-YÀRÁ Logical Isolation
//
// Logical addressing:
//
//     physical_address = (yara_id * STACK_DEPTH) + sp
//
// Each YÀRÁ owns an independent stack region inside one shared RAM.
//======================================================================

module ifa_stack_memory_v4 #(
    // Retained for compatibility with the existing byte-stack tests.
    parameter integer WIDTH       = 8,

    // Width of one complete logical stack entry.
    parameter integer ENTRY_WIDTH = WIDTH,

    parameter integer MAX_YARA    = 16,
    parameter integer STACK_DEPTH = 16,

    parameter integer YARA_W =
        (MAX_YARA <= 1) ? 1 : $clog2(MAX_YARA),

    parameter integer SP_W =
        (STACK_DEPTH <= 1) ? 1 : $clog2(STACK_DEPTH),

    parameter integer TOTAL_DEPTH =
        MAX_YARA * STACK_DEPTH,

    parameter integer PHYS_ADDR_W =
        (TOTAL_DEPTH <= 1) ? 1 : $clog2(TOTAL_DEPTH)
)(
    input  logic                  clk,
    input  logic                  rst,

    input  logic [YARA_W-1:0]     active_yara,
    input  logic [SP_W-1:0]       stack_pointer,

    input  logic                  write_valid,
    input  logic                  read_valid,

    input  logic [ENTRY_WIDTH-1:0] write_data,

    output logic [ENTRY_WIDTH-1:0] read_data,
    output logic                  write_done,
    output logic                  read_done,

    output logic                  stack_allowed,
    output logic                  stack_denied
);

    //==================================================================
    // Parameter checks
    //==================================================================

    initial begin
        if (WIDTH < 1) begin
            $error("ifa_stack_memory_v4: WIDTH must be >= 1");
            $finish;
        end

        if (ENTRY_WIDTH < 1) begin
            $error(
                "ifa_stack_memory_v4: ENTRY_WIDTH must be >= 1"
            );
            $finish;
        end

        if (MAX_YARA < 1) begin
            $error("ifa_stack_memory_v4: MAX_YARA must be >= 1");
            $finish;
        end

        if (STACK_DEPTH < 1) begin
            $error("ifa_stack_memory_v4: STACK_DEPTH must be >= 1");
            $finish;
        end
    end

    //==================================================================
    // Shared physical memory
    //==================================================================

    logic [ENTRY_WIDTH-1:0] stack_mem [0:TOTAL_DEPTH-1];

    logic active_yara_valid;
    logic stack_pointer_valid;

    logic [PHYS_ADDR_W-1:0] physical_address;

    integer reset_index;

    //==================================================================
    // Validation and address mapping
    //==================================================================

    always_comb begin
        active_yara_valid =
            (active_yara < MAX_YARA);

        stack_pointer_valid =
            (stack_pointer < STACK_DEPTH);

        physical_address =
            (active_yara * STACK_DEPTH) + stack_pointer;
    end

    //==================================================================
    // Synchronous access
    //==================================================================

    always_ff @(posedge clk) begin
        if (rst) begin
            read_data    <= '0;
            write_done   <= 1'b0;
            read_done    <= 1'b0;
            stack_allowed <= 1'b0;
            stack_denied  <= 1'b0;

            for (
                reset_index = 0;
                reset_index < TOTAL_DEPTH;
                reset_index = reset_index + 1
            ) begin
                stack_mem[reset_index] <= '0;
            end
        end else begin
            write_done    <= 1'b0;
            read_done     <= 1'b0;
            stack_allowed <= 1'b0;
            stack_denied  <= 1'b0;

            if (write_valid || read_valid) begin
                if (
                    !active_yara_valid ||
                    !stack_pointer_valid
                ) begin
                    stack_denied <= 1'b1;
                end else begin
                    stack_allowed <= 1'b1;

                    if (write_valid) begin
                        stack_mem[physical_address] <= write_data;
                        write_done <= 1'b1;
                    end

                    if (read_valid) begin
                        read_data <= stack_mem[physical_address];
                        read_done <= 1'b1;
                    end
                end
            end
        end
    end

endmodule
