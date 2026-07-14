`timescale 1ns/1ps

module tb_ifa_yara_manager;

    localparam integer YARA_COUNT = 2;
    localparam integer YARA_W = 1;

    logic clk;
    logic rst;

    logic babalawo_mode;

    logic create_valid;
    logic select_valid;
    logic pause_valid;
    logic resume_valid;
    logic destroy_valid;

    logic [YARA_W-1:0] command_yara;

    logic [YARA_W-1:0] active_yara;
    logic active_valid;
    logic active_running;

    logic [YARA_COUNT-1:0] yara_valid;
    logic [YARA_COUNT-1:0] yara_running;
    logic [YARA_COUNT-1:0] clear_yara;

    logic command_allowed;
    logic command_denied;

    logic [31:0] switch_count;
    logic [31:0] denied_count;

    ifa_yara_manager #(
        .YARA_COUNT(YARA_COUNT)
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

        .active_yara(active_yara),
        .active_valid(active_valid),
        .active_running(active_running),

        .yara_valid(yara_valid),
        .yara_running(yara_running),
        .clear_yara(clear_yara),

        .command_allowed(command_allowed),
        .command_denied(command_denied),

        .switch_count(switch_count),
        .denied_count(denied_count)
    );

    always #5 clk = ~clk;

    task automatic command(
        input logic [2:0] operation,
        input logic room
    );
    begin
        @(negedge clk);

        command_yara = room;

        create_valid  = 0;
        select_valid  = 0;
        pause_valid   = 0;
        resume_valid  = 0;
        destroy_valid = 0;

        case (operation)
            3'd0: create_valid  = 1;
            3'd1: select_valid  = 1;
            3'd2: pause_valid   = 1;
            3'd3: resume_valid  = 1;
            3'd4: destroy_valid = 1;
        endcase

        @(posedge clk);
        #1;

        $display("OP=%0d YARA=%0d allowed=%0d denied=%0d valid=%b running=%b active=%0d",
                 operation, room,
                 command_allowed, command_denied,
                 yara_valid, yara_running, active_yara);

        @(negedge clk);

        create_valid  = 0;
        select_valid  = 0;
        pause_valid   = 0;
        resume_valid  = 0;
        destroy_valid = 0;
    end
    endtask

    initial begin
        $dumpfile("sim/v4/ifa_yara_manager.vcd");
        $dumpvars(0, tb_ifa_yara_manager);

        clk = 0;
        rst = 1;

        babalawo_mode = 0;

        create_valid  = 0;
        select_valid  = 0;
        pause_valid   = 0;
        resume_valid  = 0;
        destroy_valid = 0;

        command_yara = 0;

        repeat (3) @(negedge clk);
        rst = 0;

        $display("============================================================");
        $display("IFÁ V4 YÀRÁ MANAGER TEST");
        $display("============================================================");

        // Normal mode cannot create a room.
        command(3'd0, 0);

        if (command_denied !== 1'b1)
            $fatal(1, "Normal mode CREATE should be denied");

        babalawo_mode = 1;

        // Create both rooms.
        command(3'd0, 0);
        command(3'd0, 1);

        if (yara_valid !== 2'b11)
            $fatal(1, "Both YARA should be valid");

        // Select YÀRÁ 1.
        command(3'd1, 1);

        if (active_yara !== 1)
            $fatal(1, "YARA 1 should be active");

        // Pause YÀRÁ 1.
        command(3'd2, 1);

        if (yara_running[1] !== 1'b0)
            $fatal(1, "YARA 1 should be paused");

        // Selecting paused room must fail.
        command(3'd1, 1);

        if (command_denied !== 1'b1)
            $fatal(1, "Paused YARA must not be selected");

        // Resume and select again.
        command(3'd3, 1);
        command(3'd1, 1);

        if (
            active_yara !== 1 ||
            active_running !== 1'b1
        )
            $fatal(1, "Resumed YARA 1 should be selectable");

        // Destroy YÀRÁ 0.
        command(3'd4, 0);

        if (
            yara_valid[0] !== 1'b0 ||
            clear_yara[0] !== 1'b1
        )
            $fatal(1, "Destroy must invalidate and clear YARA 0");

        $display("");
        $display("FINAL STATE");
        $display("------------------------------------------------------------");
        $display("Valid rooms   = %b", yara_valid);
        $display("Running rooms = %b", yara_running);
        $display("Active YARA   = %0d", active_yara);
        $display("Switches      = %0d", switch_count);
        $display("Denied cmds   = %0d", denied_count);

        $display("============================================================");
        $display("PASS: Only Babaláwo may manage YÀRÁ");
        $display("PASS: YÀRÁ can be created, selected, paused and resumed");
        $display("PASS: Paused rooms cannot be selected");
        $display("PASS: Destroy invalidates and clears the room");
        $display("============================================================");

        $finish;
    end

endmodule
