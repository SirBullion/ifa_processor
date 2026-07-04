module ifa_cpu_rom_top (
    input  logic clk,
    input  logic reset,

    output logic halted,
    output logic [9:0] pc,
    output logic [15:0] ir,

    output logic [7:0] data_reg,
    output logic [7:0] original_reg,
    output logic [7:0] encoded_reg,
    output logic [7:0] corrupted_reg,
    output logic [7:0] recovered_reg,
    output logic [7:0] error_reg,
    output logic [7:0] delta_reg,
    output logic [7:0] corrected_reg,
    output logic [7:0] output_reg,
    output logic [3:0] output_index,
    output logic [127:0] output_buffer_flat,
    output logic out_valid,
    output logic [7:0] out_byte
);

    logic [15:0] instr;

    ifa_rom rom (
        .addr(pc),
        .instr(instr)
    );

    ifa_cpu_core core (
        .clk(clk),
        .reset(reset),
        .instr_in(instr),

        .pc(pc),
        .ir(ir),
        .halted(halted),

        .data_reg(data_reg),
        .original_reg(original_reg),
        .encoded_reg(encoded_reg),
        .corrupted_reg(corrupted_reg),
        .recovered_reg(recovered_reg),
        .error_reg(error_reg),
        .delta_reg(delta_reg),
        .corrected_reg(corrected_reg),
        .output_reg(output_reg),
        .output_index(output_index),
        .output_buffer_flat(output_buffer_flat),
        .out_valid(out_valid),
        .out_byte(out_byte)
    );

endmodule
