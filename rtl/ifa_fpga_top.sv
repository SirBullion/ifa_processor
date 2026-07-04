module ifa_fpga_top (

    input  logic clk,
    input  logic reset,

    input  logic [7:0] sw,

    output logic [7:0] led,
    output logic led_halted,
    output logic led_error
);

    logic halted;
    logic [7:0] pc;
    logic [15:0] ir;

    logic [7:0] data_reg;
    logic [7:0] original_reg;
    logic [7:0] encoded_reg;
    logic [7:0] corrupted_reg;
    logic [7:0] recovered_reg;
    logic [7:0] error_reg;
    logic [7:0] delta_reg;
    logic [7:0] corrected_reg;
    logic [7:0] output_reg;
    logic [3:0] output_index;
    logic [127:0] output_buffer_flat;

    ifa_cpu_rom_top cpu (
        .clk(clk),
        .reset(reset),
        .halted(halted),
        .pc(pc),
        .ir(ir),
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
        .output_buffer_flat(output_buffer_flat)
    );

    assign led = output_reg;
    assign led_halted = halted;
    assign led_error = |delta_reg;

endmodule
