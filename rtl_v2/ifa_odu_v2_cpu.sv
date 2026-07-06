module ifa_odu_v2_cpu (
    input  logic clk,
    input  logic reset,

    output logic halted,
    output logic print_valid,
    output logic [7:0] print_data,

    output logic [7:0] a_reg,
    output logic [7:0] b_reg,
    output logic [3:0] addr_reg,

    output logic [7:0] out_y,
    output logic [7:0] out_ra,
    output logic [7:0] out_rd,
    output logic [7:0] out_r0,
    output logic [7:0] out_t
);

    logic [15:0] imem [0:255];

    initial begin
        $readmemh("odu_v2_program.hex", imem);
    end

    logic [7:0] pc;
    logic [15:0] ir;

    logic start_odu;
    logic done_odu;
    logic [1:0] mode;

    logic [7:0] y, ra, rd, r0, t;
    logic [7:0] fb_y, fb_ra, fb_rd, fb_r0, fb_t;
    logic [7:0] core_out_y, core_out_ra, core_out_rd, core_out_r0, core_out_t;

    logic [3:0] rpc_op;
    logic [7:0] rpc_result;
    logic rpc_cb;
    logic rpc_eq, rpc_gt, rpc_lt;
    logic [7:0] rpc_ra, rpc_rd, rpc_r1, rpc_r0, rpc_a_over_b, rpc_b_over_a;

    logic call_push;
    logic call_pop;
    logic [7:0] call_return_pc;
    logic [7:0] call_return_target;
    logic call_empty;
    logic call_full;

    logic rpush;
    logic rpop;
    logic [7:0] frame_y;
    logic [7:0] frame_ra;
    logic [7:0] frame_rd;
    logic [7:0] frame_r0;
    logic [7:0] frame_t;
    logic frame_empty;
    logic frame_full;

    typedef enum logic [1:0] {
        FETCH,
        EXEC,
        WAIT_ODU,
        HALTED
    } state_t;

    state_t state;

    ifa_odu_v2_core core (
        .clk(clk),
        .reset(reset),
        .start(start_odu),
        .mode(mode),
        .a(a_reg),
        .b(b_reg),
        .mem_addr(addr_reg),
        .done(done_odu),

        .y(y),
        .ra(ra),
        .rd(rd),
        .r0(r0),
        .t(t),

        .fb_y(fb_y),
        .fb_ra(fb_ra),
        .fb_rd(fb_rd),
        .fb_r0(fb_r0),
        .fb_t(fb_t),

        .out_y(core_out_y),
        .out_ra(core_out_ra),
        .out_rd(core_out_rd),
        .out_r0(core_out_r0),
        .out_t(core_out_t)
    );

    always_comb begin
        case (ir[15:12])
            4'h8: rpc_op = 4'd0; // RPC_ADD
            4'h9: rpc_op = 4'd1; // RPC_SUB
            4'hA: rpc_op = 4'd2; // RPC_COMPARE
            default: rpc_op = 4'd0;
        endcase
    end

    ifa_rpc rpc0 (
        .op(rpc_op),
        .A(a_reg),
        .B(b_reg),
        .result(rpc_result),
        .carry_borrow(rpc_cb),
        .eq(rpc_eq),
        .gt(rpc_gt),
        .lt(rpc_lt),
        .ra(rpc_ra),
        .rd(rpc_rd),
        .r1(rpc_r1),
        .r0(rpc_r0),
        .a_over_b(rpc_a_over_b),
        .b_over_a(rpc_b_over_a)
    );


    ifa_call_stack call_stack0 (
        .clk(clk),
        .reset(reset),
        .push(call_push),
        .pop(call_pop),
        .push_data((ir[11:8] == 4'h3) ? out_y : call_return_target),
        .top(call_return_pc),
        .empty(call_empty),
        .full(call_full)
    );


    ifa_relation_frame_stack frame_stack0 (
        .clk(clk),
        .reset(reset),
        .push(rpush),
        .pop(rpop),

        .y_in(out_y),
        .ra_in(out_ra),
        .rd_in(out_rd),
        .r0_in(out_r0),
        .t_in(out_t),

        .y_out(frame_y),
        .ra_out(frame_ra),
        .rd_out(frame_rd),
        .r0_out(frame_r0),
        .t_out(frame_t),

        .empty(frame_empty),
        .full(frame_full)
    );

    always_ff @(posedge clk) begin
        if (reset) begin
            pc <= 0;
            ir <= 0;
            halted <= 0;
            state <= FETCH;

            a_reg <= 0;
            b_reg <= 0;
            addr_reg <= 0;
            mode <= 0;
            start_odu <= 0;
            call_push <= 0;
            call_pop <= 0;
            rpush <= 0;
            rpop <= 0;
            print_valid <= 0;
            rpush <= 0;
            rpop <= 0;

            out_y <= 0;
            out_ra <= 0;
            out_rd <= 0;
            out_r0 <= 0;
            out_t <= 0;
        end else begin
            start_odu <= 0;
            call_push <= 0;
            call_pop <= 0;
            rpush <= 0;
            rpop <= 0;
            print_valid <= 0;

            case (state)

                FETCH: begin
                    ir <= imem[pc];
                    state <= EXEC;
                end

                EXEC: begin
                    case (ir[15:12])

                        4'h0: begin
                            // Branch instruction:
                            // ir[11:8] = condition
                            // ir[7:0]  = full 8-bit target PC
                            case (ir[11:8])
                                4'h1: begin // BR_EQ
                                    if (out_r0[2]) pc <= ir[7:0];
                                    else pc <= pc + 1;
                                end

                                4'h2: begin // BR_GT
                                    if (out_r0[1]) pc <= ir[7:0];
                                    else pc <= pc + 1;
                                end

                                4'h3: begin // BR_LT
                                    if (out_r0[0]) pc <= ir[7:0];
                                    else pc <= pc + 1;
                                end

                                4'h4: begin // JMP
                                    pc <= ir[7:0];
                                end

                                default: begin
                                    pc <= pc + 1;
                                end
                            endcase

                            state <= FETCH;
                        end

                        4'h1: begin
                            a_reg <= ir[7:0];
                            pc <= pc + 1;
                            state <= FETCH;
                        end

                        4'h2: begin
                            b_reg <= ir[7:0];
                            pc <= pc + 1;
                            state <= FETCH;
                        end

                        4'h3: begin
                            addr_reg <= ir[3:0];
                            pc <= pc + 1;
                            state <= FETCH;
                        end

                        4'h4: begin
                            mode <= 2'd0;
                            start_odu <= 1;
                            state <= WAIT_ODU;
                        end

                        4'h5: begin
                            mode <= 2'd1;
                            start_odu <= 1;
                            state <= WAIT_ODU;
                        end

                        4'h6: begin
                            mode <= 2'd2;
                            start_odu <= 1;
                            state <= WAIT_ODU;
                        end

                        4'h7: begin
                            mode <= 2'd3;
                            start_odu <= 1;
                            state <= WAIT_ODU;
                        end

                        4'h8, 4'h9: begin
                            out_y  <= rpc_result;
                            out_ra <= rpc_ra;
                            out_rd <= rpc_rd;
                            out_r0 <= rpc_r0;
                            out_t  <= {6'b0, rpc_cb, 1'b0};
                            pc <= pc + 1;
                            state <= FETCH;
                        end

                        4'hA: begin
                            out_y  <= rpc_result;
                            out_ra <= rpc_ra;
                            out_rd <= rpc_rd;
                            out_r0 <= {5'b0, rpc_eq, rpc_gt, rpc_lt};
                            out_t  <= 8'b0;
                            pc <= pc + 1;
                            state <= FETCH;
                        end

                        4'hF: begin
                            case (ir[11:8])
                                4'h1: begin // CALL target
                                    call_return_target <= pc + 8'd1;
                                    call_push <= 1;
                                    pc <= ir[7:0];
                                    state <= FETCH;
                                end

                                4'h2: begin // RET
                                    call_pop <= 1;
                                    pc <= call_return_pc;
                                    state <= FETCH;
                                end

                                4'h3: begin // PUSH out_y
                                    call_push <= 1;
                                    pc <= pc + 1;
                                    state <= FETCH;
                                end

                                4'h4: begin // POP into out_y
                                    out_y <= call_return_pc;
                                    call_pop <= 1;
                                    pc <= pc + 1;
                                    state <= FETCH;
                                end

                                4'h5: begin // RPUSH relation frame
                                    rpush <= 1;
                                    pc <= pc + 1;
                                    state <= FETCH;
                                end

                                4'h6: begin // RPOP relation frame
                                    out_y  <= frame_y;
                                    out_ra <= frame_ra;
                                    out_rd <= frame_rd;
                                    out_r0 <= frame_r0;
                                    out_t  <= frame_t;
                                    rpop <= 1;
                                    pc <= pc + 1;
                                    state <= FETCH;
                                end

                                4'h7: begin // PRINTY
                                    print_data  <= out_y;
                                    print_valid <= 1;
                                    pc <= pc + 1;
                                    state <= FETCH;
                                end

                                4'h8: begin // PRINTRA
                                    print_data  <= out_ra;
                                    print_valid <= 1;
                                    pc <= pc + 1;
                                    state <= FETCH;
                                end

                                4'h9: begin // PRINTRD
                                    print_data  <= out_rd;
                                    print_valid <= 1;
                                    pc <= pc + 1;
                                    state <= FETCH;
                                end

                                4'hA: begin // PRINTR0
                                    print_data  <= out_r0;
                                    print_valid <= 1;
                                    pc <= pc + 1;
                                    state <= FETCH;
                                end

                                4'hB: begin // PRINTT
                                    print_data  <= out_t;
                                    print_valid <= 1;
                                    pc <= pc + 1;
                                    state <= FETCH;
                                end

                                4'hC: begin // PRINTA
                                    print_data  <= a_reg;
                                    print_valid <= 1;
                                    pc <= pc + 1;
                                    state <= FETCH;
                                end

                                4'hD: begin // PRINTB
                                    print_data  <= b_reg;
                                    print_valid <= 1;
                                    pc <= pc + 1;
                                    state <= FETCH;
                                end

                                4'hE: begin // PRINTPC
                                    print_data  <= pc;
                                    print_valid <= 1;
                                    pc <= pc + 1;
                                    state <= FETCH;
                                end

                                4'hF: begin // PRINTIR
                                    print_data  <= ir[7:0];
                                    print_valid <= 1;
                                    pc <= pc + 1;
                                    state <= FETCH;
                                end

                                default: begin // HALT
                                    halted <= 1;
                                    state <= HALTED;
                                end
                            endcase
                        end

                        default: begin
                            pc <= pc + 1;
                            state <= FETCH;
                        end

                    endcase
                end

                WAIT_ODU: begin
                    out_y  <= core_out_y;
                    out_ra <= core_out_ra;
                    out_rd <= core_out_rd;
                    out_r0 <= core_out_r0;
                    out_t  <= core_out_t;

                    pc <= pc + 1;
                    state <= FETCH;
                end

                HALTED: begin
                    halted <= 1;
                end

            endcase
        end
    end

endmodule
