//======================================================================
// IFÁ Processor V4
// Generic YÀRÁ Context Bank
//
// Each YÀRÁ owns an independent resumable processor context.
//
// Current context fields:
//
//   PC
//   IR
//   A register
//   B register
//   Address register
//   Execution flags
//
// Locked rules:
//
//   1. Context state is indexed by YÀRÁ ID.
//   2. context_write affects only active_yara.
//   3. clear_yara[i] clears only context[i].
//   4. An invalid active_yara cannot read or write an array.
//   5. A clear operation has priority over a context write.
//======================================================================

module ifa_yara_context_bank #(
    parameter integer WIDTH      = 8,
    parameter integer IR_WIDTH   = 16,

    // Retained temporarily for compatibility.
    parameter integer YARA_COUNT = 2,

    // Official V4 operating-system capacity parameter.
    parameter integer MAX_YARA   = YARA_COUNT,

    parameter integer YARA_W =
        (MAX_YARA <= 1) ? 1 : $clog2(MAX_YARA)
)(
    input  logic                      clk,
    input  logic                      rst,

    // YÀRÁ selected by Onílẹ̀.
    input  logic [YARA_W-1:0]         active_yara,

    // Active-context write interface.
    input  logic                      context_write,

    input  logic [WIDTH-1:0]          write_pc,
    input  logic [IR_WIDTH-1:0]       write_ir,
    input  logic [WIDTH-1:0]          write_a,
    input  logic [WIDTH-1:0]          write_b,
    input  logic [WIDTH-1:0]          write_address,
    input  logic [WIDTH-1:0]          write_flags,
    input  logic [WIDTH-1:0]          write_sp,

    // Independent clear signal for every YÀRÁ.
    input  logic [MAX_YARA-1:0]       clear_yara,

    // Active-context read interface.
    output logic [WIDTH-1:0]          read_pc,
    output logic [IR_WIDTH-1:0]       read_ir,
    output logic [WIDTH-1:0]          read_a,
    output logic [WIDTH-1:0]          read_b,
    output logic [WIDTH-1:0]          read_address,
    output logic [WIDTH-1:0]          read_flags,
    output logic [WIDTH-1:0]          read_sp
);

    //==================================================================
    // Parameter validation
    //==================================================================

    initial begin
        if (MAX_YARA < 1) begin
            $error(
                "ifa_yara_context_bank: MAX_YARA must be at least 1"
            );
            $finish;
        end

        if (WIDTH < 1) begin
            $error(
                "ifa_yara_context_bank: WIDTH must be at least 1"
            );
            $finish;
        end

        if (IR_WIDTH < 1) begin
            $error(
                "ifa_yara_context_bank: IR_WIDTH must be at least 1"
            );
            $finish;
        end
    end

    //==================================================================
    // Indexed context storage
    //==================================================================

    logic [WIDTH-1:0]    pc_mem      [0:MAX_YARA-1];
    logic [IR_WIDTH-1:0] ir_mem      [0:MAX_YARA-1];

    logic [WIDTH-1:0]    a_mem       [0:MAX_YARA-1];
    logic [WIDTH-1:0]    b_mem       [0:MAX_YARA-1];

    logic [WIDTH-1:0]    address_mem [0:MAX_YARA-1];
    logic [WIDTH-1:0]    flags_mem   [0:MAX_YARA-1];
    logic [WIDTH-1:0]    sp_mem      [0:MAX_YARA-1];

    //==================================================================
    // Safe active-ID validation
    //
    // This is important when MAX_YARA is not a power of two.
    //
    // Example:
    //
    //   MAX_YARA = 5
    //   YARA_W    = 3
    //
    // IDs 5, 6 and 7 must never index the arrays.
    //==================================================================

    logic active_yara_valid;

    always_comb begin
        active_yara_valid =
            (active_yara < MAX_YARA);
    end

    //==================================================================
    // Context reset, local clear and active-context write
    //
    // Priority:
    //
    //   global reset
    //       ↓
    //   per-YÀRÁ clear
    //       ↓
    //   active-context write
    //
    // A context being cleared cannot also be written in the same cycle.
    //==================================================================

    integer context_index;

    always_ff @(posedge clk) begin
        if (rst) begin
            for (
                context_index = 0;
                context_index < MAX_YARA;
                context_index = context_index + 1
            ) begin
                pc_mem[context_index]      <= '0;
                ir_mem[context_index]      <= '0;
                a_mem[context_index]       <= '0;
                b_mem[context_index]       <= '0;
                address_mem[context_index] <= '0;
                flags_mem[context_index]   <= '0;
                sp_mem[context_index]      <= '0;
            end
        end else begin

            //----------------------------------------------------------
            // Independent local context clear
            //----------------------------------------------------------

            for (
                context_index = 0;
                context_index < MAX_YARA;
                context_index = context_index + 1
            ) begin
                if (clear_yara[context_index]) begin
                    pc_mem[context_index]      <= '0;
                    ir_mem[context_index]      <= '0;
                    a_mem[context_index]       <= '0;
                    b_mem[context_index]       <= '0;
                    address_mem[context_index] <= '0;
                    flags_mem[context_index]   <= '0;
                    sp_mem[context_index]      <= '0;
                end
            end

            //----------------------------------------------------------
            // Active-context write
            //
            // Only the selected valid YÀRÁ may be modified.
            // A simultaneous clear of that room blocks the write.
            //----------------------------------------------------------

            if (
                context_write &&
                active_yara_valid &&
                !clear_yara[active_yara]
            ) begin
                pc_mem[active_yara]      <= write_pc;
                ir_mem[active_yara]      <= write_ir;
                a_mem[active_yara]       <= write_a;
                b_mem[active_yara]       <= write_b;
                address_mem[active_yara] <= write_address;
                flags_mem[active_yara]   <= write_flags;
                sp_mem[active_yara]      <= write_sp;
            end
        end
    end

    //==================================================================
    // Active-context read
    //
    // Invalid IDs return zero and never index the context arrays.
    //==================================================================

    always_comb begin
        read_pc      = '0;
        read_ir      = '0;
        read_a       = '0;
        read_b       = '0;
        read_address = '0;
        read_flags   = '0;
        read_sp      = '0;

        if (active_yara_valid) begin
            read_pc      = pc_mem[active_yara];
            read_ir      = ir_mem[active_yara];
            read_a       = a_mem[active_yara];
            read_b       = b_mem[active_yara];
            read_address = address_mem[active_yara];
            read_flags   = flags_mem[active_yara];
            read_sp      = sp_mem[active_yara];
        end
    end

endmodule
