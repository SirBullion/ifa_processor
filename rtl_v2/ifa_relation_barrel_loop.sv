module ifa_relation_barrel_loop #(
    parameter WIDTH = 4
)(
    input  logic                 clk,
    input  logic                 rst_n,
    input  logic                 shift_en,

    // Fresh relation from ODU
    input  logic [WIDTH-1:0]     odu_new_ra,

    // Fixed low-latency output
    output logic [WIDTH-1:0]     Y_rel,

    // Debug
    output logic [WIDTH-1:0]     R_A_mem,
    output logic [WIDTH-1:0]     R_D_mem,
    output logic [WIDTH-1:0]     T_mem,
    output logic [WIDTH-1:0]     R_0_mem
);

    //-------------------------------------------------
    // No multiplexer
    //-------------------------------------------------

    assign Y_rel = R_A_mem;

    //-------------------------------------------------
    // Structural Barrel Loop
    //-------------------------------------------------

    always_ff @(posedge clk or negedge rst_n) begin

        if(!rst_n) begin

            R_A_mem <= 4'h4;
            R_D_mem <= 4'hB;
            T_mem   <= 4'hC;
            R_0_mem <= 4'h0;

        end

        else if(shift_en) begin

            logic [WIDTH-1:0] next_RA;

            next_RA = R_D_mem ^ odu_new_ra;

            R_0_mem <= R_A_mem;
            T_mem   <= R_0_mem;
            R_D_mem <= T_mem;
            R_A_mem <= next_RA;

        end

    end

endmodule
