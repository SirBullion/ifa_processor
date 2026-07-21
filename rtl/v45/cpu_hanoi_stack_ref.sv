`timescale 1ns/1ps

// Conventional single-issue stack-machine reference.  Each recursive frame
// is fetched in one cycle and executed in the next cycle.
module cpu_hanoi_stack_ref #(
    parameter integer DISKS = 5,
    parameter integer STACK_DEPTH = DISKS + 2
)(
    input logic clk, input logic reset, input logic start,
    output logic busy, output logic done, output logic move_valid,
    output logic [$clog2(DISKS + 1)-1:0] move_disk,
    output logic [1:0] move_from, output logic [1:0] move_to,
    output logic [31:0] move_count, output logic [31:0] instruction_count,
    output logic [$clog2(STACK_DEPTH + 1)-1:0] stack_depth,
    output logic execute_phase
);
    localparam integer DISK_W = $clog2(DISKS + 1);
    logic [DISK_W-1:0] frame_n [0:STACK_DEPTH-1];
    logic [1:0] frame_source [0:STACK_DEPTH-1];
    logic [1:0] frame_target [0:STACK_DEPTH-1];
    logic [1:0] frame_aux [0:STACK_DEPTH-1];
    logic [1:0] frame_phase [0:STACK_DEPTH-1];
    logic [DISK_W-1:0] fetched_n;
    logic [1:0] fetched_source, fetched_target, fetched_aux, fetched_phase;
    integer sp;
    integer top;

    assign stack_depth = sp;

    always_ff @(posedge clk) begin
        move_valid <= 1'b0;
        if (reset) begin
            busy <= 1'b0; done <= 1'b0; move_count <= '0;
            instruction_count <= '0; sp <= 0; execute_phase <= 1'b0;
            move_disk <= '0; move_from <= '0; move_to <= '0;
        end else if (start && !busy && !done) begin
            frame_n[0] <= DISKS;
            frame_source[0] <= 2'd0;
            frame_target[0] <= 2'd2;
            frame_aux[0] <= 2'd1;
            frame_phase[0] <= 2'd0;
            sp <= 1; busy <= 1'b1; execute_phase <= 1'b0;
            move_count <= '0; instruction_count <= '0;
        end else if (busy) begin
            instruction_count <= instruction_count + 1'b1;
            if (!execute_phase) begin
                if (sp == 0) begin
                    busy <= 1'b0;
                    done <= 1'b1;
                end else begin
                    top = sp - 1;
                    fetched_n <= frame_n[top];
                    fetched_source <= frame_source[top];
                    fetched_target <= frame_target[top];
                    fetched_aux <= frame_aux[top];
                    fetched_phase <= frame_phase[top];
                    execute_phase <= 1'b1;
                end
            end else begin
                top = sp - 1;
                execute_phase <= 1'b0;
                if (fetched_n == 0) begin
                    sp <= sp - 1;
                end else case (fetched_phase)
                    2'd0: begin
                        frame_phase[top] <= 2'd1;
                        frame_n[sp] <= fetched_n - 1'b1;
                        frame_source[sp] <= fetched_source;
                        frame_target[sp] <= fetched_aux;
                        frame_aux[sp] <= fetched_target;
                        frame_phase[sp] <= 2'd0;
                        sp <= sp + 1;
                    end
                    2'd1: begin
                        move_valid <= 1'b1;
                        move_disk <= fetched_n;
                        move_from <= fetched_source;
                        move_to <= fetched_target;
                        move_count <= move_count + 1'b1;
                        frame_phase[top] <= 2'd2;
                    end
                    2'd2: begin
                        frame_phase[top] <= 2'd3;
                        frame_n[sp] <= fetched_n - 1'b1;
                        frame_source[sp] <= fetched_aux;
                        frame_target[sp] <= fetched_target;
                        frame_aux[sp] <= fetched_source;
                        frame_phase[sp] <= 2'd0;
                        sp <= sp + 1;
                    end
                    default: sp <= sp - 1;
                endcase
            end
        end
    end
endmodule
