`timescale 1ns/1ps

//======================================================================
// IFÁ Processor V4
// Structured OS Command Bridge
//
// Usage:
//
//   vvp sim/v4/ifa_v4_os_bridge.out \
//       +CMD_FILE=sim/v4/os_commands.txt
//
// Supported commands:
//
//   CREATE <id>
//   SELECT <id>
//   PAUSE <id>
//   RESUME <id>
//   DESTROY <id>
//
//   CONTEXT <pc> <ir> <a> <b> <address> <flags>
//
//   EXEC <A> <B>
//
//   GRANT <src> <dst>
//   REVOKE <src> <dst>
//   SHARE <src> <dst>
//
//   MEMWRITE <address> <data>
//   MEMREAD <address>
//
//   MEMGRANTR <address> <yara>
//   MEMGRANTW <address> <yara>
//   MEMREVOKER <address> <yara>
//   MEMREVOKEW <address> <yara>
//
//   BABALAWO ON
//   BABALAWO OFF
//
//   STATUS
//   QUIT
//
// Numbers may be decimal or hexadecimal.
// Use hexadecimal with a 0x prefix.
//======================================================================

module tb_ifa_v45_os_bridge;

    string vcd_file;

    initial begin
        if ($value$plusargs("VCD=%s", vcd_file)) begin
            $dumpfile(vcd_file);
            $dumpvars(0, clk, rst, executor_busy, executor_halted, executor_fault, executor_pc, executor_ir, executor_state, executor_instruction_done, executor_print_valid, executor_print_kind, executor_print_data, active_pc, active_ir, active_a, active_b, active_address, active_flags, active_sp, executor_execute_valid, executor_execute_op, executor_execute_a, executor_execute_b, operation_valid, eq_flag, gt_flag, lt_flag, rmu_hit, rmu_miss, out_y, out_ra, out_rd, out_r0, out_t, executor_stack_write_valid, executor_stack_read_valid, executor_stack_access_sp, executor_restore_valid, kernel_restore_done, executor_context_write);
        end
    end

    localparam integer WIDTH      = 8;
    localparam integer OP_WIDTH   = 4;
    localparam integer IR_WIDTH   = 16;

    localparam logic [OP_WIDTH-1:0] OP_PAPO  = 4'h0;
    localparam logic [OP_WIDTH-1:0] OP_YO    = 4'h1;
    localparam logic [OP_WIDTH-1:0] OP_DAGBA = 4'h2;
    localparam logic [OP_WIDTH-1:0] OP_PIN   = 4'h3;
    localparam logic [OP_WIDTH-1:0] OP_KU    = 4'h4;
    localparam logic [OP_WIDTH-1:0] OP_GBE   = 4'h5;
    localparam logic [OP_WIDTH-1:0] OP_SEDA  = 4'h6;
    localparam logic [OP_WIDTH-1:0] OP_JU    = 4'h7;
    localparam logic [OP_WIDTH-1:0] OP_KERE  = 4'h8;
    localparam integer RMU_DEPTH  = 16;
    localparam integer MEM_ADDR_W = 4;

    localparam integer RELATION_STACK_WIDTH =
        (9 * WIDTH) + OP_WIDTH + 14;
    localparam integer MAX_YARA   = 4;

    localparam integer IMEM_DEPTH = 256;
    localparam integer IMEM_AW    = 8;

    localparam integer YARA_W =
        (MAX_YARA <= 1) ? 1 : $clog2(MAX_YARA);

    //==================================================================
    // Clock and reset
    //==================================================================

    logic clk;
    logic rst;

    always #5 clk = ~clk;

    //==================================================================
    // V4 program executor
    //==================================================================

    logic executor_start;
    logic executor_step;
    logic executor_stop;

    logic executor_busy;
    logic executor_halted;
    logic executor_fault;

    logic executor_imem_write_valid;
    logic [IMEM_AW-1:0] executor_imem_write_address;
    logic [IR_WIDTH-1:0] executor_imem_write_data;

    logic executor_context_write;

    logic [WIDTH-1:0] executor_write_pc;
    logic [IR_WIDTH-1:0] executor_write_ir;
    logic [WIDTH-1:0] executor_write_a;
    logic [WIDTH-1:0] executor_write_b;
    logic [WIDTH-1:0] executor_write_address;
    logic [WIDTH-1:0] executor_write_flags;
    logic [WIDTH-1:0] executor_write_sp;

    logic executor_execute_valid;
    logic [OP_WIDTH-1:0] executor_execute_op;
    logic [WIDTH-1:0] executor_execute_a;
    logic [WIDTH-1:0] executor_execute_b;

    logic executor_stack_write_valid;
    logic executor_stack_read_valid;
    logic [WIDTH-1:0] executor_stack_access_sp;
    logic [RELATION_STACK_WIDTH-1:0] executor_stack_write_data;

    logic [WIDTH-1:0] executor_pc;
    logic [IR_WIDTH-1:0] executor_ir;
    logic [3:0] executor_state;

    logic executor_instruction_done;

    logic executor_print_valid;
    logic [3:0] executor_print_kind;
    logic [WIDTH-1:0] executor_print_data;

    logic executor_last_operation_valid;

    logic executor_last_exception_valid;
    logic [3:0] executor_last_exception_code;

    logic executor_last_state_valid;
    logic [3:0] executor_last_state_code;

    logic executor_stack_transport;
    logic executor_relation_absent;

    logic executor_restore_valid;
    logic [OP_WIDTH-1:0] executor_restore_op;

    logic [WIDTH-1:0] executor_restore_y;
    logic [WIDTH-1:0] executor_restore_ra;
    logic [WIDTH-1:0] executor_restore_rd;
    logic [WIDTH-1:0] executor_restore_r0;
    logic [WIDTH-1:0] executor_restore_t;

    logic executor_mem_request;
    logic executor_mem_write;
    logic [WIDTH-1:0] executor_mem_address;
    logic [WIDTH-1:0] executor_mem_write_data;

    // Kernel-facing signals after manual/executor arbitration.
    logic kernel_context_write;

    logic [WIDTH-1:0] kernel_write_pc;
    logic [IR_WIDTH-1:0] kernel_write_ir;
    logic [WIDTH-1:0] kernel_write_a;
    logic [WIDTH-1:0] kernel_write_b;
    logic [WIDTH-1:0] kernel_write_address;
    logic [WIDTH-1:0] kernel_write_flags;
    logic [WIDTH-1:0] kernel_write_sp;

    logic kernel_execute_valid;
    logic [OP_WIDTH-1:0] kernel_execute_op;
    logic [WIDTH-1:0] kernel_execute_a;
    logic [WIDTH-1:0] kernel_execute_b;

    logic kernel_stack_write_valid;
    logic kernel_stack_read_valid;
    logic [WIDTH-1:0] kernel_stack_access_sp;
    logic [RELATION_STACK_WIDTH-1:0] kernel_stack_write_data;

    logic kernel_restore_valid;
    logic [OP_WIDTH-1:0] kernel_restore_op;

    logic [WIDTH-1:0] kernel_restore_y;
    logic [WIDTH-1:0] kernel_restore_ra;
    logic [WIDTH-1:0] kernel_restore_rd;
    logic [WIDTH-1:0] kernel_restore_r0;
    logic [WIDTH-1:0] kernel_restore_t;

    logic kernel_restore_done;

    logic kernel_mem_request;
    logic kernel_mem_write;
    logic [MEM_ADDR_W-1:0] kernel_mem_address;
    logic [WIDTH-1:0] kernel_mem_write_data;

    //==================================================================
    // Kernel inputs
    //==================================================================

    logic babalawo_mode;

    logic create_valid;
    logic select_valid;
    logic pause_valid;
    logic resume_valid;
    logic destroy_valid;

    logic [YARA_W-1:0] command_yara;

    logic context_write;

    logic [WIDTH-1:0]    write_pc;
    logic [IR_WIDTH-1:0] write_ir;
    logic [WIDTH-1:0]    write_a;
    logic [WIDTH-1:0]    write_b;
    logic [WIDTH-1:0]    write_address;
    logic [WIDTH-1:0]    write_flags;
    logic [WIDTH-1:0]    write_sp;

    logic execute_valid;
    logic [OP_WIDTH-1:0] execute_op;
    logic [WIDTH-1:0] execute_a;
    logic [WIDTH-1:0] execute_b;

    logic stack_write_valid;
    logic stack_read_valid;
    logic [RELATION_STACK_WIDTH-1:0] stack_write_data;

    logic [RELATION_STACK_WIDTH-1:0] stack_read_data;
    logic stack_write_done;
    logic stack_read_done;
    logic stack_allowed;
    logic stack_denied;

    logic frame_grant_valid;
    logic frame_revoke_valid;

    logic [YARA_W-1:0] frame_admin_source;
    logic [YARA_W-1:0] frame_admin_destination;

    logic frame_share_request;

    logic [YARA_W-1:0] frame_share_source;
    logic [YARA_W-1:0] frame_share_destination;

    logic mem_request;
    logic mem_write;

    logic [MEM_ADDR_W-1:0] mem_address;
    logic [WIDTH-1:0] mem_write_data;

    logic mem_grant_read_valid;
    logic mem_grant_write_valid;
    logic mem_revoke_read_valid;
    logic mem_revoke_write_valid;

    logic [MEM_ADDR_W-1:0] mem_admin_address;
    logic [YARA_W-1:0] mem_admin_yara;

    //==================================================================
    // Kernel outputs
    //==================================================================

    logic [WIDTH-1:0] mem_read_data;
    logic mem_allowed;
    logic mem_denied;

    logic [YARA_W-1:0] active_yara;
    logic active_valid;
    logic active_running;

    logic [MAX_YARA-1:0] yara_valid;
    logic [MAX_YARA-1:0] yara_running;

    logic command_allowed;
    logic command_denied;

    logic [WIDTH-1:0] active_pc;
    logic [IR_WIDTH-1:0] active_ir;
    logic [WIDTH-1:0] active_a;
    logic [WIDTH-1:0] active_b;
    logic [WIDTH-1:0] active_address;
    logic [WIDTH-1:0] active_flags;
    logic [WIDTH-1:0] active_sp;

    logic rmu_hit;
    logic rmu_miss;

    logic [OP_WIDTH-1:0] out_op;

    logic [WIDTH-1:0] out_y;
    logic [WIDTH-1:0] out_ra;
    logic [WIDTH-1:0] out_rd;
    logic [WIDTH-1:0] out_r0;
    logic [WIDTH-1:0] out_t;

    logic operation_valid;

    logic exception_valid;
    logic [3:0] exception_code;

    logic state_valid;
    logic [3:0] state_code;

    logic eq_flag;
    logic gt_flag;
    logic lt_flag;

    logic frame_share_allowed;
    logic frame_share_denied;
    logic frame_share_done;

    logic [31:0] switch_count;
    logic [31:0] manager_denied_count;

    logic [31:0] frame_allowed_count;
    logic [31:0] frame_denied_count;

    logic [31:0] memory_read_count;
    logic [31:0] memory_write_count;
    logic [31:0] memory_denied_count;

    logic [31:0] yara0_hits;
    logic [31:0] yara0_misses;
    logic [31:0] yara0_imports;

    logic [31:0] yara1_hits;
    logic [31:0] yara1_misses;
    logic [31:0] yara1_imports;

    //==================================================================
    // Program executor instance
    //==================================================================

    ifa_program_executor_v45 #(
        .WIDTH      (WIDTH),
        .OP_WIDTH   (OP_WIDTH),
        .IR_WIDTH   (IR_WIDTH),
        .IMEM_DEPTH (IMEM_DEPTH),
        .IMEM_AW    (IMEM_AW)
    ) program_executor (
        .clk(clk),
        .rst(rst),

        .start(executor_start),
        .step(executor_step),
        .stop(executor_stop),

        .busy(executor_busy),
        .halted(executor_halted),
        .fault(executor_fault),

        .imem_write_valid(executor_imem_write_valid),
        .imem_write_address(executor_imem_write_address),
        .imem_write_data(executor_imem_write_data),

        .active_valid(active_valid),
        .active_running(active_running),

        .active_pc(active_pc),
        .active_ir(active_ir),
        .active_a(active_a),
        .active_b(active_b),
        .active_address(active_address),
        .active_flags(active_flags),
        .active_sp(active_sp),

        .context_write(executor_context_write),

        .write_pc(executor_write_pc),
        .write_ir(executor_write_ir),
        .write_a(executor_write_a),
        .write_b(executor_write_b),
        .write_address(executor_write_address),
        .write_flags(executor_write_flags),
        .write_sp(executor_write_sp),

        .stack_write_valid(executor_stack_write_valid),
        .stack_read_valid(executor_stack_read_valid),
        .stack_access_sp(executor_stack_access_sp),
        .stack_write_data(executor_stack_write_data),

        .stack_read_data(stack_read_data),
        .stack_write_done(stack_write_done),
        .stack_read_done(stack_read_done),
        .stack_allowed(stack_allowed),
        .stack_denied(stack_denied),

        .stack_transport(executor_stack_transport),
        .relation_absent(executor_relation_absent),

        .restore_valid(executor_restore_valid),
        .restore_op(executor_restore_op),

        .restore_y(executor_restore_y),
        .restore_ra(executor_restore_ra),
        .restore_rd(executor_restore_rd),
        .restore_r0(executor_restore_r0),
        .restore_t(executor_restore_t),

        .restore_done(kernel_restore_done),

        .execute_valid(executor_execute_valid),
        .execute_op(executor_execute_op),
        .execute_a(executor_execute_a),
        .execute_b(executor_execute_b),

        .operation_valid(operation_valid),

        .exception_valid(exception_valid),
        .exception_code(exception_code),

        .state_valid(state_valid),
        .state_code(state_code),

        .eq_flag(eq_flag),
        .gt_flag(gt_flag),
        .lt_flag(lt_flag),

        .active_frame_y(out_y),
        .active_frame_ra(out_ra),
        .active_frame_rd(out_rd),
        .active_frame_r0(out_r0),
        .active_frame_t(out_t),
        .active_frame_op(out_op),

        .mem_request(executor_mem_request),
        .mem_write(executor_mem_write),
        .mem_address(executor_mem_address),
        .mem_write_data(executor_mem_write_data),
        .mem_read_data(mem_read_data),
        .mem_allowed(mem_allowed),
        .mem_denied(mem_denied),

        .print_valid(executor_print_valid),
        .print_kind(executor_print_kind),
        .print_data(executor_print_data),

        .executor_pc(executor_pc),
        .executor_ir(executor_ir),
        .executor_state(executor_state),

        .instruction_done(executor_instruction_done),

        .last_operation_valid(executor_last_operation_valid),

        .last_exception_valid(executor_last_exception_valid),
        .last_exception_code(executor_last_exception_code),

        .last_state_valid(executor_last_state_valid),
        .last_state_code(executor_last_state_code)
    );

    //==================================================================
    // Manual-command / program-executor arbitration
    //
    // Manual CONTEXT and EXEC commands remain available while the
    // executor is idle. During program execution, the executor owns
    // context write-back and native dispatch.
    //==================================================================

    always_comb begin
        kernel_context_write = context_write;

        kernel_write_pc      = write_pc;
        kernel_write_ir      = write_ir;
        kernel_write_a       = write_a;
        kernel_write_b       = write_b;
        kernel_write_address = write_address;
        kernel_write_flags   = write_flags;
        kernel_write_sp      = write_sp;

        kernel_execute_valid = execute_valid;
        kernel_execute_op    = execute_op;
        kernel_execute_a     = execute_a;
        kernel_execute_b     = execute_b;

        kernel_stack_write_valid = stack_write_valid;
        kernel_stack_read_valid  = stack_read_valid;

        // Manual diagnostics use the active context SP.
        kernel_stack_access_sp   = active_sp;
        kernel_stack_write_data  = stack_write_data;

        kernel_restore_valid = 1'b0;
        kernel_restore_op    = {OP_WIDTH{1'b0}};

        kernel_restore_y  = {WIDTH{1'b0}};
        kernel_restore_ra = {WIDTH{1'b0}};
        kernel_restore_rd = {WIDTH{1'b0}};
        kernel_restore_r0 = {WIDTH{1'b0}};
        kernel_restore_t  = {WIDTH{1'b0}};

        kernel_mem_request = mem_request;
        kernel_mem_write = mem_write;
        kernel_mem_address = mem_address;
        kernel_mem_write_data = mem_write_data;

        if (executor_busy) begin
            kernel_context_write = executor_context_write;

            kernel_write_pc      = executor_write_pc;
            kernel_write_ir      = executor_write_ir;
            kernel_write_a       = executor_write_a;
            kernel_write_b       = executor_write_b;
            kernel_write_address = executor_write_address;
            kernel_write_flags   = executor_write_flags;
            kernel_write_sp      = executor_write_sp;

            kernel_execute_valid = executor_execute_valid;
            kernel_execute_op    = executor_execute_op;
            kernel_execute_a     = executor_execute_a;
            kernel_execute_b     = executor_execute_b;

            kernel_stack_write_valid =
                executor_stack_write_valid;

            kernel_stack_read_valid =
                executor_stack_read_valid;

            kernel_stack_access_sp =
                executor_stack_access_sp;

            kernel_stack_write_data =
                executor_stack_write_data;

            kernel_restore_valid =
                executor_restore_valid;

            kernel_restore_op =
                executor_restore_op;

            kernel_restore_y =
                executor_restore_y;

            kernel_restore_ra =
                executor_restore_ra;

            kernel_restore_rd =
                executor_restore_rd;

            kernel_restore_r0 =
                executor_restore_r0;

            kernel_restore_t =
                executor_restore_t;

            kernel_mem_request = executor_mem_request;
            kernel_mem_write = executor_mem_write;
            kernel_mem_address =
                executor_mem_address[MEM_ADDR_W-1:0];
            kernel_mem_write_data = executor_mem_write_data;
        end
    end

    //==================================================================
    // Kernel instance
    //==================================================================

    ifa_onile_kernel_v45 #(
        .WIDTH      (WIDTH),
        .OP_WIDTH   (OP_WIDTH),
        .IR_WIDTH   (IR_WIDTH),
        .RMU_DEPTH  (RMU_DEPTH),
        .MEM_ADDR_W (MEM_ADDR_W),
        .MAX_YARA   (MAX_YARA)
    ) dut (
        .clk(clk),
        .rst(rst),

        .babalawo_mode(babalawo_mode),

        .create_valid(create_valid),
        .select_valid(select_valid),
        .pause_valid(pause_valid),
        .resume_valid(resume_valid),
        .destroy_valid(destroy_valid),

        .command_yara(command_yara),

        .context_write(kernel_context_write),

        .write_pc(kernel_write_pc),
        .write_ir(kernel_write_ir),
        .write_a(kernel_write_a),
        .write_b(kernel_write_b),
        .write_address(kernel_write_address),
        .write_flags(kernel_write_flags),
        .write_sp(kernel_write_sp),

        .stack_write_valid(kernel_stack_write_valid),
        .stack_read_valid(kernel_stack_read_valid),
        .stack_access_sp(kernel_stack_access_sp),
        .stack_write_data(kernel_stack_write_data),

        .stack_read_data(stack_read_data),
        .stack_write_done(stack_write_done),
        .stack_read_done(stack_read_done),
        .stack_allowed(stack_allowed),
        .stack_denied(stack_denied),

        .execute_valid(kernel_execute_valid),
        .execute_op(kernel_execute_op),
        .execute_a(kernel_execute_a),
        .execute_b(kernel_execute_b),

        .frame_grant_valid(frame_grant_valid),
        .frame_revoke_valid(frame_revoke_valid),

        .frame_admin_source(frame_admin_source),
        .frame_admin_destination(frame_admin_destination),

        .frame_share_request(frame_share_request),
        .frame_share_source(frame_share_source),
        .frame_share_destination(frame_share_destination),

        .restore_valid(kernel_restore_valid),
        .restore_op(kernel_restore_op),

        .restore_y(kernel_restore_y),
        .restore_ra(kernel_restore_ra),
        .restore_rd(kernel_restore_rd),
        .restore_r0(kernel_restore_r0),
        .restore_t(kernel_restore_t),

        .restore_done(kernel_restore_done),

        .mem_request(kernel_mem_request),
        .mem_write(kernel_mem_write),
        .mem_address(kernel_mem_address),
        .mem_write_data(kernel_mem_write_data),

        .mem_read_data(mem_read_data),
        .mem_allowed(mem_allowed),
        .mem_denied(mem_denied),

        .mem_grant_read_valid(mem_grant_read_valid),
        .mem_grant_write_valid(mem_grant_write_valid),
        .mem_revoke_read_valid(mem_revoke_read_valid),
        .mem_revoke_write_valid(mem_revoke_write_valid),

        .mem_admin_address(mem_admin_address),
        .mem_admin_yara(mem_admin_yara),

        .active_yara(active_yara),
        .active_valid(active_valid),
        .active_running(active_running),

        .yara_valid(yara_valid),
        .yara_running(yara_running),

        .command_allowed(command_allowed),
        .command_denied(command_denied),

        .active_pc(active_pc),
        .active_ir(active_ir),
        .active_a(active_a),
        .active_b(active_b),
        .active_address(active_address),
        .active_flags(active_flags),
        .active_sp(active_sp),

        .rmu_hit(rmu_hit),
        .rmu_miss(rmu_miss),

        .out_op(out_op),

        .out_y(out_y),
        .out_ra(out_ra),
        .out_rd(out_rd),
        .out_r0(out_r0),
        .out_t(out_t),

        .operation_valid(operation_valid),

        .exception_valid(exception_valid),
        .exception_code(exception_code),

        .state_valid(state_valid),
        .state_code(state_code),

        .eq_flag(eq_flag),
        .gt_flag(gt_flag),
        .lt_flag(lt_flag),

        .frame_share_allowed(frame_share_allowed),
        .frame_share_denied(frame_share_denied),
        .frame_share_done(frame_share_done),

        .switch_count(switch_count),
        .manager_denied_count(manager_denied_count),

        .frame_allowed_count(frame_allowed_count),
        .frame_denied_count(frame_denied_count),

        .memory_read_count(memory_read_count),
        .memory_write_count(memory_write_count),
        .memory_denied_count(memory_denied_count),

        .yara0_hits(yara0_hits),
        .yara0_misses(yara0_misses),
        .yara0_imports(yara0_imports),

        .yara1_hits(yara1_hits),
        .yara1_misses(yara1_misses),
        .yara1_imports(yara1_imports)
    );

    //==================================================================
    // Clear all one-cycle control signals
    //==================================================================

    task automatic clear_control_signals;
    begin
        create_valid  = 1'b0;
        select_valid  = 1'b0;
        pause_valid   = 1'b0;
        resume_valid  = 1'b0;
        destroy_valid = 1'b0;

        context_write = 1'b0;
        execute_valid = 1'b0;

        stack_write_valid = 1'b0;
        stack_read_valid  = 1'b0;
        stack_write_data  = '0;

        executor_start = 1'b0;
        executor_step  = 1'b0;
        executor_stop  = 1'b0;

        executor_imem_write_valid = 1'b0;

        frame_grant_valid  = 1'b0;
        frame_revoke_valid = 1'b0;
        frame_share_request = 1'b0;

        mem_request = 1'b0;

        mem_grant_read_valid   = 1'b0;
        mem_grant_write_valid  = 1'b0;
        mem_revoke_read_valid  = 1'b0;
        mem_revoke_write_valid = 1'b0;
    end
    endtask

    //==================================================================
    // Lifecycle command
    //==================================================================

    task automatic issue_lifecycle(
        input integer operation,
        input integer room
    );
    begin
        // Reject invalid IDs before narrowing to YARA_W bits.
        if (room < 0 || room >= MAX_YARA) begin
            case (operation)
                0: $display("DENY CREATE ID=%0d", room);
                1: $display("DENY SELECT ID=%0d", room);
                2: $display("DENY PAUSE ID=%0d", room);
                3: $display("DENY RESUME ID=%0d", room);
                4: $display("DENY DESTROY ID=%0d", room);
                default:
                    $display(
                        "DENY LIFECYCLE UNKNOWN_OPERATION=%0d ID=%0d",
                        operation,
                        room
                    );
            endcase
        end else begin
            @(negedge clk);

            command_yara = room[YARA_W-1:0];

            case (operation)
                0: create_valid  = 1'b1;
                1: select_valid  = 1'b1;
                2: pause_valid   = 1'b1;
                3: resume_valid  = 1'b1;
                4: destroy_valid = 1'b1;
                default: begin
                end
            endcase

            @(posedge clk);
            #1;

            case (operation)
                0: begin
                    if (command_allowed)
                        $display("OK CREATE ID=%0d", room);
                    else
                        $display("DENY CREATE ID=%0d", room);
                end

                1: begin
                    if (command_allowed)
                        $display("OK SELECT ID=%0d", room);
                    else
                        $display("DENY SELECT ID=%0d", room);
                end

                2: begin
                    if (command_allowed)
                        $display("OK PAUSE ID=%0d", room);
                    else
                        $display("DENY PAUSE ID=%0d", room);
                end

                3: begin
                    if (command_allowed)
                        $display("OK RESUME ID=%0d", room);
                    else
                        $display("DENY RESUME ID=%0d", room);
                end

                4: begin
                    if (command_allowed)
                        $display("OK DESTROY ID=%0d", room);
                    else
                        $display("DENY DESTROY ID=%0d", room);
                end
            endcase

            @(negedge clk);
            clear_control_signals();
        end
    end
    endtask

    //==================================================================
    // Context write command
    //==================================================================

    task automatic issue_context(
        input integer pc_value,
        input integer ir_value,
        input integer a_value,
        input integer b_value,
        input integer address_value,
        input integer flags_value,
        input integer sp_value
    );
    begin
        @(negedge clk);

        write_pc      = pc_value[WIDTH-1:0];
        write_ir      = ir_value[IR_WIDTH-1:0];
        write_a       = a_value[WIDTH-1:0];
        write_b       = b_value[WIDTH-1:0];
        write_address = address_value[WIDTH-1:0];
        write_flags   = flags_value[WIDTH-1:0];
        write_sp      = sp_value[WIDTH-1:0];

        context_write = 1'b1;

        @(posedge clk);
        #1;

        if (active_valid && active_running) begin
            $display(
                "OK CONTEXT ID=%0d PC=%02h IR=%04h A=%02h B=%02h ADDR=%02h FLAGS=%02h SP=%02h",
                active_yara,
                write_pc,
                write_ir,
                write_a,
                write_b,
                write_address,
                write_flags,
                write_sp
            );
        end else begin
            $display("DENY CONTEXT NO_ACTIVE_YARA");
        end

        @(negedge clk);
        clear_control_signals();
    end
    endtask


    //==================================================================
    // Manual Stack Commands
    // V4.4.10
    //==================================================================

    task automatic issue_stack_write(
        input integer value
    );
    begin
        @(negedge clk);

        stack_write_data = {
            RELATION_STACK_WIDTH{1'b0}
        };

        stack_write_data[WIDTH-1:0] =
            value[WIDTH-1:0];

        stack_write_valid = 1'b1;

        @(posedge clk);
        #1;

        if (stack_write_done && stack_allowed)
            $display(
                "OK STACKWRITE SP=%02h DATA=%02h",
                active_sp,
                stack_write_data[WIDTH-1:0]
            );
        else
            $display("DENY STACKWRITE");

        @(negedge clk);

        stack_write_valid = 1'b0;
    end
    endtask


    task automatic issue_stack_read;
    begin
        @(negedge clk);

        stack_read_valid = 1'b1;

        @(posedge clk);
        #1;

        if (stack_read_done && stack_allowed)
            $display(
                "OK STACKREAD SP=%02h DATA=%02h",
                active_sp,
                stack_read_data[WIDTH-1:0]
            );
        else
            $display("DENY STACKREAD");

        @(negedge clk);

        stack_read_valid = 1'b0;
    end
    endtask

    //==================================================================
    // Relation execution
    //==================================================================

    task automatic issue_execute(
        input logic [OP_WIDTH-1:0] operation,
        input integer a_value,
        input integer b_value
    );
    begin
        @(negedge clk);

        execute_op = operation;
        execute_a = a_value[WIDTH-1:0];
        execute_b = b_value[WIDTH-1:0];
        execute_valid = 1'b1;

        @(posedge clk);
        #1;

        if (!active_valid) begin
            $display("DENY EXEC NO_ACTIVE_YARA");
        end else if (!active_running) begin
            $display(
                "DENY EXEC YARA_PAUSED ID=%0d",
                active_yara
            );
        end else begin
            $display(
                "EXEC ID=%0d OP=%0h HIT=%0d MISS=%0d Y=%02h RA=%02h RD=%02h R0=%02h T=%02h VALID=%0d EXC=%0d EXC_CODE=%0h STATE=%0d STATE_CODE=%0h EQ=%0d GT=%0d LT=%0d",
                active_yara,
                out_op,
                rmu_hit,
                rmu_miss,
                out_y,
                out_ra,
                out_rd,
                out_r0,
                out_t,
                operation_valid,
                exception_valid,
                exception_code,
                state_valid,
                state_code,
                eq_flag,
                gt_flag,
                lt_flag
            );
        end

        @(negedge clk);
        clear_control_signals();
    end
    endtask

    //==================================================================
    // Frame permission administration
    //==================================================================

    task automatic issue_frame_permission(
        input integer do_grant,
        input integer src,
        input integer dst
    );
    begin
        // Frame permissions are cross-YÀRÁ only.
        // Reject invalid and self-directed requests before narrowing.
        if (
            src < 0
            || src >= MAX_YARA
            || dst < 0
            || dst >= MAX_YARA
            || src == dst
        ) begin
            if (do_grant)
                $display(
                    "DENY GRANT SRC=%0d DST=%0d",
                    src,
                    dst
                );
            else
                $display(
                    "DENY REVOKE SRC=%0d DST=%0d",
                    src,
                    dst
                );
        end else if (!babalawo_mode) begin
            if (do_grant)
                $display(
                    "DENY GRANT SRC=%0d DST=%0d",
                    src,
                    dst
                );
            else
                $display(
                    "DENY REVOKE SRC=%0d DST=%0d",
                    src,
                    dst
                );
        end else begin
            @(negedge clk);

            frame_admin_source =
                src[YARA_W-1:0];

            frame_admin_destination =
                dst[YARA_W-1:0];

            if (do_grant)
                frame_grant_valid = 1'b1;
            else
                frame_revoke_valid = 1'b1;

            @(posedge clk);
            #1;

            if (do_grant)
                $display(
                    "OK GRANT SRC=%0d DST=%0d",
                    src,
                    dst
                );
            else
                $display(
                    "OK REVOKE SRC=%0d DST=%0d",
                    src,
                    dst
                );

            @(negedge clk);
            clear_control_signals();
        end
    end
    endtask

    //==================================================================
    // Frame delegation
    //==================================================================

    task automatic issue_share(
        input integer src,
        input integer dst
    );
    begin
        // SHARE means cross-YÀRÁ delegation only.
        if (
            src < 0
            || src >= MAX_YARA
            || dst < 0
            || dst >= MAX_YARA
            || src == dst
        ) begin
            $display(
                "DENY SHARE SRC=%0d DST=%0d",
                src,
                dst
            );
        end else begin
            @(negedge clk);

            frame_share_source =
                src[YARA_W-1:0];

            frame_share_destination =
                dst[YARA_W-1:0];

            frame_share_request = 1'b1;

            #1;

            if (frame_share_denied) begin
                $display(
                    "DENY SHARE SRC=%0d DST=%0d",
                    src,
                    dst
                );
            end

            @(posedge clk);
            #1;

            if (
                frame_share_allowed
                && frame_share_done
            ) begin
                $display(
                    "OK SHARE SRC=%0d DST=%0d",
                    src,
                    dst
                );
            end

            @(negedge clk);
            clear_control_signals();
        end
    end
    endtask

    //==================================================================
    // General Memory read/write
    //==================================================================

    task automatic issue_memory(
        input integer do_write,
        input integer address_value,
        input integer data_value
    );
    begin
        @(negedge clk);

        mem_write =
            do_write;

        mem_address =
            address_value[MEM_ADDR_W-1:0];

        mem_write_data =
            data_value[WIDTH-1:0];

        mem_request = 1'b1;

        @(posedge clk);
        #1;

        if (mem_allowed) begin
            if (do_write) begin
                $display(
                    "OK MEMWRITE ID=%0d ADDR=%0h DATA=%02h",
                    active_yara,
                    mem_address,
                    mem_write_data
                );
            end else begin
                $display(
                    "OK MEMREAD ID=%0d ADDR=%0h DATA=%02h",
                    active_yara,
                    mem_address,
                    mem_read_data
                );
            end
        end else begin
            if (do_write) begin
                $display(
                    "DENY MEMWRITE ID=%0d ADDR=%0h",
                    active_yara,
                    mem_address
                );
            end else begin
                $display(
                    "DENY MEMREAD ID=%0d ADDR=%0h",
                    active_yara,
                    mem_address
                );
            end
        end

        @(negedge clk);
        clear_control_signals();
    end
    endtask

    //==================================================================
    // General Memory permission administration
    //==================================================================

    task automatic issue_memory_permission(
        input integer operation,
        input integer address_value,
        input integer yara_value
    );
    begin
        @(negedge clk);

        mem_admin_address =
            address_value[MEM_ADDR_W-1:0];

        mem_admin_yara =
            yara_value[YARA_W-1:0];

        case (operation)
            0: mem_grant_read_valid   = 1'b1;
            1: mem_grant_write_valid  = 1'b1;
            2: mem_revoke_read_valid  = 1'b1;
            3: mem_revoke_write_valid = 1'b1;
            default: begin
            end
        endcase

        @(posedge clk);
        #1;

        if (!babalawo_mode) begin
            $display(
                "DENY MEMPERM OP=%0d ADDR=%0h ID=%0d",
                operation,
                address_value,
                yara_value
            );
        end else begin
            $display(
                "OK MEMPERM OP=%0d ADDR=%0h ID=%0d",
                operation,
                address_value,
                yara_value
            );
        end

        @(negedge clk);
        clear_control_signals();
    end
    endtask

    //==================================================================
    // Status
    //==================================================================

    task automatic print_status;
    begin
        $display("STATUS BEGIN");
        $display("MAX_YARA=%0d", MAX_YARA);
        $display("BABALAWO=%0d", babalawo_mode);
        $display("ACTIVE_ID=%0d", active_yara);
        $display("ACTIVE_VALID=%0d", active_valid);
        $display("ACTIVE_RUNNING=%0d", active_running);
        $display("VALID_MASK=%h", yara_valid);
        $display("RUNNING_MASK=%h", yara_running);

        $display(
            "CONTEXT PC=%02h IR=%04h A=%02h B=%02h ADDR=%02h FLAGS=%02h SP=%02h",
            active_pc,
            active_ir,
            active_a,
            active_b,
            active_address,
            active_flags,
            active_sp
        );

        $display(
            "FRAME OP=%0h Y=%02h RA=%02h RD=%02h R0=%02h T=%02h HIT=%0d MISS=%0d",
            out_op,
            out_y,
            out_ra,
            out_rd,
            out_r0,
            out_t,
            rmu_hit,
            rmu_miss
        );

        $display(
            "EXECUTOR BUSY=%0d HALTED=%0d FAULT=%0d STATE=%0h PC=%02h IR=%04h INSTRUCTION_DONE=%0d",
            executor_busy,
            executor_halted,
            executor_fault,
            executor_state,
            executor_pc,
            executor_ir,
            executor_instruction_done
        );

        $display(
            "STACK TRANSPORT=%0d RELATION_ABSENT=%0d",
            executor_stack_transport,
            executor_relation_absent
        );

        $display(
            "STATS SWITCH=%0d MANAGER_DENIED=%0d FRAME_ALLOWED=%0d FRAME_DENIED=%0d MEM_READ=%0d MEM_WRITE=%0d MEM_DENIED=%0d",
            switch_count,
            manager_denied_count,
            frame_allowed_count,
            frame_denied_count,
            memory_read_count,
            memory_write_count,
            memory_denied_count
        );

        $display("STATUS END");
    end
    endtask

    //==================================================================
    // Program-memory instruction loader
    //
    // Command:
    //
    //     LOAD <8-bit address> <16-bit instruction>
    //==================================================================

    task automatic issue_program_load(
        input integer instruction_address,
        input integer instruction_word
    );
    begin
        if (executor_busy) begin
            $display(
                "DENY LOAD EXECUTOR_BUSY"
            );
        end else begin
            @(negedge clk);

            executor_imem_write_address =
                instruction_address[IMEM_AW-1:0];

            executor_imem_write_data =
                instruction_word[IR_WIDTH-1:0];

            executor_imem_write_valid = 1'b1;

            @(posedge clk);
            #1;

            $display(
                "OK LOAD ADDR=%02h IR=%04h",
                executor_imem_write_address,
                executor_imem_write_data
            );

            @(negedge clk);
            executor_imem_write_valid = 1'b0;
        end
    end
    endtask


    //==================================================================
    // Program execution
    //==================================================================

    task automatic issue_program_run;
        integer cycle_guard;

        logic run_hit_seen;
        logic run_miss_seen;
        integer run_hit_count;
        integer run_miss_count;

        logic [OP_WIDTH-1:0] run_out_op;

        logic [WIDTH-1:0] run_out_y;
        logic [WIDTH-1:0] run_out_ra;
        logic [WIDTH-1:0] run_out_rd;
        logic [WIDTH-1:0] run_out_r0;
        logic [WIDTH-1:0] run_out_t;

        logic run_operation_valid;

        logic run_exception_valid;
        logic [3:0] run_exception_code;

        logic run_state_valid;
        logic [3:0] run_state_code;

        logic run_eq;
        logic run_gt;
        logic run_lt;
    begin
        if (!active_valid) begin
            $display(
                "DENY RUN NO_ACTIVE_YARA"
            );
        end else if (!active_running) begin
            $display(
                "DENY RUN YARA_PAUSED ID=%0d",
                active_yara
            );
        end else if (executor_busy) begin
            $display(
                "DENY RUN EXECUTOR_BUSY"
            );
        end else begin
            run_hit_seen  = 1'b0;
            run_miss_seen = 1'b0;
            run_hit_count = 0;
            run_miss_count = 0;

            run_out_op = {OP_WIDTH{1'b0}};

            run_out_y  = {WIDTH{1'b0}};
            run_out_ra = {WIDTH{1'b0}};
            run_out_rd = {WIDTH{1'b0}};
            run_out_r0 = {WIDTH{1'b0}};
            run_out_t  = {WIDTH{1'b0}};

            run_operation_valid = 1'b0;

            run_exception_valid = 1'b0;
            run_exception_code  = 4'h0;

            run_state_valid = 1'b0;
            run_state_code  = 4'h0;

            run_eq = 1'b0;
            run_gt = 1'b0;
            run_lt = 1'b0;

            @(negedge clk);
            executor_start = 1'b1;

            @(posedge clk);
            #1;

            @(negedge clk);
            executor_start = 1'b0;

            cycle_guard = 0;

            while (
                !executor_halted
                && !executor_fault
                && cycle_guard < 2000000
            ) begin
                @(posedge clk);
                #1;

                if (rmu_hit) begin
                    run_hit_seen = 1'b1;
                    run_hit_count = run_hit_count + 1;
                end

                if (rmu_miss) begin
                    run_miss_seen = 1'b1;
                    run_miss_count = run_miss_count + 1;
                end

                // Native status is a one-cycle pulse. Accumulate it
                // independently so a later zero cycle cannot erase it.
                if (operation_valid) begin
                    run_operation_valid = 1'b1;

                    run_eq = eq_flag;
                    run_gt = gt_flag;
                    run_lt = lt_flag;
                end

                if (exception_valid) begin
                    run_exception_valid = 1'b1;
                    run_exception_code  = exception_code;
                end

                if (state_valid) begin
                    run_state_valid = 1'b1;
                    run_state_code  = state_code;
                end

                // The complete operation-aware frame is committed when
                // the selected local RMU reports HIT or MISS.
                if (rmu_hit || rmu_miss) begin
                    run_out_op = out_op;

                    run_out_y  = out_y;
                    run_out_ra = out_ra;
                    run_out_rd = out_rd;
                    run_out_r0 = out_r0;
                    run_out_t  = out_t;
                end

                cycle_guard = cycle_guard + 1;
            end

            if (executor_fault) begin
                $display(
                    "FAULT RUN ID=%0d PC=%02h IR=%04h STATE=%0h",
                    active_yara,
                    active_pc,
                    executor_ir,
                    executor_state
                );
            end else if (!executor_halted) begin
                $display(
                    "FAULT RUN TIMEOUT ID=%0d PC=%02h",
                    active_yara,
                    active_pc
                );
            end else begin
                $display(
                    "OK RUN ID=%0d PC=%02h IR=%04h A=%02h B=%02h ADDR=%02h FLAGS=%02h HIT=%0d MISS=%0d OP=%0h Y=%02h RA=%02h RD=%02h R0=%02h T=%02h VALID=%0d EXC=%0d EXC_CODE=%0h STATE=%0d STATE_CODE=%0h EQ=%0d GT=%0d LT=%0d CYCLES=%0d RMU_HITS=%0d RMU_MISSES=%0d",
                    active_yara,
                    active_pc,
                    active_ir,
                    active_a,
                    active_b,
                    active_address,
                    active_flags,
                    run_hit_seen,
                    run_miss_seen,
                    run_out_op,
                    run_out_y,
                    run_out_ra,
                    run_out_rd,
                    run_out_r0,
                    run_out_t,
                    executor_last_operation_valid,
                    executor_last_exception_valid,
                    executor_last_exception_code,
                    executor_last_state_valid,
                    executor_last_state_code,
                    active_flags[2],
                    active_flags[1],
                    active_flags[0],
                    cycle_guard,
                    run_hit_count,
                    run_miss_count
                );
            end
        end
    end
    endtask


    //==================================================================
    // Single-instruction program step
    //==================================================================

    task automatic issue_program_step;
        integer cycle_guard;
    begin
        if (!active_valid) begin
            $display(
                "DENY STEP NO_ACTIVE_YARA"
            );
        end else if (!active_running) begin
            $display(
                "DENY STEP YARA_PAUSED ID=%0d",
                active_yara
            );
        end else if (executor_busy) begin
            $display(
                "DENY STEP EXECUTOR_BUSY"
            );
        end else begin
            @(negedge clk);
            executor_step = 1'b1;

            @(posedge clk);
            #1;

            @(negedge clk);
            executor_step = 1'b0;

            cycle_guard = 0;

            while (
                !executor_instruction_done
                && !executor_halted
                && !executor_fault
                && cycle_guard < 256
            ) begin
                @(posedge clk);
                #1;
                cycle_guard = cycle_guard + 1;
            end

            if (executor_fault) begin
                $display(
                    "FAULT STEP ID=%0d PC=%02h IR=%04h STATE=%0h",
                    active_yara,
                    active_pc,
                    executor_ir,
                    executor_state
                );
            end else if (
                !executor_instruction_done
                && !executor_halted
            ) begin
                $display(
                    "FAULT STEP TIMEOUT ID=%0d PC=%02h",
                    active_yara,
                    active_pc
                );
            end else begin
                $display(
                    "OK STEP ID=%0d PC=%02h IR=%04h A=%02h B=%02h ADDR=%02h FLAGS=%02h HALTED=%0d",
                    active_yara,
                    active_pc,
                    active_ir,
                    active_a,
                    active_b,
                    active_address,
                    active_flags,
                    executor_halted
                );
            end
        end
    end
    endtask


    //==================================================================
    // Program stop
    //==================================================================

    task automatic issue_program_stop;
    begin
        @(negedge clk);
        executor_stop = 1'b1;

        @(posedge clk);
        #1;

        @(negedge clk);
        executor_stop = 1'b0;

        $display(
            "OK STOP ID=%0d PC=%02h HALTED=%0d FAULT=%0d STATE=%0h",
            active_yara,
            active_pc,
            executor_halted,
            executor_fault,
            executor_state
        );
    end
    endtask


    //==================================================================
    // Program-controlled output
    //==================================================================

    always_ff @(posedge clk) begin
        if (!rst && executor_print_valid) begin
            $display(
                "PRINT KIND=%0h DATA=%02h",
                executor_print_kind,
                executor_print_data
            );
        end
    end


    //==================================================================
    // Command parser
    //==================================================================

    integer command_file;
    integer read_status;
    integer parsed;
    integer interactive_mode;

    integer arg0;
    integer arg1;
    integer arg2;
    integer arg3;
    integer arg4;
    integer arg5;
    integer arg6;

    // Keep the packed string below Verilator's 64-word value limit.  The
    // bridge commands are bounded, so 256 bytes leaves ample input space
    // while remaining portable across Icarus and Verilator.
    reg [8*512-1:0] command_line;
    reg [8*32-1:0] command_word;
    reg [8*32-1:0] mode_word;
    reg [8*32-1:0] arg_word;
    reg [8*256-1:0] command_file_name;

    initial begin
        clk = 1'b0;
        rst = 1'b1;

        babalawo_mode = 1'b0;

        command_yara = '0;

        write_pc      = '0;
        write_ir      = '0;
        write_a       = '0;
        write_b       = '0;
        write_address = '0;
        write_flags   = '0;
        write_sp      = '0;

        execute_op = OP_PAPO;
        execute_a = '0;
        execute_b = '0;

        executor_start = 1'b0;
        executor_step  = 1'b0;
        executor_stop  = 1'b0;

        executor_imem_write_valid   = 1'b0;
        executor_imem_write_address = '0;
        executor_imem_write_data    = '0;

        frame_admin_source      = '0;
        frame_admin_destination = '0;

        frame_share_source      = '0;
        frame_share_destination = '0;

        mem_write      = 1'b0;
        mem_address    = '0;
        mem_write_data = '0;

        mem_admin_address = '0;
        mem_admin_yara    = '0;

        clear_control_signals();

        repeat (3) @(negedge clk);

        rst = 1'b0;

        interactive_mode = $test$plusargs(
            "INTERACTIVE"
        );

        if (interactive_mode) begin
            command_file = 32'h8000_0000;
        end else begin
            if (!$value$plusargs(
                "CMD_FILE=%s",
                command_file_name
            )) begin
                $display(
                    "ERROR: use +CMD_FILE=<command-file> or +INTERACTIVE"
                );
                $finish;
            end

            command_file =
                $fopen(command_file_name, "r");

            if (command_file == 0) begin
                $display(
                    "ERROR: cannot open command file %0s",
                    command_file_name
                );
                $finish;
            end
        end

        $display("IFA_V4_OS_BRIDGE READY");
        $fflush(32'h8000_0001);

        while (
            interactive_mode
            || !$feof(command_file)
        ) begin
            command_line = '0;
            command_word = '0;
            mode_word    = '0;

            arg0 = 0;
            arg1 = 0;
            arg2 = 0;
            arg3 = 0;
            arg4 = 0;
            arg5 = 0;

            read_status =
                $fgets(command_line, command_file);

            if (read_status != 0) begin
                parsed = $sscanf(
                    command_line,
                    "%s",
                    command_word
                );

                if (parsed == 1) begin
                    //--------------------------------------------------
                    // Comments and blank lines
                    //--------------------------------------------------

                    if (
                        command_word[8*32-1 -: 8] == "#"
                    ) begin
                        // Ignore comment.
                    end

                    //--------------------------------------------------
                    // Babaláwo privilege
                    //--------------------------------------------------

                    else if (command_word == "BABALAWO") begin
                        parsed = $sscanf(
                            command_line,
                            "%s %s",
                            command_word,
                            mode_word
                        );

                        if (mode_word == "ON") begin
                            babalawo_mode = 1'b1;
                            $display("OK BABALAWO ON");
                        end else if (mode_word == "OFF") begin
                            babalawo_mode = 1'b0;
                            $display("OK BABALAWO OFF");
                        end else begin
                            $display(
                                "ERROR BABALAWO EXPECTED_ON_OR_OFF"
                            );
                        end
                    end

                    //--------------------------------------------------
                    // Lifecycle
                    //--------------------------------------------------

                    else if (command_word == "CREATE") begin
                        parsed = $sscanf(
                            command_line,
                            "%s %d",
                            command_word,
                            arg0
                        );

                        issue_lifecycle(0, arg0);
                    end

                    else if (command_word == "SELECT") begin
                        parsed = $sscanf(
                            command_line,
                            "%s %d",
                            command_word,
                            arg0
                        );

                        issue_lifecycle(1, arg0);
                    end

                    else if (command_word == "PAUSE") begin
                        parsed = $sscanf(
                            command_line,
                            "%s %d",
                            command_word,
                            arg0
                        );

                        issue_lifecycle(2, arg0);
                    end

                    else if (command_word == "RESUME") begin
                        parsed = $sscanf(
                            command_line,
                            "%s %d",
                            command_word,
                            arg0
                        );

                        issue_lifecycle(3, arg0);
                    end

                    else if (command_word == "DESTROY") begin
                        parsed = $sscanf(
                            command_line,
                            "%s %d",
                            command_word,
                            arg0
                        );

                        issue_lifecycle(4, arg0);
                    end

                    //--------------------------------------------------
                    // Manual stack commands
                    // V4.4.10
                    //--------------------------------------------------

                    else if (command_word == "STACKWRITE") begin
                        parsed = $sscanf(
                            command_line,
                            "%s %h",
                            command_word,
                            arg0
                        );

                        if (parsed == 2) begin
                            issue_stack_write(arg0);
                        end else begin
                            $display(
                                "ERROR STACKWRITE EXPECTED_1_VALUE"
                            );
                        end
                    end

                    else if (command_word == "STACKREAD") begin
                        parsed = $sscanf(
                            command_line,
                            "%s",
                            command_word
                        );

                        issue_stack_read();
                    end

                    //--------------------------------------------------
                    // Context
                    //--------------------------------------------------

                    else if (command_word == "CONTEXT") begin
                        parsed = $sscanf(
                            command_line,
                            "%s %h %h %h %h %h %h %h",
                            command_word,
                            arg0,
                            arg1,
                            arg2,
                            arg3,
                            arg4,
                            arg5,
                            arg6
                        );

                        if (parsed == 8) begin
                            issue_context(
                                arg0,
                                arg1,
                                arg2,
                                arg3,
                                arg4,
                                arg5,
                                arg6
                            );
                        end else begin
                            $display(
                                "ERROR CONTEXT EXPECTED_7_VALUES"
                            );
                        end
                    end

                    //--------------------------------------------------
                    // Program execution
                    //--------------------------------------------------

                    else if (command_word == "RUN") begin
                        issue_program_run();
                    end

                    else if (command_word == "STEP") begin
                        issue_program_step();
                    end

                    else if (command_word == "STOP") begin
                        issue_program_stop();
                    end

                    //--------------------------------------------------
                    // Program-memory loading
                    //--------------------------------------------------

                    else if (command_word == "LOAD") begin
                        parsed = $sscanf(
                            command_line,
                            "%s %h %h",
                            command_word,
                            arg0,
                            arg1
                        );

                        if (parsed == 3) begin
                            issue_program_load(
                                arg0,
                                arg1
                            );
                        end else begin
                            $display(
                                "ERROR LOAD EXPECTED_ADDRESS_INSTRUCTION"
                            );
                        end
                    end

                    //--------------------------------------------------
                    // Execution
                    //--------------------------------------------------

                    else if (command_word == "EXEC") begin
                        parsed = $sscanf(
                            command_line,
                            "%s %s %h %h",
                            command_word,
                            arg_word,
                            arg0,
                            arg1
                        );

                        if (parsed == 4) begin
                            if (arg_word == "PAPO")
                                issue_execute(OP_PAPO, arg0, arg1);
                            else if (arg_word == "YO")
                                issue_execute(OP_YO, arg0, arg1);
                            else if (arg_word == "DAGBA")
                                issue_execute(OP_DAGBA, arg0, arg1);
                            else if (arg_word == "PIN")
                                issue_execute(OP_PIN, arg0, arg1);
                            else if (arg_word == "KU")
                                issue_execute(OP_KU, arg0, arg1);
                            else if (arg_word == "GBE")
                                issue_execute(OP_GBE, arg0, arg1);
                            else if (arg_word == "SEDA")
                                issue_execute(OP_SEDA, arg0, arg1);
                            else if (arg_word == "JU")
                                issue_execute(OP_JU, arg0, arg1);
                            else if (arg_word == "KERE")
                                issue_execute(OP_KERE, arg0, arg1);
                            else
                                $display(
                                    "ERROR EXEC UNKNOWN_OP=%s",
                                    arg_word
                                );
                        end else begin
                            $display(
                                "ERROR EXEC EXPECTED_OP_A_B"
                            );
                        end
                    end

                    //--------------------------------------------------
                    // Frame permissions and sharing
                    //--------------------------------------------------

                    else if (command_word == "GRANT") begin
                        parsed = $sscanf(
                            command_line,
                            "%s %d %d",
                            command_word,
                            arg0,
                            arg1
                        );

                        issue_frame_permission(
                            1,
                            arg0,
                            arg1
                        );
                    end

                    else if (command_word == "REVOKE") begin
                        parsed = $sscanf(
                            command_line,
                            "%s %d %d",
                            command_word,
                            arg0,
                            arg1
                        );

                        issue_frame_permission(
                            0,
                            arg0,
                            arg1
                        );
                    end

                    else if (command_word == "SHARE") begin
                        parsed = $sscanf(
                            command_line,
                            "%s %d %d",
                            command_word,
                            arg0,
                            arg1
                        );

                        issue_share(arg0, arg1);
                    end

                    //--------------------------------------------------
                    // General Memory
                    //--------------------------------------------------

                    else if (command_word == "MEMWRITE") begin
                        parsed = $sscanf(
                            command_line,
                            "%s %h %h",
                            command_word,
                            arg0,
                            arg1
                        );

                        issue_memory(
                            1,
                            arg0,
                            arg1
                        );
                    end

                    else if (command_word == "MEMREAD") begin
                        parsed = $sscanf(
                            command_line,
                            "%s %h",
                            command_word,
                            arg0
                        );

                        issue_memory(
                            0,
                            arg0,
                            0
                        );
                    end

                    else if (command_word == "MEMGRANTR") begin
                        parsed = $sscanf(
                            command_line,
                            "%s %h %d",
                            command_word,
                            arg0,
                            arg1
                        );

                        issue_memory_permission(
                            0,
                            arg0,
                            arg1
                        );
                    end

                    else if (command_word == "MEMGRANTW") begin
                        parsed = $sscanf(
                            command_line,
                            "%s %h %d",
                            command_word,
                            arg0,
                            arg1
                        );

                        issue_memory_permission(
                            1,
                            arg0,
                            arg1
                        );
                    end

                    else if (command_word == "MEMREVOKER") begin
                        parsed = $sscanf(
                            command_line,
                            "%s %h %d",
                            command_word,
                            arg0,
                            arg1
                        );

                        issue_memory_permission(
                            2,
                            arg0,
                            arg1
                        );
                    end

                    else if (command_word == "MEMREVOKEW") begin
                        parsed = $sscanf(
                            command_line,
                            "%s %h %d",
                            command_word,
                            arg0,
                            arg1
                        );

                        issue_memory_permission(
                            3,
                            arg0,
                            arg1
                        );
                    end

                    //--------------------------------------------------
                    // Status and exit
                    //--------------------------------------------------

                    else if (command_word == "STATUS") begin
                        print_status();
                    end

                    else if (command_word == "QUIT") begin
                        $display("OK QUIT");

                        if (!interactive_mode)
                            $fclose(command_file);

                        $finish;
                    end

                    else begin
                        $display(
                            "ERROR UNKNOWN_COMMAND %0s",
                            command_word
                        );
                    end
                end

                // Interactive mode uses a persistent stdout pipe.
                // Flush every command response immediately.
                // Explicit VPI stdout descriptor.
                $fflush(32'h8000_0001);
            end
        end

        if (!interactive_mode)
            $fclose(command_file);

        $display("IFA_V4_OS_BRIDGE COMPLETE");

        $finish;
    end

endmodule
