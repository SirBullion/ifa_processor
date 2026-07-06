module ifa_relation_state_memory #(
    parameter int WIDTH = 8,
    parameter int DEPTH = 16,
    parameter int ADDR_W = 4
)(
    input  logic clk,
    input  logic reset,

    input  logic write_en,
    input  logic [ADDR_W-1:0] write_addr,
    input  logic [WIDTH-1:0] y_in,
    input  logic [WIDTH-1:0] ra_in,
    input  logic [WIDTH-1:0] rd_in,
    input  logic [WIDTH-1:0] r0_in,
    input  logic [WIDTH-1:0] t_in,

    input  logic [2:0] rmu_cmd,
    input  logic [ADDR_W-1:0] src_addr,
    input  logic [ADDR_W-1:0] dst_addr,

    input  logic [ADDR_W-1:0] read_addr,

    output logic [WIDTH-1:0] y_out,
    output logic [WIDTH-1:0] ra_out,
    output logic [WIDTH-1:0] rd_out,
    output logic [WIDTH-1:0] r0_out,
    output logic [WIDTH-1:0] t_out
);

    localparam RMU_NONE  = 3'd0;
    localparam RMU_CLEAR = 3'd1;
    localparam RMU_COPY  = 3'd2;
    localparam RMU_MOVE  = 3'd3;
    localparam RMU_SWAP  = 3'd4;

    logic [WIDTH-1:0] y_mem  [0:DEPTH-1];
    logic [WIDTH-1:0] ra_mem [0:DEPTH-1];
    logic [WIDTH-1:0] rd_mem [0:DEPTH-1];
    logic [WIDTH-1:0] r0_mem [0:DEPTH-1];
    logic [WIDTH-1:0] t_mem  [0:DEPTH-1];

    integer i;

    always_ff @(posedge clk) begin
        if (reset) begin
            for (i = 0; i < DEPTH; i++) begin
                y_mem[i]  <= '0;
                ra_mem[i] <= '0;
                rd_mem[i] <= '0;
                r0_mem[i] <= '0;
                t_mem[i]  <= '0;
            end
        end else begin
            case (rmu_cmd)
                RMU_CLEAR: begin
                    y_mem[dst_addr]  <= '0;
                    ra_mem[dst_addr] <= '0;
                    rd_mem[dst_addr] <= '0;
                    r0_mem[dst_addr] <= '0;
                    t_mem[dst_addr]  <= '0;
                end

                RMU_COPY: begin
                    y_mem[dst_addr]  <= y_mem[src_addr];
                    ra_mem[dst_addr] <= ra_mem[src_addr];
                    rd_mem[dst_addr] <= rd_mem[src_addr];
                    r0_mem[dst_addr] <= r0_mem[src_addr];
                    t_mem[dst_addr]  <= t_mem[src_addr];
                end

                RMU_MOVE: begin
                    y_mem[dst_addr]  <= y_mem[src_addr];
                    ra_mem[dst_addr] <= ra_mem[src_addr];
                    rd_mem[dst_addr] <= rd_mem[src_addr];
                    r0_mem[dst_addr] <= r0_mem[src_addr];
                    t_mem[dst_addr]  <= t_mem[src_addr];

                    y_mem[src_addr]  <= '0;
                    ra_mem[src_addr] <= '0;
                    rd_mem[src_addr] <= '0;
                    r0_mem[src_addr] <= '0;
                    t_mem[src_addr]  <= '0;
                end

                RMU_SWAP: begin
                    y_mem[dst_addr]  <= y_mem[src_addr];
                    ra_mem[dst_addr] <= ra_mem[src_addr];
                    rd_mem[dst_addr] <= rd_mem[src_addr];
                    r0_mem[dst_addr] <= r0_mem[src_addr];
                    t_mem[dst_addr]  <= t_mem[src_addr];

                    y_mem[src_addr]  <= y_mem[dst_addr];
                    ra_mem[src_addr] <= ra_mem[dst_addr];
                    rd_mem[src_addr] <= rd_mem[dst_addr];
                    r0_mem[src_addr] <= r0_mem[dst_addr];
                    t_mem[src_addr]  <= t_mem[dst_addr];
                end

                default: begin
                    if (write_en) begin
                        y_mem[write_addr]  <= y_in;
                        ra_mem[write_addr] <= ra_in;
                        rd_mem[write_addr] <= rd_in;
                        r0_mem[write_addr] <= r0_in;
                        t_mem[write_addr]  <= t_in;
                    end
                end
            endcase
        end
    end

    assign y_out  = y_mem[read_addr];
    assign ra_out = ra_mem[read_addr];
    assign rd_out = rd_mem[read_addr];
    assign r0_out = r0_mem[read_addr];
    assign t_out  = t_mem[read_addr];

endmodule
