module ifa_relation_compressor #(
    parameter WIDTH = 4
)(
    input  logic [WIDTH-1:0] Y,
    input  logic [WIDTH-1:0] R_A,
    input  logic [WIDTH-1:0] R_D,
    input  logic [WIDTH-1:0] R_0,
    input  logic [WIDTH-1:0] T,

    output logic             compressed_valid,
    output logic [1:0]       mode,

    output logic [WIDTH-1:0] Y_store,
    output logic [WIDTH-1:0] R_primary,
    output logic [WIDTH-1:0] R_delay
);

    localparam MODE_FULL       = 2'b00;
    localparam MODE_BARREL_CMP = 2'b01;

    always_comb begin
        Y_store = Y;

        compressed_valid = 1'b0;
        mode             = MODE_FULL;

        R_primary = R_A;
        R_delay   = R_D;

        // Compress when barrel states duplicate
        if ((R_D == R_0) && (R_0 == T)) begin
            compressed_valid = 1'b1;
            mode             = MODE_BARREL_CMP;

            // Store active relation and one shared delayed relation
            R_primary = R_A;
            R_delay   = R_D;
        end
    end

endmodule
