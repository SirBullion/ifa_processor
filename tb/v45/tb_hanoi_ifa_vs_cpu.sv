`timescale 1ns/1ps

module tb_hanoi_ifa_vs_cpu;
    parameter integer DISKS = 5;
    localparam integer EXPECTED = (1 << DISKS) - 1;
    logic clk = 0, reset = 1, start = 0;
    logic ifa_busy, ifa_done, ifa_move_valid;
    logic cpu_busy, cpu_done, cpu_move_valid, cpu_execute_phase;
    logic [$clog2(DISKS+1)-1:0] ifa_disk, cpu_disk;
    logic [1:0] ifa_from, ifa_to, cpu_from, cpu_to;
    logic [31:0] ifa_moves, cpu_moves, cpu_instructions;
    logic [$clog2(DISKS+3)-1:0] ifa_depth, cpu_depth;
    integer ifa_cycles = 0, cpu_cycles = 0;
    integer ifa_seen = 0, cpu_seen = 0;
    integer ifa_sequence [0:EXPECTED-1];

    ifa_hanoi_recursive_v45 #(.DISKS(DISKS)) ifa (
        .clk(clk), .reset(reset), .start(start), .busy(ifa_busy), .done(ifa_done),
        .move_valid(ifa_move_valid), .move_disk(ifa_disk), .move_from(ifa_from),
        .move_to(ifa_to), .move_count(ifa_moves), .stack_depth(ifa_depth));

    cpu_hanoi_stack_ref #(.DISKS(DISKS)) cpu (
        .clk(clk), .reset(reset), .start(start), .busy(cpu_busy), .done(cpu_done),
        .move_valid(cpu_move_valid), .move_disk(cpu_disk), .move_from(cpu_from),
        .move_to(cpu_to), .move_count(cpu_moves), .instruction_count(cpu_instructions),
        .stack_depth(cpu_depth), .execute_phase(cpu_execute_phase));

    always #5 clk = ~clk;
    always @(posedge clk) begin
        if (ifa_busy) ifa_cycles <= ifa_cycles + 1;
        if (cpu_busy) cpu_cycles <= cpu_cycles + 1;
        if (ifa_move_valid) begin
            ifa_sequence[ifa_seen] <= {ifa_disk, ifa_from, ifa_to};
            ifa_seen <= ifa_seen + 1;
        end
        if (cpu_move_valid) begin
            if (cpu_seen >= ifa_seen)
                $fatal(1, "CPU move stream overtook IFÁ stream");
            if (ifa_sequence[cpu_seen] !== {cpu_disk, cpu_from, cpu_to})
                $fatal(1, "Move mismatch at index %0d", cpu_seen);
            cpu_seen <= cpu_seen + 1;
        end
    end

    initial begin
        if (DISKS == 5) $dumpfile("sim/v45/hanoi_5_ifa_vs_cpu.vcd");
        else $dumpfile("sim/v45/hanoi_10_ifa_vs_cpu.vcd");
        $dumpvars(0, tb_hanoi_ifa_vs_cpu);
        repeat (2) @(posedge clk); reset <= 0;
        @(posedge clk); start <= 1;
        @(posedge clk); start <= 0;
        wait (ifa_done && cpu_done);
        @(posedge clk);
        if (ifa_seen != EXPECTED || cpu_seen != EXPECTED)
            $fatal(1, "Move counts differ: IFA=%0d CPU=%0d expected=%0d", ifa_seen, cpu_seen, EXPECTED);
        $display("PASS HANOI(%0d): identical %0d-move streams", DISKS, EXPECTED);
        $display("IFA cycles=%0d; CPU cycles=%0d; CPU instructions=%0d", ifa_cycles, cpu_cycles, cpu_instructions);
        $finish;
    end
endmodule
