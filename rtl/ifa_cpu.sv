module ifa_cpu (
    input  logic clk,
    input  logic reset,

    output logic halted,
    output logic [7:0] pc,
    output logic [15:0] ir,

    output logic [7:0] data_reg,
    output logic [7:0] original_reg,
    output logic [7:0] encoded_reg,
    output logic [7:0] corrupted_reg,
    output logic [7:0] recovered_reg,
    output logic [7:0] error_reg,
    output logic [7:0] delta_reg,
    output logic [7:0] corrected_reg,
    output logic [7:0] output_reg
);

    localparam OP_NOP         = 4'h0;
    localparam OP_LOAD        = 4'h1;
    localparam OP_P8          = 4'h2;
    localparam OP_INJECT      = 4'h3;
    localparam OP_INV_CORRUPT = 4'h4;
    localparam OP_CORRECT     = 4'h5;
    localparam OP_FINAL_INV   = 4'h6;
    localparam OP_OUT         = 4'h7;
    localparam OP_HALT        = 4'hF;

    logic [15:0] imem [0:15];
    logic [3:0] opcode;
    logic [7:0] imm;

    logic [7:0] p8_out;
    logic [7:0] inv_corrupt_out;
    logic [7:0] inv_corrected_out;
    logic [7:0] error_from_delta;
    logic [7:0] delta_from_error;

    assign opcode = ir[15:12];
    assign imm    = ir[7:0];

    ifa_p8 p8_unit (
        .x(data_reg),
        .y(p8_out)
    );

    ifa_p8_inv inv_corrupt_unit (
        .y(corrupted_reg),
        .x(inv_corrupt_out)
    );

    ifa_p8_inv inv_corrected_unit (
        .y(corrected_reg),
        .x(inv_corrected_out)
    );

    ifa_t8 t_error (
        .e(error_reg),
        .delta(delta_from_error)
    );

    ifa_t8 t_delta (
        .e(delta_reg),
        .delta(error_from_delta)
    );

    initial begin
        // Program:
        // LOAD 0xA5
        // P8
        // INJECT error 0x04
        // INV corrupted
        // CORRECT
        // FINAL inverse
        // OUT
        // HALT

        imem[0]  = {OP_LOAD,        4'h0, 8'hA5};
        imem[1]  = {OP_P8,          4'h0, 8'h00};
        imem[2]  = {OP_INJECT,      4'h0, 8'h04};
        imem[3]  = {OP_INV_CORRUPT, 4'h0, 8'h00};
        imem[4]  = {OP_CORRECT,     4'h0, 8'h00};
        imem[5]  = {OP_FINAL_INV,   4'h0, 8'h00};
        imem[6]  = {OP_OUT,         4'h0, 8'h00};
        imem[7]  = {OP_HALT,        4'h0, 8'h00};

        for (int i = 8; i < 16; i++) begin
            imem[i] = {OP_NOP, 4'h0, 8'h00};
        end
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            pc            <= 8'h00;
            ir            <= 16'h0000;
            halted        <= 1'b0;

            data_reg      <= 8'h00;
            original_reg  <= 8'h00;
            encoded_reg   <= 8'h00;
            corrupted_reg <= 8'h00;
            recovered_reg <= 8'h00;
            error_reg     <= 8'h00;
            delta_reg     <= 8'h00;
            corrected_reg <= 8'h00;
            output_reg    <= 8'h00;
        end else if (!halted) begin
            ir <= imem[pc];

            case (imem[pc][15:12])

                OP_NOP: begin
                end

                OP_LOAD: begin
                    data_reg     <= imem[pc][7:0];
                    original_reg <= imem[pc][7:0];
                end

                OP_P8: begin
                    encoded_reg <= p8_out;
                    data_reg    <= p8_out;
                end

                OP_INJECT: begin
                    error_reg     <= imem[pc][7:0];
                    corrupted_reg <= encoded_reg ^ imem[pc][7:0];
                    data_reg      <= encoded_reg ^ imem[pc][7:0];
                end

                OP_INV_CORRUPT: begin
                    recovered_reg <= inv_corrupt_out;
                    delta_reg     <= original_reg ^ inv_corrupt_out;
                    data_reg      <= inv_corrupt_out;
                end

                OP_CORRECT: begin
                    corrected_reg <= corrupted_reg ^ error_from_delta;
                    data_reg      <= corrupted_reg ^ error_from_delta;
                end

                OP_FINAL_INV: begin
                    recovered_reg <= inv_corrected_out;
                    data_reg      <= inv_corrected_out;
                end

                OP_OUT: begin
                    output_reg <= data_reg;
                end

                OP_HALT: begin
                    halted <= 1'b1;
                end

            endcase

            pc <= pc + 1;
        end
    end

endmodule
