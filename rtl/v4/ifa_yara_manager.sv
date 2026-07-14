//======================================================================
// IFÁ Processor V4
// Generic YÀRÁ Lifecycle Manager
//
// ONÍLẸ̀ owns and enforces YÀRÁ lifecycle state.
//
// Babaláwo privilege is required to invoke these ONÍLẸ̀ services:
//
//   CREATE
//   SELECT
//   PAUSE
//   RESUME
//   DESTROY
//
// Lifecycle rules:
//
//   CREATE
//       - initializes a fixed YÀRÁ slot
//       - marks it valid
//       - marks it running
//       - emits a one-cycle clear pulse
//
//   SELECT
//       - succeeds only for a valid, running YÀRÁ
//
//   PAUSE
//       - preserves context and RMU state
//       - prevents execution
//
//   RESUME
//       - restores execution availability
//
//   DESTROY
//       - invalidates the YÀRÁ
//       - stops it
//       - emits a one-cycle clear pulse
//
// Only one lifecycle command is accepted per cycle.
// Priority:
//
//   CREATE > SELECT > PAUSE > RESUME > DESTROY
//======================================================================

module ifa_yara_manager #(
    // Retained temporarily for compatibility with existing modules
    // and testbenches.
    parameter integer YARA_COUNT = 2,

    // Official V4 operating-system capacity parameter.
    parameter integer MAX_YARA = YARA_COUNT,

    parameter integer YARA_W =
        (MAX_YARA <= 1) ? 1 : $clog2(MAX_YARA)
)(
    input  logic                       clk,
    input  logic                       rst,

    // Babaláwo privilege level.
    input  logic                       babalawo_mode,

    // ONÍLẸ̀ lifecycle commands.
    input  logic                       create_valid,
    input  logic                       select_valid,
    input  logic                       pause_valid,
    input  logic                       resume_valid,
    input  logic                       destroy_valid,

    input  logic [YARA_W-1:0]          command_yara,

    // Current active YÀRÁ.
    output logic [YARA_W-1:0]          active_yara,
    output logic                       active_valid,
    output logic                       active_running,

    // Indexed lifecycle state.
    output logic [MAX_YARA-1:0]        yara_valid,
    output logic [MAX_YARA-1:0]        yara_running,

    // One-cycle local-state clear pulse.
    output logic [MAX_YARA-1:0]        clear_yara,

    // Command result.
    output logic                       command_allowed,
    output logic                       command_denied,

    // Statistics.
    output logic [31:0]                switch_count,
    output logic [31:0]                denied_count
);

    //==================================================================
    // Parameter validation
    //==================================================================

    initial begin
        if (MAX_YARA < 1) begin
            $error(
                "ifa_yara_manager: MAX_YARA must be at least 1"
            );
            $finish;
        end
    end

    //==================================================================
    // Safe identifier validation
    //
    // This is required when MAX_YARA is not a power of two.
    //
    // Example:
    //
    //   MAX_YARA = 5
    //   YARA_W    = 3
    //
    // Three bits can represent 0 through 7, but IDs 5, 6 and 7 must
    // never index the state arrays.
    //==================================================================

    logic command_yara_valid;
    logic active_yara_in_range;

    always_comb begin
        command_yara_valid =
            (command_yara < MAX_YARA);

        active_yara_in_range =
            (active_yara < MAX_YARA);
    end

    //==================================================================
    // Lifecycle state machine
    //==================================================================

    always_ff @(posedge clk) begin
        if (rst) begin
            active_yara    <= '0;

            yara_valid     <= '0;
            yara_running   <= '0;
            clear_yara     <= '0;

            command_allowed <= 1'b0;
            command_denied  <= 1'b0;

            switch_count   <= 32'd0;
            denied_count   <= 32'd0;
        end else begin

            //----------------------------------------------------------
            // Default one-cycle outputs
            //----------------------------------------------------------

            clear_yara      <= '0;
            command_allowed <= 1'b0;
            command_denied  <= 1'b0;

            //----------------------------------------------------------
            // CREATE
            //
            // A create operation initializes the selected fixed slot.
            //
            // Re-creating an already valid room is denied. This avoids
            // accidentally clearing a live execution context.
            //----------------------------------------------------------

            if (create_valid) begin
                if (
                    babalawo_mode &&
                    command_yara_valid &&
                    !yara_valid[command_yara]
                ) begin
                    yara_valid[command_yara]   <= 1'b1;
                    yara_running[command_yara] <= 1'b1;

                    clear_yara[command_yara] <= 1'b1;

                    command_allowed <= 1'b1;
                end else begin
                    command_denied <= 1'b1;
                    denied_count   <= denied_count + 32'd1;
                end
            end

            //----------------------------------------------------------
            // SELECT
            //
            // A YÀRÁ may become active only when it exists and is
            // currently running.
            //----------------------------------------------------------

            else if (select_valid) begin
                if (
                    babalawo_mode &&
                    command_yara_valid &&
                    yara_valid[command_yara] &&
                    yara_running[command_yara]
                ) begin
                    active_yara <= command_yara;

                    command_allowed <= 1'b1;
                    switch_count    <= switch_count + 32'd1;
                end else begin
                    command_denied <= 1'b1;
                    denied_count   <= denied_count + 32'd1;
                end
            end

            //----------------------------------------------------------
            // PAUSE
            //
            // Pausing preserves the YÀRÁ context and local RMU.
            //----------------------------------------------------------

            else if (pause_valid) begin
                if (
                    babalawo_mode &&
                    command_yara_valid &&
                    yara_valid[command_yara] &&
                    yara_running[command_yara]
                ) begin
                    yara_running[command_yara] <= 1'b0;

                    command_allowed <= 1'b1;
                end else begin
                    command_denied <= 1'b1;
                    denied_count   <= denied_count + 32'd1;
                end
            end

            //----------------------------------------------------------
            // RESUME
            //----------------------------------------------------------

            else if (resume_valid) begin
                if (
                    babalawo_mode &&
                    command_yara_valid &&
                    yara_valid[command_yara] &&
                    !yara_running[command_yara]
                ) begin
                    yara_running[command_yara] <= 1'b1;

                    command_allowed <= 1'b1;
                end else begin
                    command_denied <= 1'b1;
                    denied_count   <= denied_count + 32'd1;
                end
            end

            //----------------------------------------------------------
            // DESTROY
            //
            // Destroying a room invalidates it and clears all local
            // state owned by that YÀRÁ.
            //----------------------------------------------------------

            else if (destroy_valid) begin
                if (
                    babalawo_mode &&
                    command_yara_valid &&
                    yara_valid[command_yara]
                ) begin
                    yara_valid[command_yara]   <= 1'b0;
                    yara_running[command_yara] <= 1'b0;

                    clear_yara[command_yara] <= 1'b1;

                    command_allowed <= 1'b1;

                    //--------------------------------------------------
                    // If the destroyed YÀRÁ was active, active_yara
                    // retains its numeric ID, but active_valid and
                    // active_running immediately become false through
                    // the lifecycle state outputs.
                    //--------------------------------------------------

                end else begin
                    command_denied <= 1'b1;
                    denied_count   <= denied_count + 32'd1;
                end
            end
        end
    end

    //==================================================================
    // Active-YÀRÁ state
    //
    // Never index arrays with an out-of-range active ID.
    //==================================================================

    always_comb begin
        active_valid   = 1'b0;
        active_running = 1'b0;

        if (active_yara_in_range) begin
            active_valid   = yara_valid[active_yara];
            active_running = yara_running[active_yara];
        end
    end

endmodule
