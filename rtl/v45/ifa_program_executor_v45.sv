//======================================================================
// IFÁ Processor V4.5
// Backward-compatible Program Executor
//
// Purpose:
//     Fetch and decode instructions, then dispatch native mathematics
//     through the existing ONÍLẸ̀ kernel.
//
// This module does NOT contain:
//     - an RAU
//     - an RMU
//     - a YÀRÁ context bank
//     - lifecycle/security logic
//
// Those remain owned by the ONÍLẸ̀ kernel.
//
//---------------------------------------------------------------------
// Initial 16-bit V4 instruction format
//---------------------------------------------------------------------
//
// [15:12] Major instruction class
//
// 0x0 : branch/jump
//       [11:8] condition
//           0x1 BR_EQ
//           0x2 BR_GT
//           0x3 BR_LT
//           0x4 JMP
//       [7:0] target PC
//
// 0x1 : LDAI
//       A <- instruction[7:0]
//
// 0x2 : LDBI
//       B <- instruction[7:0]
//
// 0x3 : LDADDR
//       Address <- instruction[7:0]
//
// 0x4 : DATA
//       [11:8]
//           0x0 MOVY_A       A <- relation Y
//           0x1 MOVY_B       B <- relation Y
//           0x2 MOVADDR_A    Address <- A
//           0x3 MOVADDR_B    Address <- B
//           0x4 LOAD_A       A <- Memory[Address]
//           0x5 LOAD_B       B <- Memory[Address]
//           0x6 STORE_A      Memory[Address] <- A
//           0x7 STORE_B      Memory[Address] <- B
//
// 0x8 : NATIVE
//       [11:8] native operation
//
//           0x0 PAPO
//           0x1 YO
//           0x2 DAGBA
//           0x3 PIN
//           0x4 KU
//           0x5 GBE
//           0x6 SEDA
//           0x7 JU
//           0x8 KERE
//
//       Operands are the active YÀRÁ A and B registers.
//
// 0xF : system
//       [11:8]
//           0x0 NOP
//           0x1 HALT
//           0x2 PRINTY
//           0x3 PRINTRA
//           0x4 PRINTRD
//           0x5 PRINTR0
//           0x6 PRINTT
//           0x7 PRINTOP
//           0x8 PRINTSTATUS
//           0x9 RPUSH
//           0xA RPOP
//           0xB CALL target
//           0xC RET
//
//======================================================================

module ifa_program_executor_v45 #(
    parameter integer WIDTH      = 8,
    parameter integer OP_WIDTH   = 4,
    parameter integer IR_WIDTH   = 16,
    parameter integer IMEM_DEPTH = 256,
    parameter integer IMEM_AW    = 8,
    parameter integer STACK_DEPTH = 16,

    parameter integer RELATION_STACK_WIDTH =
        (9 * WIDTH) + OP_WIDTH + 14,

    parameter         INIT_FILE  = ""
) (
    input  logic clk,
    input  logic rst,

    //------------------------------------------------------------------
    // Program control
    //------------------------------------------------------------------

    input  logic start,
    input  logic step,
    input  logic stop,

    output logic busy,
    output logic halted,
    output logic fault,

    //------------------------------------------------------------------
    // Program-memory administration
    //------------------------------------------------------------------

    input  logic                     imem_write_valid,
    input  logic [IMEM_AW-1:0]       imem_write_address,
    input  logic [IR_WIDTH-1:0]      imem_write_data,

    //------------------------------------------------------------------
    // Active YÀRÁ context from the ONÍLẸ̀ kernel
    //------------------------------------------------------------------

    input  logic                     active_valid,
    input  logic                     active_running,

    input  logic [WIDTH-1:0]         active_pc,
    input  logic [IR_WIDTH-1:0]      active_ir,
    input  logic [WIDTH-1:0]         active_a,
    input  logic [WIDTH-1:0]         active_b,
    input  logic [WIDTH-1:0]         active_address,
    input  logic [WIDTH-1:0]         active_flags,
    input  logic [WIDTH-1:0]         active_sp,

    //------------------------------------------------------------------
    // Context-write request to the ONÍLẸ̀ kernel
    //------------------------------------------------------------------

    output logic                     context_write,

    output logic [WIDTH-1:0]         write_pc,
    output logic [IR_WIDTH-1:0]      write_ir,
    output logic [WIDTH-1:0]         write_a,
    output logic [WIDTH-1:0]         write_b,
    output logic [WIDTH-1:0]         write_address,
    output logic [WIDTH-1:0]         write_flags,
    output logic [WIDTH-1:0]         write_sp,

    //------------------------------------------------------------------
    // Shared stack request to the ONÍLẸ̀ kernel
    //------------------------------------------------------------------

    output logic                     stack_write_valid,
    output logic                     stack_read_valid,

    // Address used for the current stack transaction.
    //
    // RPUSH: active_sp
    // RPOP : active_sp - 1
    output logic [WIDTH-1:0]         stack_access_sp,

    output logic [RELATION_STACK_WIDTH-1:0]
                                             stack_write_data,

    input  logic [RELATION_STACK_WIDTH-1:0]
                                             stack_read_data,
    input  logic                     stack_write_done,
    input  logic                     stack_read_done,
    input  logic                     stack_allowed,
    input  logic                     stack_denied,

    //------------------------------------------------------------------
    // IFÁ relation-stack status
    //
    // stack_transport:
    //     A relation could not enter the current local stack window.
    //
    // relation_absent:
    //     A restore was requested when no preserved relation existed.
    //
    // These are not classical overflow/underflow flags.
    //------------------------------------------------------------------

    output logic                     stack_transport,
    output logic                     relation_absent,

    //------------------------------------------------------------------
    // Relation restoration request to ONÍLẸ̀
    //------------------------------------------------------------------

    output logic                     restore_valid,

    output logic [OP_WIDTH-1:0]      restore_op,

    output logic [WIDTH-1:0]         restore_y,
    output logic [WIDTH-1:0]         restore_ra,
    output logic [WIDTH-1:0]         restore_rd,
    output logic [WIDTH-1:0]         restore_r0,
    output logic [WIDTH-1:0]         restore_t,

    input  logic                     restore_done,

    //------------------------------------------------------------------
    // Native-operation request to the ONÍLẸ̀ kernel
    //------------------------------------------------------------------

    output logic                     execute_valid,
    output logic [OP_WIDTH-1:0]      execute_op,
    output logic [WIDTH-1:0]         execute_a,
    output logic [WIDTH-1:0]         execute_b,

    //------------------------------------------------------------------
    // Native status returned by the ONÍLẸ̀ kernel
    //------------------------------------------------------------------

    input  logic                     operation_valid,

    input  logic                     exception_valid,
    input  logic [3:0]               exception_code,

    input  logic                     state_valid,
    input  logic [3:0]               state_code,

    input  logic                     eq_flag,
    input  logic                     gt_flag,
    input  logic                     lt_flag,

    //------------------------------------------------------------------
    // Active operation-aware relation frame from the kernel
    //------------------------------------------------------------------

    input  logic [WIDTH-1:0]         active_frame_y,
    input  logic [WIDTH-1:0]         active_frame_ra,
    input  logic [WIDTH-1:0]         active_frame_rd,
    input  logic [WIDTH-1:0]         active_frame_r0,
    input  logic [WIDTH-1:0]         active_frame_t,
    input  logic [OP_WIDTH-1:0]      active_frame_op,

    //------------------------------------------------------------------
    // V4.5 compiler-visible General Memory request
    //------------------------------------------------------------------

    output logic                     mem_request,
    output logic                     mem_write,
    output logic [WIDTH-1:0]         mem_address,
    output logic [WIDTH-1:0]         mem_write_data,

    input  logic [WIDTH-1:0]         mem_read_data,
    input  logic                     mem_allowed,
    input  logic                     mem_denied,

    //------------------------------------------------------------------
    // Program-controlled output
    //------------------------------------------------------------------

    output logic                     print_valid,
    output logic [3:0]               print_kind,
    output logic [WIDTH-1:0]         print_data,

    //------------------------------------------------------------------
    // Executor inspection
    //------------------------------------------------------------------

    output logic [WIDTH-1:0]         executor_pc,
    output logic [IR_WIDTH-1:0]      executor_ir,
    output logic [3:0]               executor_state,

    output logic                     instruction_done,

    output logic                     last_operation_valid,
    output logic                     last_exception_valid,
    output logic [3:0]               last_exception_code,
    output logic                     last_state_valid,
    output logic [3:0]               last_state_code
);

    //------------------------------------------------------------------
    // Native operation constants
    //------------------------------------------------------------------

    localparam logic [OP_WIDTH-1:0] OP_PAPO  = 4'h0;
    localparam logic [OP_WIDTH-1:0] OP_YO    = 4'h1;
    localparam logic [OP_WIDTH-1:0] OP_DAGBA = 4'h2;
    localparam logic [OP_WIDTH-1:0] OP_PIN   = 4'h3;
    localparam logic [OP_WIDTH-1:0] OP_KU    = 4'h4;
    localparam logic [OP_WIDTH-1:0] OP_GBE   = 4'h5;
    localparam logic [OP_WIDTH-1:0] OP_SEDA  = 4'h6;
    localparam logic [OP_WIDTH-1:0] OP_JU    = 4'h7;
    localparam logic [OP_WIDTH-1:0] OP_KERE  = 4'h8;

    //------------------------------------------------------------------
    // Program memory
    //------------------------------------------------------------------

    logic [IR_WIDTH-1:0] imem [0:IMEM_DEPTH-1];

    integer index;

    initial begin
        for (index = 0; index < IMEM_DEPTH; index = index + 1)
            imem[index] = {IR_WIDTH{1'b0}};

        if (INIT_FILE != "")
            $readmemh(INIT_FILE, imem);
    end

    always_ff @(posedge clk) begin
        if (imem_write_valid)
            imem[imem_write_address] <= imem_write_data;
    end

    //------------------------------------------------------------------
    // Executor state
    //------------------------------------------------------------------

    typedef enum logic [3:0] {
        ST_IDLE          = 4'h0,
        ST_FETCH         = 4'h1,
        ST_DECODE        = 4'h2,
        ST_WAIT_NATIVE   = 4'h3,
        ST_COMMIT        = 4'h4,
        ST_HALTED           = 4'h5,
        ST_WAIT_STACK_WRITE = 4'h6,
        ST_WAIT_STACK_READ  = 4'h7,
        ST_WAIT_RESTORE     = 4'h8,
        ST_WAIT_MEMORY      = 4'h9,
        ST_FAULT            = 4'hF
    } executor_state_t;

    executor_state_t state;

    logic [IR_WIDTH-1:0] fetched_ir;
    logic step_latched;

    //------------------------------------------------------------------
    // Pending relation-stack write purpose
    //
    // RPUSH resumes at PC + 1.
    // CALL transfers to pending_call_target after the frame is saved.
    //------------------------------------------------------------------

    logic pending_stack_call;
    logic [WIDTH-1:0] pending_call_target;

    // Selects whether the current relation restore is RPOP or RET.
    logic pending_stack_return;
    logic [WIDTH-1:0] pending_return_y;

    //------------------------------------------------------------------
    // Decoded IFÁ relation-stack entry
    //------------------------------------------------------------------

    logic [WIDTH-1:0] saved_return_pc;

    logic [OP_WIDTH-1:0] saved_op;

    logic [WIDTH-1:0] saved_y;
    logic [WIDTH-1:0] saved_ra;
    logic [WIDTH-1:0] saved_rd;
    logic [WIDTH-1:0] saved_r0;
    logic [WIDTH-1:0] saved_t;

    logic saved_valid;

    logic saved_exception;
    logic [3:0] saved_exception_code;

    logic saved_state;
    logic [3:0] saved_state_code;

    logic saved_eq;
    logic saved_gt;
    logic saved_lt;

    // V4.5 language-call state.  These fields are deliberately appended
    // only to the V4.5 stack format; the V4 relation frame is unchanged.
    logic [WIDTH-1:0] saved_a;
    logic [WIDTH-1:0] saved_b;
    logic [WIDTH-1:0] saved_address;

    logic pending_memory_load;
    logic pending_memory_target_b;

    //------------------------------------------------------------------
    // Canonical relation-stack frame unpacking
    //------------------------------------------------------------------

    always_comb begin
        {
            saved_return_pc,

            saved_op,

            saved_y,
            saved_ra,
            saved_rd,
            saved_r0,
            saved_t,

            saved_valid,

            saved_exception,
            saved_exception_code,

            saved_state,
            saved_state_code,

            saved_eq,
            saved_gt,
            saved_lt,

            saved_a,
            saved_b,
            saved_address
        } = stack_read_data;
    end

    //------------------------------------------------------------------
    // Utility: prepare a complete context write
    //------------------------------------------------------------------

    task automatic prepare_context_write;
        input logic [WIDTH-1:0] next_pc;
        input logic [IR_WIDTH-1:0] next_ir;
        input logic [WIDTH-1:0] next_a;
        input logic [WIDTH-1:0] next_b;
        input logic [WIDTH-1:0] next_address;
        input logic [WIDTH-1:0] next_flags;
        begin
            write_pc      <= next_pc;
            write_ir      <= next_ir;
            write_a       <= next_a;
            write_b       <= next_b;
            write_address <= next_address;
            write_flags   <= next_flags;
            write_sp      <= active_sp;

            context_write <= 1'b1;
        end
    endtask

    //------------------------------------------------------------------
    // Utility: prepare a complete context write with a new SP
    //------------------------------------------------------------------

    task automatic prepare_context_write_with_sp;
        input logic [WIDTH-1:0] next_pc;
        input logic [IR_WIDTH-1:0] next_ir;
        input logic [WIDTH-1:0] next_a;
        input logic [WIDTH-1:0] next_b;
        input logic [WIDTH-1:0] next_address;
        input logic [WIDTH-1:0] next_flags;
        input logic [WIDTH-1:0] next_sp;
        begin
            write_pc      <= next_pc;
            write_ir      <= next_ir;
            write_a       <= next_a;
            write_b       <= next_b;
            write_address <= next_address;
            write_flags   <= next_flags;
            write_sp      <= next_sp;

            context_write <= 1'b1;
        end
    endtask

    //------------------------------------------------------------------
    // Inspection outputs
    //------------------------------------------------------------------

    always_comb begin
        busy = (
            state != ST_IDLE
            && state != ST_HALTED
            && state != ST_FAULT
        );

        executor_pc    = active_pc;
        executor_ir    = fetched_ir;
        executor_state = state;
    end

    //------------------------------------------------------------------
    // Fetch/decode/dispatch FSM
    //------------------------------------------------------------------

    always_ff @(posedge clk) begin
        if (rst) begin
            state <= ST_IDLE;

            fetched_ir <= {IR_WIDTH{1'b0}};
            step_latched <= 1'b0;

            pending_stack_call   <= 1'b0;
            pending_call_target  <= {WIDTH{1'b0}};
            pending_stack_return <= 1'b0;
            pending_return_y      <= {WIDTH{1'b0}};

            halted <= 1'b0;
            fault  <= 1'b0;

            context_write <= 1'b0;

            write_pc      <= {WIDTH{1'b0}};
            write_ir      <= {IR_WIDTH{1'b0}};
            write_a       <= {WIDTH{1'b0}};
            write_b       <= {WIDTH{1'b0}};
            write_address <= {WIDTH{1'b0}};
            write_flags   <= {WIDTH{1'b0}};
            write_sp      <= {WIDTH{1'b0}};

            stack_write_valid <= 1'b0;
            stack_read_valid  <= 1'b0;
            stack_access_sp   <= {WIDTH{1'b0}};
            stack_write_data <= {
                RELATION_STACK_WIDTH{1'b0}
            };

            stack_transport <= 1'b0;
            relation_absent <= 1'b0;

            restore_valid <= 1'b0;

            restore_op <= {OP_WIDTH{1'b0}};

            restore_y  <= {WIDTH{1'b0}};
            restore_ra <= {WIDTH{1'b0}};
            restore_rd <= {WIDTH{1'b0}};
            restore_r0 <= {WIDTH{1'b0}};
            restore_t  <= {WIDTH{1'b0}};

            execute_valid <= 1'b0;
            execute_op    <= OP_PAPO;
            execute_a     <= {WIDTH{1'b0}};
            execute_b     <= {WIDTH{1'b0}};

            mem_request    <= 1'b0;
            mem_write      <= 1'b0;
            mem_address    <= {WIDTH{1'b0}};
            mem_write_data <= {WIDTH{1'b0}};
            pending_memory_load <= 1'b0;
            pending_memory_target_b <= 1'b0;

            instruction_done <= 1'b0;

            print_valid <= 1'b0;
            print_kind  <= 4'h0;
            print_data  <= {WIDTH{1'b0}};

            last_operation_valid <= 1'b0;

            last_exception_valid <= 1'b0;
            last_exception_code  <= 4'h0;

            last_state_valid <= 1'b0;
            last_state_code  <= 4'h0;
        end else begin
            //------------------------------------------------------------------
            // Default one-cycle controls
            //------------------------------------------------------------------

            context_write    <= 1'b0;
            execute_valid    <= 1'b0;
            stack_write_valid <= 1'b0;
            stack_read_valid  <= 1'b0;
            restore_valid     <= 1'b0;
            instruction_done <= 1'b0;
            print_valid      <= 1'b0;
            mem_request      <= 1'b0;

            //------------------------------------------------------------------
            // External stop
            //------------------------------------------------------------------

            if (stop) begin
                state  <= ST_HALTED;
                halted <= 1'b1;
            end else begin
                case (state)

                    //----------------------------------------------------------
                    // Waiting for RUN or STEP
                    //----------------------------------------------------------

                    ST_IDLE: begin
                        halted <= 1'b0;
                        fault  <= 1'b0;

                        if (start || step) begin
                            if (!active_valid || !active_running) begin
                                fault <= 1'b1;
                                state <= ST_FAULT;
                            end else begin
                                step_latched <= step;
                                state <= ST_FETCH;
                            end
                        end
                    end

                    //----------------------------------------------------------
                    // Fetch from program memory using active YÀRÁ PC
                    //----------------------------------------------------------

                    ST_FETCH: begin
                        if (!active_valid || !active_running) begin
                            fault <= 1'b1;
                            state <= ST_FAULT;
                        end else begin
                            fetched_ir <= imem[active_pc[IMEM_AW-1:0]];
                            state <= ST_DECODE;
                        end
                    end

                    //----------------------------------------------------------
                    // Decode one instruction
                    //----------------------------------------------------------

                    ST_DECODE: begin
                        case (fetched_ir[15:12])

                            //--------------------------------------------------
                            // Branch and jump
                            //--------------------------------------------------

                            4'h0: begin
                                case (fetched_ir[11:8])

                                    4'h1: begin
                                        prepare_context_write(
                                            active_flags[2]
                                                ? fetched_ir[7:0]
                                                : active_pc + 1'b1,
                                            fetched_ir,
                                            active_a,
                                            active_b,
                                            active_address,
                                            active_flags
                                        );
                                    end

                                    4'h2: begin
                                        prepare_context_write(
                                            active_flags[1]
                                                ? fetched_ir[7:0]
                                                : active_pc + 1'b1,
                                            fetched_ir,
                                            active_a,
                                            active_b,
                                            active_address,
                                            active_flags
                                        );
                                    end

                                    4'h3: begin
                                        prepare_context_write(
                                            active_flags[0]
                                                ? fetched_ir[7:0]
                                                : active_pc + 1'b1,
                                            fetched_ir,
                                            active_a,
                                            active_b,
                                            active_address,
                                            active_flags
                                        );
                                    end

                                    4'h4: begin
                                        prepare_context_write(
                                            fetched_ir[7:0],
                                            fetched_ir,
                                            active_a,
                                            active_b,
                                            active_address,
                                            active_flags
                                        );
                                    end

                                    default: begin
                                        prepare_context_write(
                                            active_pc + 1'b1,
                                            fetched_ir,
                                            active_a,
                                            active_b,
                                            active_address,
                                            active_flags
                                        );
                                    end
                                endcase

                                state <= ST_COMMIT;
                            end

                            //--------------------------------------------------
                            // Load immediate A
                            //--------------------------------------------------

                            4'h1: begin
                                prepare_context_write(
                                    active_pc + 1'b1,
                                    fetched_ir,
                                    fetched_ir[7:0],
                                    active_b,
                                    active_address,
                                    active_flags
                                );

                                state <= ST_COMMIT;
                            end

                            //--------------------------------------------------
                            // Load immediate B
                            //--------------------------------------------------

                            4'h2: begin
                                prepare_context_write(
                                    active_pc + 1'b1,
                                    fetched_ir,
                                    active_a,
                                    fetched_ir[7:0],
                                    active_address,
                                    active_flags
                                );

                                state <= ST_COMMIT;
                            end

                            //--------------------------------------------------
                            // Load address
                            //--------------------------------------------------

                            4'h3: begin
                                prepare_context_write(
                                    active_pc + 1'b1,
                                    fetched_ir,
                                    active_a,
                                    active_b,
                                    fetched_ir[7:0],
                                    active_flags
                                );

                                state <= ST_COMMIT;
                            end

                            //--------------------------------------------------
                            // V4.5 data movement and General Memory
                            //--------------------------------------------------

                            4'h4: begin
                                case (fetched_ir[11:8])
                                    4'h0: begin
                                        prepare_context_write(
                                            active_pc + 1'b1, fetched_ir,
                                            active_frame_y, active_b,
                                            active_address, active_flags
                                        );
                                        state <= ST_COMMIT;
                                    end
                                    4'h1: begin
                                        prepare_context_write(
                                            active_pc + 1'b1, fetched_ir,
                                            active_a, active_frame_y,
                                            active_address, active_flags
                                        );
                                        state <= ST_COMMIT;
                                    end
                                    4'h2: begin
                                        prepare_context_write(
                                            active_pc + 1'b1, fetched_ir,
                                            active_a, active_b,
                                            active_a, active_flags
                                        );
                                        state <= ST_COMMIT;
                                    end
                                    4'h3: begin
                                        prepare_context_write(
                                            active_pc + 1'b1, fetched_ir,
                                            active_a, active_b,
                                            active_b, active_flags
                                        );
                                        state <= ST_COMMIT;
                                    end
                                    4'h4, 4'h5, 4'h6, 4'h7: begin
                                        pending_memory_load <=
                                            !fetched_ir[9];
                                        pending_memory_target_b <=
                                            fetched_ir[8];
                                        mem_write <= fetched_ir[9];
                                        mem_address <= active_address;
                                        mem_write_data <= fetched_ir[8]
                                            ? active_b : active_a;
                                        mem_request <= 1'b1;
                                        state <= ST_WAIT_MEMORY;
                                    end
                                    default: begin
                                        fault <= 1'b1;
                                        state <= ST_FAULT;
                                    end
                                endcase
                            end

                            //--------------------------------------------------
                            // Native relation mathematics
                            //--------------------------------------------------

                            4'h8: begin
                                if (fetched_ir[11:8] <= OP_KERE) begin
                                    execute_op <= fetched_ir[11:8];
                                    execute_a  <= active_a;
                                    execute_b  <= active_b;

                                    execute_valid <= 1'b1;
                                    state <= ST_WAIT_NATIVE;
                                end else begin
                                    fault <= 1'b1;
                                    state <= ST_FAULT;
                                end
                            end

                            //--------------------------------------------------
                            // System operations
                            //--------------------------------------------------

                            4'hF: begin
                                case (fetched_ir[11:8])

                                    4'h0: begin
                                        // NOP
                                        prepare_context_write(
                                            active_pc + 1'b1,
                                            fetched_ir,
                                            active_a,
                                            active_b,
                                            active_address,
                                            active_flags
                                        );

                                        state <= ST_COMMIT;
                                    end

                                    4'h1: begin
                                        // HALT
                                        halted <= 1'b1;
                                        state <= ST_HALTED;
                                    end

                                    4'h2: begin
                                        // PRINTY
                                        print_kind  <= 4'h1;
                                        print_data  <= active_frame_y;
                                        print_valid <= 1'b1;

                                        prepare_context_write(
                                            active_pc + 1'b1,
                                            fetched_ir,
                                            active_a,
                                            active_b,
                                            active_address,
                                            active_flags
                                        );

                                        state <= ST_COMMIT;
                                    end

                                    4'h3: begin
                                        // PRINTRA
                                        print_kind  <= 4'h2;
                                        print_data  <= active_frame_ra;
                                        print_valid <= 1'b1;

                                        prepare_context_write(
                                            active_pc + 1'b1,
                                            fetched_ir,
                                            active_a,
                                            active_b,
                                            active_address,
                                            active_flags
                                        );

                                        state <= ST_COMMIT;
                                    end

                                    4'h4: begin
                                        // PRINTRD
                                        print_kind  <= 4'h3;
                                        print_data  <= active_frame_rd;
                                        print_valid <= 1'b1;

                                        prepare_context_write(
                                            active_pc + 1'b1,
                                            fetched_ir,
                                            active_a,
                                            active_b,
                                            active_address,
                                            active_flags
                                        );

                                        state <= ST_COMMIT;
                                    end

                                    4'h5: begin
                                        // PRINTR0
                                        print_kind  <= 4'h4;
                                        print_data  <= active_frame_r0;
                                        print_valid <= 1'b1;

                                        prepare_context_write(
                                            active_pc + 1'b1,
                                            fetched_ir,
                                            active_a,
                                            active_b,
                                            active_address,
                                            active_flags
                                        );

                                        state <= ST_COMMIT;
                                    end

                                    4'h6: begin
                                        // PRINTT
                                        print_kind  <= 4'h5;
                                        print_data  <= active_frame_t;
                                        print_valid <= 1'b1;

                                        prepare_context_write(
                                            active_pc + 1'b1,
                                            fetched_ir,
                                            active_a,
                                            active_b,
                                            active_address,
                                            active_flags
                                        );

                                        state <= ST_COMMIT;
                                    end

                                    4'h7: begin
                                        // PRINTOP
                                        print_kind  <= 4'h6;
                                        print_data  <= {
                                            {(WIDTH-OP_WIDTH){1'b0}},
                                            active_frame_op
                                        };
                                        print_valid <= 1'b1;

                                        prepare_context_write(
                                            active_pc + 1'b1,
                                            fetched_ir,
                                            active_a,
                                            active_b,
                                            active_address,
                                            active_flags
                                        );

                                        state <= ST_COMMIT;
                                    end

                                    4'h8: begin
                                        // PRINTSTATUS
                                        //
                                        // bit 7 = VALID
                                        // bit 6 = EXC
                                        // bit 5 = STATE
                                        // bit 4 = reserved
                                        // bit 3 = reserved
                                        // bit 2 = EQ
                                        // bit 1 = GT
                                        // bit 0 = LT
                                        print_kind <= 4'h7;

                                        print_data <= {
                                            last_operation_valid,
                                            last_exception_valid,
                                            last_state_valid,
                                            2'b00,
                                            active_flags[2:0]
                                        };

                                        print_valid <= 1'b1;

                                        prepare_context_write(
                                            active_pc + 1'b1,
                                            fetched_ir,
                                            active_a,
                                            active_b,
                                            active_address,
                                            active_flags
                                        );

                                        state <= ST_COMMIT;
                                    end

                                    4'h9: begin
                                        // RPUSH
                                        //
                                        // Preserve the complete IFÁ
                                        // relation and its continuation.
                                        //
                                        // A full local relation window
                                        // produces STACK_TRANSPORT.
                                        //
                                        // This is not classical overflow.

                                        relation_absent <= 1'b0;
                                        pending_stack_call <= 1'b0;

                                        if (
                                            active_sp >= STACK_DEPTH
                                        ) begin
                                            stack_transport <= 1'b1;

                                            // No stack write. SP remains
                                            // unchanged, while execution
                                            // continues so software can
                                            // inspect STACK_TRANSPORT.
                                            prepare_context_write(
                                                active_pc + 1'b1,
                                                fetched_ir,
                                                active_a,
                                                active_b,
                                                active_address,
                                                active_flags
                                            );

                                            state <= ST_COMMIT;
                                        end else begin
                                            stack_transport <= 1'b0;

                                            stack_access_sp <=
                                                active_sp;

                                            stack_write_data <= {
                                                active_pc + 1'b1,

                                                active_frame_op,

                                                active_frame_y,
                                                active_frame_ra,
                                                active_frame_rd,
                                                active_frame_r0,
                                                active_frame_t,

                                                last_operation_valid,

                                                last_exception_valid,
                                                last_exception_code,

                                                last_state_valid,
                                                last_state_code,

                                                active_flags[2],
                                                active_flags[1],
                                                active_flags[0],

                                                active_a,
                                                active_b,
                                                active_address
                                            };

                                            stack_write_valid <= 1'b1;
                                            state <=
                                                ST_WAIT_STACK_WRITE;
                                        end
                                    end

                                    4'hA: begin
                                        // RPOP
                                        //
                                        // Restore the most recently
                                        // preserved IFÁ relation.
                                        //
                                        // An empty local relation stack
                                        // produces RELATION_ABSENT.
                                        //
                                        // This is not classical underflow.

                                        stack_transport <= 1'b0;
                                        pending_stack_return <= 1'b0;

                                        if (active_sp == 0) begin
                                            relation_absent <= 1'b1;

                                            // No read and no SP movement.
                                            // Advance so software may
                                            // inspect RELATION_ABSENT.
                                            prepare_context_write(
                                                active_pc + 1'b1,
                                                fetched_ir,
                                                active_a,
                                                active_b,
                                                active_address,
                                                active_flags
                                            );

                                            state <= ST_COMMIT;
                                        end else begin
                                            relation_absent <= 1'b0;

                                            stack_access_sp <=
                                                active_sp - 1'b1;

                                            stack_read_valid <= 1'b1;

                                            state <=
                                                ST_WAIT_STACK_READ;
                                        end
                                    end

                                    4'hB: begin
                                        // CALL target
                                        //
                                        // Preserve the current relation
                                        // and continuation before transfer.
                                        //
                                        // If the frame cannot enter the
                                        // current local relation window,
                                        // assert STACK_TRANSPORT and do
                                        // not transfer control.

                                        relation_absent <= 1'b0;
                                        pending_stack_call <= 1'b1;
                                        pending_call_target <=
                                            fetched_ir[7:0];

                                        if (
                                            active_sp >= STACK_DEPTH
                                        ) begin
                                            stack_transport <= 1'b1;
                                            pending_stack_call <= 1'b0;

                                            prepare_context_write(
                                                active_pc + 1'b1,
                                                fetched_ir,
                                                active_a,
                                                active_b,
                                                active_address,
                                                active_flags
                                            );

                                            state <= ST_COMMIT;
                                        end else begin
                                            stack_transport <= 1'b0;

                                            stack_access_sp <=
                                                active_sp;

                                            stack_write_data <= {
                                                active_pc + 1'b1,

                                                active_frame_op,

                                                active_frame_y,
                                                active_frame_ra,
                                                active_frame_rd,
                                                active_frame_r0,
                                                active_frame_t,

                                                last_operation_valid,

                                                last_exception_valid,
                                                last_exception_code,

                                                last_state_valid,
                                                last_state_code,

                                                active_flags[2],
                                                active_flags[1],
                                                active_flags[0],

                                                active_a,
                                                active_b,
                                                active_address
                                            };

                                            stack_write_valid <= 1'b1;

                                            state <=
                                                ST_WAIT_STACK_WRITE;
                                        end
                                    end

                                    4'hC: begin
                                        // RET
                                        //
                                        // Restore the most recently
                                        // preserved relation and resume
                                        // from its saved RETURN_PC.
                                        //
                                        // An empty local relation stack
                                        // produces RELATION_ABSENT.

                                        stack_transport <= 1'b0;
                                        pending_stack_return <= 1'b1;
                                        // Latch the callee result before the
                                        // caller relation is restored by RMU.
                                        pending_return_y <= active_frame_y;

                                        if (active_sp == 0) begin
                                            relation_absent <= 1'b1;
                                            pending_stack_return <= 1'b0;

                                            // No relation exists to
                                            // restore. SP is unchanged.
                                            prepare_context_write(
                                                active_pc + 1'b1,
                                                fetched_ir,
                                                active_a,
                                                active_b,
                                                active_address,
                                                active_flags
                                            );

                                            state <= ST_COMMIT;
                                        end else begin
                                            relation_absent <= 1'b0;

                                            stack_access_sp <=
                                                active_sp - 1'b1;

                                            stack_read_valid <= 1'b1;

                                            state <=
                                                ST_WAIT_STACK_READ;
                                        end
                                    end

                                    default: begin
                                        fault <= 1'b1;
                                        state <= ST_FAULT;
                                    end
                                endcase
                            end

                            //--------------------------------------------------
                            // Unknown major opcode
                            //--------------------------------------------------

                            default: begin
                                fault <= 1'b1;
                                state <= ST_FAULT;
                            end
                        endcase
                    end

                    //----------------------------------------------------------
                    // Kernel consumes execute_valid during this cycle.
                    //
                    // Preserve returned comparison predicates in the YÀRÁ
                    // context flags:
                    //
                    //     flags[2] = EQ
                    //     flags[1] = GT
                    //     flags[0] = LT
                    //----------------------------------------------------------

                    ST_WAIT_NATIVE: begin
                        last_operation_valid <= operation_valid;

                        last_exception_valid <= exception_valid;
                        last_exception_code  <= exception_code;

                        last_state_valid <= state_valid;
                        last_state_code  <= state_code;

                        prepare_context_write(
                            active_pc + 1'b1,
                            fetched_ir,
                            active_a,
                            active_b,
                            active_address,
                            {
                                {(WIDTH-3){1'b0}},
                                eq_flag,
                                gt_flag,
                                lt_flag
                            }
                        );

                        state <= ST_COMMIT;
                    end

                    //----------------------------------------------------------
                    // Wait for the one-cycle guarded memory request issued by
                    // decode to be accepted or denied.  The guard registers
                    // both the status and read data.
                    //----------------------------------------------------------

                    ST_WAIT_MEMORY: begin
                        if (mem_denied) begin
                            fault <= 1'b1;
                            state <= ST_FAULT;
                        end else if (mem_allowed) begin
                            prepare_context_write(
                                active_pc + 1'b1,
                                fetched_ir,
                                pending_memory_load &&
                                    !pending_memory_target_b
                                    ? mem_read_data : active_a,
                                pending_memory_load &&
                                    pending_memory_target_b
                                    ? mem_read_data : active_b,
                                active_address,
                                active_flags
                            );
                            state <= ST_COMMIT;
                        end
                    end

                    //----------------------------------------------------------
                    // Wait for the complete IFÁ relation frame to enter
                    // the local YÀRÁ stack window.
                    //----------------------------------------------------------

                    //----------------------------------------------------------
                    // Wait for the saved IFÁ relation frame.
                    //----------------------------------------------------------

                    ST_WAIT_STACK_READ: begin
                        if (stack_denied) begin
                            relation_absent <= 1'b1;
                            pending_stack_return <= 1'b0;

                            prepare_context_write(
                                active_pc + 1'b1,
                                fetched_ir,
                                active_a,
                                active_b,
                                active_address,
                                active_flags
                            );

                            state <= ST_COMMIT;
                        end
                        else if (
                            stack_read_done &&
                            stack_allowed
                        ) begin
                            relation_absent <= 1'b0;
                            stack_transport <= 1'b0;

                            // Feed the restored mathematical relation
                            // through ONÍLẸ̀'s existing RMU import path.
                            restore_op <= saved_op;

                            restore_y  <= saved_y;
                            restore_ra <= saved_ra;
                            restore_rd <= saved_rd;
                            restore_r0 <= saved_r0;
                            restore_t  <= saved_t;

                            restore_valid <= 1'b1;

                            state <= ST_WAIT_RESTORE;
                        end
                    end

                    //----------------------------------------------------------
                    // Wait for ONÍLẸ̀ to restore the relation into the
                    // active YÀRÁ local RMU.
                    //----------------------------------------------------------

                    ST_WAIT_RESTORE: begin
                        // Hold the request until the active local RMU
                        // acknowledges its administrative import.
                        restore_valid <= 1'b1;

                        if (restore_done) begin
                            restore_valid <= 1'b0;

                            stack_transport <= 1'b0;
                            relation_absent <= 1'b0;

                            // Restore the saved non-RMU status.
                            last_operation_valid <= saved_valid;

                            last_exception_valid <=
                                saved_exception;

                            last_exception_code <=
                                saved_exception_code;

                            last_state_valid <= saved_state;
                            last_state_code  <= saved_state_code;

                            if (pending_stack_return) begin
                                // RET resumes at the continuation saved
                                // by CALL.
                                prepare_context_write_with_sp(
                                    saved_return_pc,
                                    fetched_ir,
                                    // V4.5 return ABI: the callee's relation
                                    // result is delivered in A.  Caller B and
                                    // Address are restored from its frame.
                                    pending_return_y,
                                    saved_b,
                                    saved_address,
                                    {
                                        {(WIDTH-3){1'b0}},
                                        saved_eq,
                                        saved_gt,
                                        saved_lt
                                    },
                                    active_sp - 1'b1
                                );
                            end else begin
                                // RPOP resumes after itself.
                                prepare_context_write_with_sp(
                                    active_pc + 1'b1,
                                    fetched_ir,
                                    active_a,
                                    active_b,
                                    active_address,
                                    {
                                        {(WIDTH-3){1'b0}},
                                        saved_eq,
                                        saved_gt,
                                        saved_lt
                                    },
                                    active_sp - 1'b1
                                );
                            end

                            pending_stack_return <= 1'b0;
                            state <= ST_COMMIT;
                        end
                    end

                    ST_WAIT_STACK_WRITE: begin
                        if (stack_denied) begin
                            stack_transport <= 1'b1;
                            pending_stack_call <= 1'b0;

                            // Preserve SP and complete the instruction.
                            prepare_context_write(
                                active_pc + 1'b1,
                                fetched_ir,
                                active_a,
                                active_b,
                                active_address,
                                active_flags
                            );

                            state <= ST_COMMIT;
                        end
                        else if (
                            stack_write_done &&
                            stack_allowed
                        ) begin
                            stack_transport <= 1'b0;
                            relation_absent <= 1'b0;

                            if (pending_stack_call) begin
                                prepare_context_write_with_sp(
                                    pending_call_target,
                                    fetched_ir,
                                    active_a,
                                    active_b,
                                    active_address,
                                    active_flags,
                                    active_sp + 1'b1
                                );
                            end else begin
                                prepare_context_write_with_sp(
                                    active_pc + 1'b1,
                                    fetched_ir,
                                    active_a,
                                    active_b,
                                    active_address,
                                    active_flags,
                                    active_sp + 1'b1
                                );
                            end

                            pending_stack_call <= 1'b0;
                            state <= ST_COMMIT;
                        end
                    end

                    //----------------------------------------------------------
                    // Context write is committed by the kernel on this edge.
                    //----------------------------------------------------------

                    ST_COMMIT: begin
                        instruction_done <= 1'b1;

                        if (step_latched) begin
                            step_latched <= 1'b0;
                            state <= ST_IDLE;
                        end else begin
                            state <= ST_FETCH;
                        end
                    end

                    ST_HALTED: begin
                        halted <= 1'b1;

                        if (start || step) begin
                            halted <= 1'b0;
                            step_latched <= step;
                            state <= ST_FETCH;
                        end
                    end

                    ST_FAULT: begin
                        fault <= 1'b1;

                        if (start || step) begin
                            fault <= 1'b0;
                            step_latched <= step;
                            state <= ST_FETCH;
                        end
                    end

                    default: begin
                        fault <= 1'b1;
                        state <= ST_FAULT;
                    end
                endcase
            end
        end
    end

endmodule
