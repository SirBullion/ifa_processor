module uart_tx #(
    parameter int CLKS_PER_BIT = 10
)(
    input  logic clk,
    input  logic reset,

    input  logic tx_start,
    input  logic [7:0] tx_data,

    output logic tx,
    output logic tx_busy,
    output logic tx_done
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
            state     <= IDLE;
            tx        <= 1'b1;
            tx_busy   <= 1'b0;
            tx_done   <= 1'b0;
            clk_count <= 0;
            bit_index <= 0;
            data_reg  <= 8'h00;
        end else begin
            tx_done <= 1'b0;

            case (state)

                IDLE: begin
                    tx <= 1'b1;
                    tx_busy <= 1'b0;
                    clk_count <= 0;
                    bit_index <= 0;

                    if (tx_start) begin
                        data_reg <= tx_data;
                        tx_busy <= 1'b1;
                        state <= START_BIT;
                    end
                end

                START_BIT: begin
                    tx <= 1'b0;

                    if (clk_count == CLKS_PER_BIT-1) begin
                        clk_count <= 0;
                        state <= DATA_BITS;
                    end else begin
                        clk_count <= clk_count + 1;
                    end
                end

                DATA_BITS: begin
                    tx <= data_reg[bit_index];

                    if (clk_count == CLKS_PER_BIT-1) begin
                        clk_count <= 0;

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
                    tx <= 1'b1;

                    if (clk_count == CLKS_PER_BIT-1) begin
                        clk_count <= 0;
                        state <= DONE;
                    end else begin
                        clk_count <= clk_count + 1;
                    end
                end

                DONE: begin
                    tx_done <= 1'b1;
                    tx_busy <= 1'b0;
                    state <= IDLE;
                end

            endcase
        end
    end

endmodule
