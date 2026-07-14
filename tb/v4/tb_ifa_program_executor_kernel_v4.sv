`timescale 1ns/1ps

module tb_ifa_program_executor_kernel_v4;

    localparam integer WIDTH      = 8;
    localparam integer OP_WIDTH   = 4;
    localparam integer IR_WIDTH   = 16;
    localparam integer RMU_DEPTH  = 16;
    localparam integer MEM_ADDR_W = 4;
    localparam integer MAX_YARA   = 2;
    localparam integer YARA_W     = 1;

    localparam integer IMEM_DEPTH = 256;
    localparam integer IMEM_AW    = 8;

    //--------------------------------------------------------------
    // Clock and reset
    //--------------------------------------------------------------

    logic clk;
    logic rst;

    always #5 clk = ~clk;

    //--------------------------------------------------------------
    // BABALÁWO and YÀRÁ lifecycle
    //--------------------------------------------------------------

    logic babalawo_mode;

    logic create_valid;
    logic select_valid;
    logic pause_valid;
    logic resume_valid;
    logic destroy_valid;

    logic [YARA_W-1:0] command_yara;

    //--------------------------------------------------------------
    // Executor program control
    //--------------------------------------------------------------

    logic executor_start;
    logic executor_step;
    logic executor_stop;

    logic executor_busy;
    logic executor_halted;
    logic executor_fault;

    //--------------------------------------------------------------
    // Executor instruction-memory administration
    //--------------------------------------------------------------

    logic imem_write_valid;
    logic [IMEM_AW-1:0] imem_write_address;
    logic [IR_WIDTH-1:0] imem_write_data;

    //--------------------------------------------------------------
    // Executor → kernel context update
    //--------------------------------------------------------------

    logic executor_context_write;

    logic [WIDTH-1:0] executor_write_pc;
    logic [IR_WIDTH-1:0] executor_write_ir;
    logic [WIDTH-1:0] executor_write_a;
    logic [WIDTH-1:0] executor_write_b;
    logic [WIDTH-1:0] executor_write_address;
    logic [WIDTH-1:0] executor_write_flags;

    //--------------------------------------------------------------
    // Executor → kernel native execution
    //--------------------------------------------------------------

    logic executor_execute_valid;
    logic [OP_WIDTH-1:0] executor_execute_op;
    logic [WIDTH-1:0] executor_execute_a;
    logic [WIDTH-1:0] executor_execute_b;

    //--------------------------------------------------------------
    // Kernel administrative inputs not used in this test
    //--------------------------------------------------------------

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

    //--------------------------------------------------------------
    // Kernel outputs
    //--------------------------------------------------------------

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

    //--------------------------------------------------------------
    // Executor inspection
    //--------------------------------------------------------------

    logic [WIDTH-1:0] executor_pc;
    logic [IR_WIDTH-1:0] executor_ir;
    logic [3:0] executor_state;

    logic instruction_done;

    logic last_operation_valid;

    logic last_exception_valid;
    logic [3:0] last_exception_code;

    logic last_state_valid;
    logic [3:0] last_state_code;

    //--------------------------------------------------------------
    // Test observation
    //--------------------------------------------------------------

    integer observed_hits;
    integer observed_misses;
    integer observed_native_requests;
    integer observed_instruction_done;

    //--------------------------------------------------------------
    // Real program executor
    //--------------------------------------------------------------

    ifa_program_executor_v4 #(
        .WIDTH(WIDTH),
        .OP_WIDTH(OP_WIDTH),
        .IR_WIDTH(IR_WIDTH),
        .IMEM_DEPTH(IMEM_DEPTH),
        .IMEM_AW(IMEM_AW)
    ) executor (
        .clk(clk),
        .rst(rst),

        .start(executor_start),
        .step(executor_step),
        .stop(executor_stop),

        .busy(executor_busy),
        .halted(executor_halted),
        .fault(executor_fault),

        .imem_write_valid(imem_write_valid),
        .imem_write_address(imem_write_address),
        .imem_write_data(imem_write_data),

        .active_valid(active_valid),
        .active_running(active_running),

        .active_pc(active_pc),
        .active_ir(active_ir),
        .active_a(active_a),
        .active_b(active_b),
        .active_address(active_address),
        .active_flags(active_flags),

        .context_write(executor_context_write),

        .write_pc(executor_write_pc),
        .write_ir(executor_write_ir),
        .write_a(executor_write_a),
        .write_b(executor_write_b),
        .write_address(executor_write_address),
        .write_flags(executor_write_flags),

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

        .executor_pc(executor_pc),
        .executor_ir(executor_ir),
        .executor_state(executor_state),

        .instruction_done(instruction_done),

        .last_operation_valid(last_operation_valid),

        .last_exception_valid(last_exception_valid),
        .last_exception_code(last_exception_code),

        .last_state_valid(last_state_valid),
        .last_state_code(last_state_code)
    );

    //--------------------------------------------------------------
    // Real ONÍLẸ̀ kernel
    //--------------------------------------------------------------

    ifa_onile_kernel_v4 #(
        .WIDTH(WIDTH),
        .OP_WIDTH(OP_WIDTH),
        .IR_WIDTH(IR_WIDTH),
        .RMU_DEPTH(RMU_DEPTH),
        .MEM_ADDR_W(MEM_ADDR_W),
        .MAX_YARA(MAX_YARA)
    ) kernel (
        .clk(clk),
        .rst(rst),

        .babalawo_mode(babalawo_mode),

        .create_valid(create_valid),
        .select_valid(select_valid),
        .pause_valid(pause_valid),
        .resume_valid(resume_valid),
        .destroy_valid(destroy_valid),

        .command_yara(command_yara),

        .context_write(executor_context_write),

        .write_pc(executor_write_pc),
        .write_ir(executor_write_ir),
        .write_a(executor_write_a),
        .write_b(executor_write_b),
        .write_address(executor_write_address),
        .write_flags(executor_write_flags),

        .execute_valid(executor_execute_valid),
        .execute_op(executor_execute_op),
        .execute_a(executor_execute_a),
        .execute_b(executor_execute_b),

        .frame_grant_valid(frame_grant_valid),
        .frame_revoke_valid(frame_revoke_valid),

        .frame_admin_source(frame_admin_source),
        .frame_admin_destination(frame_admin_destination),

        .frame_share_request(frame_share_request),
        .frame_share_source(frame_share_source),
        .frame_share_destination(frame_share_destination),

        .mem_request(mem_request),
        .mem_write(mem_write),
        .mem_address(mem_address),
        .mem_write_data(mem_write_data),

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

    //--------------------------------------------------------------
    // Observe real kernel/RMU behavior
    //--------------------------------------------------------------

    always_ff @(posedge clk) begin
        if (rst) begin
            observed_hits             <= 0;
            observed_misses           <= 0;
            observed_native_requests  <= 0;
            observed_instruction_done <= 0;
        end else begin
            if (rmu_hit)
                observed_hits <= observed_hits + 1;

            if (rmu_miss)
                observed_misses <= observed_misses + 1;

            if (executor_execute_valid)
                observed_native_requests <=
                    observed_native_requests + 1;

            if (instruction_done)
                observed_instruction_done <=
                    observed_instruction_done + 1;
        end
    end

    //--------------------------------------------------------------
    // One-cycle lifecycle command
    //--------------------------------------------------------------

    task automatic lifecycle_command(
        input logic do_create,
        input logic do_select,
        input logic do_pause,
        input logic do_resume,
        input logic do_destroy,
        input logic [YARA_W-1:0] yara_id
    );
    begin
        @(negedge clk);

        command_yara = yara_id;

        create_valid  = do_create;
        select_valid  = do_select;
        pause_valid   = do_pause;
        resume_valid  = do_resume;
        destroy_valid = do_destroy;

        @(posedge clk);
        #1;

        @(negedge clk);

        create_valid  = 1'b0;
        select_valid  = 1'b0;
        pause_valid   = 1'b0;
        resume_valid  = 1'b0;
        destroy_valid = 1'b0;
    end
    endtask

    //--------------------------------------------------------------
    // Program-memory writer
    //--------------------------------------------------------------

    task automatic write_instruction(
        input logic [IMEM_AW-1:0] address,
        input logic [IR_WIDTH-1:0] instruction
    );
    begin
        @(negedge clk);

        imem_write_address = address;
        imem_write_data    = instruction;
        imem_write_valid   = 1'b1;

        @(posedge clk);
        #1;

        @(negedge clk);

        imem_write_valid = 1'b0;
    end
    endtask

    //--------------------------------------------------------------
    // Integrated test program
    //
    // 00: LDAI 05
    // 01: LDBI 08
    // 02: NATIVE PAPO   -- first execution: RMU MISS
    // 03: NATIVE PAPO   -- same relation: RMU HIT
    // 04: LDBI 05
    // 05: NATIVE SEDA   -- EQ=1
    // 06: BR_EQ 08
    // 07: HALT          -- must be skipped
    // 08: LDADDR 2A
    // 09: HALT
    //--------------------------------------------------------------

    initial begin
        clk = 1'b0;
        rst = 1'b1;

        babalawo_mode = 1'b0;

        create_valid  = 1'b0;
        select_valid  = 1'b0;
        pause_valid   = 1'b0;
        resume_valid  = 1'b0;
        destroy_valid = 1'b0;

        command_yara = '0;

        executor_start = 1'b0;
        executor_step  = 1'b0;
        executor_stop  = 1'b0;

        imem_write_valid   = 1'b0;
        imem_write_address = '0;
        imem_write_data    = '0;

        frame_grant_valid  = 1'b0;
        frame_revoke_valid = 1'b0;

        frame_admin_source      = '0;
        frame_admin_destination = '0;

        frame_share_request     = 1'b0;
        frame_share_source      = '0;
        frame_share_destination = '0;

        mem_request    = 1'b0;
        mem_write      = 1'b0;
        mem_address    = '0;
        mem_write_data = '0;

        mem_grant_read_valid   = 1'b0;
        mem_grant_write_valid  = 1'b0;
        mem_revoke_read_valid  = 1'b0;
        mem_revoke_write_valid = 1'b0;

        mem_admin_address = '0;
        mem_admin_yara    = '0;

        repeat (4) @(posedge clk);
        rst = 1'b0;

        //----------------------------------------------------------
        // Enter BABALÁWO authority and create/select YÀRÁ 0
        //----------------------------------------------------------

        babalawo_mode = 1'b1;

        lifecycle_command(
            1'b1, 1'b0, 1'b0, 1'b0, 1'b0,
            1'b0
        );

        lifecycle_command(
            1'b0, 1'b1, 1'b0, 1'b0, 1'b0,
            1'b0
        );

        if (!active_valid || !active_running)
            $fatal(
                1,
                "YARA 0 was not created and selected"
            );

        //----------------------------------------------------------
        // Load the program
        //----------------------------------------------------------

        write_instruction(8'h00, 16'h1005);
        write_instruction(8'h01, 16'h2008);
        write_instruction(8'h02, 16'h8000);
        write_instruction(8'h03, 16'h8000);
        write_instruction(8'h04, 16'h2005);
        write_instruction(8'h05, 16'h8600);
        write_instruction(8'h06, 16'h0108);
        write_instruction(8'h07, 16'hF100);
        write_instruction(8'h08, 16'h302A);
        write_instruction(8'h09, 16'hF100);

        //----------------------------------------------------------
        // Run continuously
        //----------------------------------------------------------

        @(negedge clk);
        executor_start = 1'b1;

        @(posedge clk);
        #1;

        @(negedge clk);
        executor_start = 1'b0;

        //----------------------------------------------------------
        // Guard against infinite execution
        //----------------------------------------------------------

        fork
            begin
                wait (executor_halted === 1'b1);
            end

            begin
                repeat (300) @(posedge clk);

                $fatal(
                    1,
                    "Executor/kernel integration timed out"
                );
            end
        join_any

        disable fork;

        #1;

        //----------------------------------------------------------
        // Verify executor state
        //----------------------------------------------------------

        if (executor_fault !== 1'b0)
            $fatal(
                1,
                "Executor entered FAULT state"
            );

        if (executor_halted !== 1'b1)
            $fatal(
                1,
                "Executor did not halt"
            );

        //----------------------------------------------------------
        // Verify real YÀRÁ context
        //----------------------------------------------------------

        if (active_a !== 8'h05)
            $fatal(
                1,
                "Integrated LDAI failed: A=%02h",
                active_a
            );

        if (active_b !== 8'h05)
            $fatal(
                1,
                "Integrated LDBI failed: B=%02h",
                active_b
            );

        if (active_flags[2:0] !== 3'b100)
            $fatal(
                1,
                "Integrated SEDA flags failed: FLAGS=%02h",
                active_flags
            );

        if (active_address !== 8'h2A)
            $fatal(
                1,
                "Integrated BR_EQ/LDADDR failed: ADDRESS=%02h",
                active_address
            );

        if (active_pc !== 8'h09)
            $fatal(
                1,
                "Integrated final PC failed: PC=%02h",
                active_pc
            );

        //----------------------------------------------------------
        // Verify real kernel/native status
        //----------------------------------------------------------

        if (observed_native_requests < 3)
            $fatal(
                1,
                "Expected at least 3 native requests, got %0d",
                observed_native_requests
            );

        if (observed_misses < 2)
            $fatal(
                1,
                "Expected PAPO and SEDA misses, got %0d",
                observed_misses
            );

        if (observed_hits < 1)
            $fatal(
                1,
                "Repeated PAPO did not produce an RMU hit"
            );

        if (yara0_hits < 1)
            $fatal(
                1,
                "YARA 0 RMU hit statistic was not updated"
            );

        if (yara0_misses < 2)
            $fatal(
                1,
                "YARA 0 RMU miss statistic was not updated"
            );

        if (last_operation_valid !== 1'b1)
            $fatal(
                1,
                "Executor did not capture kernel operation_valid"
            );

        if (last_exception_valid !== 1'b0)
            $fatal(
                1,
                "Unexpected native exception: code=%0h",
                last_exception_code
            );

        //----------------------------------------------------------
        // Report
        //----------------------------------------------------------

        $display(
            "============================================================"
        );
        $display(
            "PASS: V4 PROGRAM EXECUTOR + ONILE KERNEL INTEGRATION"
        );
        $display(
            "PASS: PROGRAM FETCH AND DECODE VERIFIED"
        );
        $display(
            "PASS: REAL YARA CONTEXT WRITE-BACK VERIFIED"
        );
        $display(
            "PASS: REAL NATIVE RAU DISPATCH VERIFIED"
        );
        $display(
            "PASS: FIRST PAPO RMU MISS VERIFIED"
        );
        $display(
            "PASS: REPEATED PAPO RMU HIT VERIFIED"
        );
        $display(
            "PASS: REAL SEDA FLAGS AND BR_EQ VERIFIED"
        );
        $display(
            "PASS: PROGRAM HALT VERIFIED"
        );
        $display(
            "HITS=%0d MISSES=%0d NATIVE_REQUESTS=%0d INSTRUCTIONS=%0d",
            observed_hits,
            observed_misses,
            observed_native_requests,
            observed_instruction_done
        );
        $display(
            "FINAL PC=%02h A=%02h B=%02h ADDR=%02h FLAGS=%02h",
            active_pc,
            active_a,
            active_b,
            active_address,
            active_flags
        );
        $display(
            "============================================================"
        );

        $finish;
    end

endmodule
