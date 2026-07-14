`timescale 1ns/1ps

module tb_ifa_program_executor_v4;

    localparam integer WIDTH      = 8;
    localparam integer OP_WIDTH   = 4;
    localparam integer IR_WIDTH   = 16;
    localparam integer IMEM_DEPTH = 256;
    localparam integer IMEM_AW    = 8;

    logic clk;
    logic rst;

    logic start;
    logic step;
    logic stop;

    logic busy;
    logic halted;
    logic fault;

    logic imem_write_valid;
    logic [IMEM_AW-1:0] imem_write_address;
    logic [IR_WIDTH-1:0] imem_write_data;

    //--------------------------------------------------------------
    // Mock active YÀRÁ context
    //--------------------------------------------------------------

    logic active_valid;
    logic active_running;

    logic [WIDTH-1:0] active_pc;
    logic [IR_WIDTH-1:0] active_ir;
    logic [WIDTH-1:0] active_a;
    logic [WIDTH-1:0] active_b;
    logic [WIDTH-1:0] active_address;
    logic [WIDTH-1:0] active_flags;

    //--------------------------------------------------------------
    // Executor context-write outputs
    //--------------------------------------------------------------

    logic context_write;

    logic [WIDTH-1:0] write_pc;
    logic [IR_WIDTH-1:0] write_ir;
    logic [WIDTH-1:0] write_a;
    logic [WIDTH-1:0] write_b;
    logic [WIDTH-1:0] write_address;
    logic [WIDTH-1:0] write_flags;

    //--------------------------------------------------------------
    // Native dispatch
    //--------------------------------------------------------------

    logic execute_valid;
    logic [OP_WIDTH-1:0] execute_op;
    logic [WIDTH-1:0] execute_a;
    logic [WIDTH-1:0] execute_b;

    //--------------------------------------------------------------
    // Mock kernel status
    //--------------------------------------------------------------

    logic operation_valid;

    logic exception_valid;
    logic [3:0] exception_code;

    logic state_valid;
    logic [3:0] state_code;

    logic eq_flag;
    logic gt_flag;
    logic lt_flag;

    //--------------------------------------------------------------
    // Inspection
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
    // DUT
    //--------------------------------------------------------------

    ifa_program_executor_v4 #(
        .WIDTH(WIDTH),
        .OP_WIDTH(OP_WIDTH),
        .IR_WIDTH(IR_WIDTH),
        .IMEM_DEPTH(IMEM_DEPTH),
        .IMEM_AW(IMEM_AW)
    ) dut (
        .clk(clk),
        .rst(rst),

        .start(start),
        .step(step),
        .stop(stop),

        .busy(busy),
        .halted(halted),
        .fault(fault),

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

        .context_write(context_write),

        .write_pc(write_pc),
        .write_ir(write_ir),
        .write_a(write_a),
        .write_b(write_b),
        .write_address(write_address),
        .write_flags(write_flags),

        .execute_valid(execute_valid),
        .execute_op(execute_op),
        .execute_a(execute_a),
        .execute_b(execute_b),

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
    // Clock
    //--------------------------------------------------------------

    always #5 clk = ~clk;

    //--------------------------------------------------------------
    // Mock ONÍLẸ̀ context commit
    //--------------------------------------------------------------

    always_ff @(posedge clk) begin
        if (rst) begin
            active_pc      <= 8'h00;
            active_ir      <= 16'h0000;
            active_a       <= 8'h00;
            active_b       <= 8'h00;
            active_address <= 8'h00;
            active_flags   <= 8'h00;
        end else if (context_write) begin
            active_pc      <= write_pc;
            active_ir      <= write_ir;
            active_a       <= write_a;
            active_b       <= write_b;
            active_address <= write_address;
            active_flags   <= write_flags;
        end
    end

    //--------------------------------------------------------------
    // Mock native RAU/kernel response
    //--------------------------------------------------------------

    always_comb begin
        operation_valid = execute_valid;

        exception_valid = 1'b0;
        exception_code  = 4'h0;

        state_valid = 1'b0;
        state_code  = 4'h0;

        eq_flag = 1'b0;
        gt_flag = 1'b0;
        lt_flag = 1'b0;

        if (execute_valid) begin
            case (execute_op)

                4'h0: begin
                    // PAPO
                    operation_valid = 1'b1;
                end

                4'h6: begin
                    // SEDA
                    eq_flag = (execute_a == execute_b);
                    gt_flag = (execute_a > execute_b);
                    lt_flag = (execute_a < execute_b);
                end

                default: begin
                    operation_valid = 1'b1;
                end
            endcase
        end
    end

    //--------------------------------------------------------------
    // Program-memory writer
    //--------------------------------------------------------------

    task automatic write_instruction(
        input logic [7:0] address,
        input logic [15:0] instruction
    );
    begin
        @(negedge clk);

        imem_write_address = address;
        imem_write_data = instruction;
        imem_write_valid = 1'b1;

        @(posedge clk);
        #1;

        @(negedge clk);
        imem_write_valid = 1'b0;
    end
    endtask

    //--------------------------------------------------------------
    // Test
    //
    // 00: LDAI 05
    // 01: LDBI 08
    // 02: NATIVE PAPO
    // 03: LDBI 05
    // 04: NATIVE SEDA
    // 05: BR_EQ 07
    // 06: HALT       -- must be skipped
    // 07: LDADDR 2A
    // 08: HALT
    //--------------------------------------------------------------

    initial begin
        clk = 1'b0;
        rst = 1'b1;

        start = 1'b0;
        step  = 1'b0;
        stop  = 1'b0;

        imem_write_valid   = 1'b0;
        imem_write_address = 8'h00;
        imem_write_data    = 16'h0000;

        active_valid   = 1'b1;
        active_running = 1'b1;

        repeat (3) @(posedge clk);
        rst = 1'b0;

        write_instruction(8'h00, 16'h1005);
        write_instruction(8'h01, 16'h2008);
        write_instruction(8'h02, 16'h8000);
        write_instruction(8'h03, 16'h2005);
        write_instruction(8'h04, 16'h8600);
        write_instruction(8'h05, 16'h0107);
        write_instruction(8'h06, 16'hF100);
        write_instruction(8'h07, 16'h302A);
        write_instruction(8'h08, 16'hF100);

        //----------------------------------------------------------
        // Start continuous execution
        //----------------------------------------------------------

        @(negedge clk);
        start = 1'b1;

        @(posedge clk);
        #1;

        @(negedge clk);
        start = 1'b0;

        //----------------------------------------------------------
        // Wait for final HALT
        //----------------------------------------------------------

        wait (halted === 1'b1);
        #1;

        //----------------------------------------------------------
        // Verify final context
        //----------------------------------------------------------

        if (fault !== 1'b0)
            $fatal(1, "Executor entered FAULT state");

        if (active_a !== 8'h05)
            $fatal(
                1,
                "LDAI failed: A=%02h",
                active_a
            );

        if (active_b !== 8'h05)
            $fatal(
                1,
                "LDBI failed: B=%02h",
                active_b
            );

        if (active_flags[2:0] !== 3'b100)
            $fatal(
                1,
                "SEDA flags failed: FLAGS=%02h",
                active_flags
            );

        if (active_address !== 8'h2A)
            $fatal(
                1,
                "BR_EQ or LDADDR failed: ADDRESS=%02h",
                active_address
            );

        if (active_pc !== 8'h08)
            $fatal(
                1,
                "Final PC failed: PC=%02h",
                active_pc
            );

        if (last_operation_valid !== 1'b1)
            $fatal(
                1,
                "Native operation status was not captured"
            );

        $display(
            "============================================================"
        );
        $display(
            "PASS: IFÁ V4 PROGRAM EXECUTOR UNIT TEST COMPLETE"
        );
        $display(
            "PASS: LDAI AND LDBI VERIFIED"
        );
        $display(
            "PASS: NATIVE PAPO DISPATCH VERIFIED"
        );
        $display(
            "PASS: NATIVE SEDA FLAGS VERIFIED"
        );
        $display(
            "PASS: BR_EQ VERIFIED"
        );
        $display(
            "PASS: LDADDR VERIFIED"
        );
        $display(
            "PASS: HALT VERIFIED"
        );
        $display(
            "============================================================"
        );

        $finish;
    end

endmodule
