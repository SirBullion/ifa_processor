module ifa_odu_v2_core #(
    parameter int WIDTH = 8,
    parameter int ADDR_W = 4
)(
    input  logic clk,
    input  logic reset,

    input  logic start,
    input  logic [1:0] mode,

    input  logic [WIDTH-1:0] a,
    input  logic [WIDTH-1:0] b,
    input  logic [ADDR_W-1:0] mem_addr,
    input  logic [2:0] rmu_cmd,
    input  logic [ADDR_W-1:0] rmu_src_addr,

    output logic done,

    output logic [WIDTH-1:0] y,
    output logic [WIDTH-1:0] ra,
    output logic [WIDTH-1:0] rd,
    output logic [WIDTH-1:0] r0,
    output logic [WIDTH-1:0] t,

    output logic [WIDTH-1:0] fb_y,
    output logic [WIDTH-1:0] fb_ra,
    output logic [WIDTH-1:0] fb_rd,
    output logic [WIDTH-1:0] fb_r0,
    output logic [WIDTH-1:0] fb_t,

    output logic [WIDTH-1:0] out_y,
    output logic [WIDTH-1:0] out_ra,
    output logic [WIDTH-1:0] out_rd,
    output logic [WIDTH-1:0] out_r0,
    output logic [WIDTH-1:0] out_t
);

    localparam MODE_RAW        = 2'd0;
    localparam MODE_FEEDBACK   = 2'd1;
    localparam MODE_STORE_ONLY = 2'd2;
    localparam MODE_RECALL_ONLY= 2'd3;

    logic write_en;

    logic [WIDTH-1:0] prev_y;
    logic [WIDTH-1:0] prev_ra;
    logic [WIDTH-1:0] prev_rd;
    logic [WIDTH-1:0] prev_r0;
    logic [WIDTH-1:0] prev_t;

    logic [WIDTH-1:0] write_y;
    logic [WIDTH-1:0] write_ra;
    logic [WIDTH-1:0] write_rd;
    logic [WIDTH-1:0] write_r0;
    logic [WIDTH-1:0] write_t;

    // ODU relation computation
    always_comb begin
        y  = a ^ b;
        ra = ~(a ^ b);
        rd =  (a ^ b);
        r0 = ~(a | b);
        t  = rd;
    end

    ifa_relation_state_memory #(
        .WIDTH(WIDTH),
        .DEPTH(16),
        .ADDR_W(ADDR_W)
    ) rsm (
        .clk(clk),
        .reset(reset),
        .write_en(write_en),
        .write_addr(mem_addr),
        .y_in(write_y),
        .ra_in(write_ra),
        .rd_in(write_rd),
        .r0_in(write_r0),
        .t_in(write_t),
        .rmu_cmd(rmu_cmd),
        .src_addr(rmu_src_addr),
        .dst_addr(mem_addr),
        .read_addr(mem_addr),
        .y_out(prev_y),
        .ra_out(prev_ra),
        .rd_out(prev_rd),
        .r0_out(prev_r0),
        .t_out(prev_t)
    );

    ifa_relation_feedback_unit #(
        .WIDTH(WIDTH)
    ) rfu (
        .current_y(y),
        .current_ra(ra),
        .current_rd(rd),
        .current_r0(r0),
        .current_t(t),

        .prev_y(prev_y),
        .prev_ra(prev_ra),
        .prev_rd(prev_rd),
        .prev_r0(prev_r0),
        .prev_t(prev_t),

        .fb_y(fb_y),
        .fb_ra(fb_ra),
        .fb_rd(fb_rd),
        .fb_r0(fb_r0),
        .fb_t(fb_t)
    );

    always_comb begin
        case (mode)
            MODE_RAW: begin
                out_y  = y;
                out_ra = ra;
                out_rd = rd;
                out_r0 = r0;
                out_t  = t;
            end

            MODE_FEEDBACK: begin
                out_y  = fb_y;
                out_ra = fb_ra;
                out_rd = fb_rd;
                out_r0 = fb_r0;
                out_t  = fb_t;
            end

            MODE_STORE_ONLY: begin
                out_y  = y;
                out_ra = ra;
                out_rd = rd;
                out_r0 = r0;
                out_t  = t;
            end

            MODE_RECALL_ONLY: begin
                out_y  = prev_y;
                out_ra = prev_ra;
                out_rd = prev_rd;
                out_r0 = prev_r0;
                out_t  = prev_t;
            end

            default: begin
                out_y  = '0;
                out_ra = '0;
                out_rd = '0;
                out_r0 = '0;
                out_t  = '0;
            end
        endcase
    end


    always_comb begin
        case (mode)
            MODE_FEEDBACK: begin
                write_y  = fb_y;
                write_ra = fb_ra;
                write_rd = fb_rd;
                write_r0 = fb_r0;
                write_t  = fb_t;
            end

            default: begin
                write_y  = y;
                write_ra = ra;
                write_rd = rd;
                write_r0 = r0;
                write_t  = t;
            end
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            done <= 1'b0;
            write_en <= 1'b0;
        end else begin
            done <= 1'b0;
            write_en <= 1'b0;

            if (start) begin
                if (mode == MODE_RAW || mode == MODE_FEEDBACK || mode == MODE_STORE_ONLY)
                    write_en <= 1'b1;

                done <= 1'b1;
            end
        end
    end

endmodule
