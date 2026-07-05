module cpu_relation_sequential_ref #(
    parameter WIDTH = 4
)(
    input  logic             clk,
    input  logic             rst_n,
    input  logic             start,

    input  logic [WIDTH-1:0] A,
    input  logic [WIDTH-1:0] B,

    output logic             done,

    output logic [WIDTH-1:0] Y,
    output logic [WIDTH-1:0] R_A,
    output logic [WIDTH-1:0] R_D,
    output logic [WIDTH-1:0] R_0,
    output logic [WIDTH-1:0] T
);

    typedef enum logic [2:0] {
        IDLE,
        DO_ADD,
        DO_RA,
        DO_RD,
        DO_R0,
        DO_T,
        DONE
    } state_t;

    state_t state;

    logic [WIDTH-1:0] A_reg;
    logic [WIDTH-1:0] B_reg;

    logic [WIDTH:0] carry_chain;

    integer i;

    always_comb begin
        carry_chain = '0;
        carry_chain[0] = 1'b0;

        for (i = 0; i < WIDTH; i = i + 1) begin
            carry_chain[i+1] =
                (A_reg[i] & B_reg[i]) |
                ((A_reg[i] ^ B_reg[i]) & carry_chain[i]);
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            done  <= 1'b0;

            A_reg <= '0;
            B_reg <= '0;

            Y   <= '0;
            R_A <= '0;
            R_D <= '0;
            R_0 <= '0;
            T   <= '0;
        end
        else begin
            done <= 1'b0;

            case (state)
                IDLE: begin
                    if (start) begin
                        A_reg <= A;
                        B_reg <= B;
                        state <= DO_ADD;
                    end
                end

                DO_ADD: begin
                    Y <= A_reg + B_reg;
                    state <= DO_RA;
                end

                DO_RA: begin
                    R_A <= A_reg & B_reg;
                    state <= DO_RD;
                end

                DO_RD: begin
                    R_D <= A_reg ^ B_reg;
                    state <= DO_R0;
                end

                DO_R0: begin
                    R_0 <= ~(A_reg | B_reg);
                    state <= DO_T;
                end

                DO_T: begin
                    T <= carry_chain[WIDTH:1];
                    state <= DONE;
                end

                DONE: begin
                    done <= 1'b1;
                    state <= IDLE;
                end
            endcase
        end
    end

endmodule
