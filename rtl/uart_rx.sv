module uart_rx #(
    parameter int CLKS_PER_BIT = 10
)(
    input  logic clk,
    input  logic reset,
    input  logic rx,

    output logic rx_valid,
    output logic [7:0] rx_data
);

    typedef enum logic [2:0] {
        IDLE,
        START_BIT,
        DATA_BITS,
        STOP_BIT,
        DONE
    } state_t;

    state_t state;

    logic [$clog2(CLKS_PER_BIT)-1:0] clk_count;
    logic [2:0] bit_index;
    logic [7:0] data_reg;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            rx_valid <= 1'b0;
            rx_data <= 8'h00;
            clk_count <= 0;
            bit_index <= 0;
            data_reg <= 8'h00;
        end else begin
            rx_valid <= 1'b0;

            case (state)

                IDLE: begin
                    clk_count <= 0;
                    bit_index <= 0;

                    if (rx == 1'b0)
                        state <= START_BIT;
                end

                START_BIT: begin
                    if (clk_count == (CLKS_PER_BIT/2)) begin
                        if (rx == 1'b0) begin
                            clk_count <= 0;
                            state <= DATA_BITS;
                        end else begin
                            state <= IDLE;
                        end
                    end else begin
                        clk_count <= clk_count + 1;
                    end
                end

                DATA_BITS: begin
                    if (clk_count == CLKS_PER_BIT-1) begin
                        clk_count <= 0;
                        data_reg[bit_index] <= rx;

                        if (bit_index == 7) begin
                            bit_index <= 0;
                            state <= STOP_BIT;
                        end else begin
                            bit_index <= bit_index + 1;
                        end
                    end else begin
                        clk_count <= clk_count + 1;
                    end
                end

                STOP_BIT: begin
                    if (clk_count == CLKS_PER_BIT-1) begin
                        rx_data <= data_reg;
                        rx_valid <= 1'b1;
                        clk_count <= 0;
                        state <= DONE;
                    end else begin
                        clk_count <= clk_count + 1;
                    end
                end

                DONE: begin
                    state <= IDLE;
                end

            endcase
        end
    end

endmodule
