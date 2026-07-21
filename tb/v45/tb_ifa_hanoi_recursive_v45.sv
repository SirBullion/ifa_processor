`timescale 1ns/1ps

module tb_ifa_hanoi_recursive_v45;
    parameter integer DISKS = 5;
    localparam integer EXPECTED_MOVES = (1 << DISKS) - 1;

    logic clk = 1'b0;
    logic reset = 1'b1;
    logic start = 1'b0;
    logic busy;
    logic done;
    logic move_valid;
    logic [$clog2(DISKS + 1)-1:0] move_disk;
    logic [1:0] move_from;
    logic [1:0] move_to;
    logic [31:0] move_count;
    logic [$clog2(DISKS + 3)-1:0] stack_depth;
    integer cycles = 0;
    integer observed_moves = 0;
    integer disk_peg [1:DISKS];
    integer i;

    ifa_hanoi_recursive_v45 #(.DISKS(DISKS)) dut (
        .clk(clk), .reset(reset), .start(start), .busy(busy), .done(done),
        .move_valid(move_valid), .move_disk(move_disk),
        .move_from(move_from), .move_to(move_to),
        .move_count(move_count), .stack_depth(stack_depth)
    );

    always #5 clk = ~clk;

    always @(posedge clk) begin
        if (busy)
            cycles <= cycles + 1;

        if (move_valid) begin
            observed_moves <= observed_moves + 1;
            if (move_disk < 1 || move_disk > DISKS)
                $fatal(1, "Invalid disk number %0d", move_disk);
            if (disk_peg[move_disk] != move_from)
                $fatal(1, "Disk %0d is not on source peg %0d", move_disk, move_from);
            for (i = 1; i < move_disk; i = i + 1)
                if (disk_peg[i] == move_to)
                    $fatal(1, "Illegal move: disk %0d onto smaller disk %0d", move_disk, i);
            disk_peg[move_disk] <= move_to;
            $display("MOVE %0d FROM %0d TO %0d", move_disk, move_from, move_to);
        end
    end

    initial begin
        if (DISKS == 5)
            $dumpfile("sim/v45/hanoi_5.vcd");
        else if (DISKS == 10)
            $dumpfile("sim/v45/hanoi_10.vcd");
        else
            $dumpfile("sim/v45/hanoi.vcd");
        $dumpvars(0, tb_ifa_hanoi_recursive_v45);

        for (i = 1; i <= DISKS; i = i + 1)
            disk_peg[i] = 0;

        repeat (2) @(posedge clk);
        reset <= 1'b0;
        @(posedge clk);
        start <= 1'b1;
        @(posedge clk);
        start <= 1'b0;

        wait (done);
        @(posedge clk);

        if (observed_moves != EXPECTED_MOVES)
            $fatal(1, "Expected %0d moves, observed %0d", EXPECTED_MOVES, observed_moves);
        if (move_count != EXPECTED_MOVES)
            $fatal(1, "Hardware count expected %0d, got %0d", EXPECTED_MOVES, move_count);
        for (i = 1; i <= DISKS; i = i + 1)
            if (disk_peg[i] != 2)
                $fatal(1, "Disk %0d did not finish on peg C", i);

        $display("PASS: HANOI(%0d), moves=%0d, cycles=%0d", DISKS, observed_moves, cycles);
        $finish;
    end
endmodule
