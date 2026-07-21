module ifa_hanoi_recursive_v45 #(
    parameter integer DISKS = 5,
    parameter integer STACK_DEPTH = DISKS + 2
)(
    input  logic clk,
    input  logic reset,
    input  logic start,
    output logic busy,
    output logic done,
    output logic move_valid,
    output logic [$clog2(DISKS + 1)-1:0] move_disk,
    output logic [1:0] move_from,
    output logic [1:0] move_to,
    output logic [31:0] move_count,
    output logic [$clog2(STACK_DEPTH + 1)-1:0] stack_depth
);
    localparam integer DISK_W = $clog2(DISKS + 1);
    localparam logic [1:0] PEG_A = 2'd0;
    localparam logic [1:0] PEG_B = 2'd1;
    localparam logic [1:0] PEG_C = 2'd2;

    logic [DISK_W-1:0] frame_n [0:STACK_DEPTH-1];
    logic [1:0] frame_source [0:STACK_DEPTH-1];
    logic [1:0] frame_target [0:STACK_DEPTH-1];
    logic [1:0] frame_aux [0:STACK_DEPTH-1];
    logic [1:0] frame_phase [0:STACK_DEPTH-1];
    integer sp;
    integer top;

    assign stack_depth = sp;

    always_ff @(posedge clk) begin
        move_valid <= 1'b0;

        if (reset) begin
            busy       <= 1'b0;
            done       <= 1'b0;
            move_disk  <= '0;
            move_from  <= '0;
            move_to    <= '0;
            move_count <= '0;
            sp          <= 0;
        end else if (start && !busy && !done) begin
            frame_n[0]      <= DISKS;
            frame_source[0] <= PEG_A;
            frame_target[0] <= PEG_C;
            frame_aux[0]    <= PEG_B;
            frame_phase[0]  <= 2'd0;
            sp               <= 1;
            busy             <= 1'b1;
            move_count       <= '0;
        end else if (busy) begin
            if (sp == 0) begin
                busy <= 1'b0;
                done <= 1'b1;
            end else begin
                top = sp - 1;

                if (frame_n[top] == 0) begin
                    sp <= sp - 1;
                end else begin
                    case (frame_phase[top])
                        2'd0: begin
                            // HANOI(n-1, source, auxiliary, target)
                            frame_phase[top]  <= 2'd1;
                            frame_n[sp]       <= frame_n[top] - 1'b1;
                            frame_source[sp]  <= frame_source[top];
                            frame_target[sp]  <= frame_aux[top];
                            frame_aux[sp]     <= frame_target[top];
                            frame_phase[sp]   <= 2'd0;
                            sp                <= sp + 1;
                        end
                        2'd1: begin
                            move_valid        <= 1'b1;
                            move_disk         <= frame_n[top];
                            move_from         <= frame_source[top];
                            move_to           <= frame_target[top];
                            move_count        <= move_count + 1'b1;
                            frame_phase[top]  <= 2'd2;
                        end
                        2'd2: begin
                            // HANOI(n-1, auxiliary, target, source)
                            frame_phase[top]  <= 2'd3;
                            frame_n[sp]       <= frame_n[top] - 1'b1;
                            frame_source[sp]  <= frame_aux[top];
                            frame_target[sp]  <= frame_target[top];
                            frame_aux[sp]     <= frame_source[top];
                            frame_phase[sp]   <= 2'd0;
                            sp                <= sp + 1;
                        end
                        default: sp <= sp - 1;
                    endcase
                end
            end
        end
    end
endmodule
