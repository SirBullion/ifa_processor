module ifa_relation_pattern_encoder #(
    parameter WIDTH = 4
)(
    input  logic [WIDTH-1:0] Y,
    input  logic [WIDTH-1:0] R_A,
    input  logic [WIDTH-1:0] R_D,
    input  logic [WIDTH-1:0] R_0,
    input  logic [WIDTH-1:0] T,

    output logic [1:0]       mode,
    output logic             compressed_valid,

    output logic [WIDTH-1:0] Y_store,
    output logic [WIDTH-1:0] R_primary,
    output logic [WIDTH-1:0] R_secondary,
    output logic [WIDTH-1:0] R_delta
);

    localparam MODE_FULL        = 2'b00;
    localparam MODE_DELAY_SHARE = 2'b01; // R_D = R_0 = T
    localparam MODE_RA_RD_SHARE = 2'b10; // R_A = R_D
    localparam MODE_DELTA       = 2'b11; // Store delta relation

    always_comb begin
        Y_store          = Y;
        mode             = MODE_FULL;
        compressed_valid = 1'b0;

        R_primary   = R_A;
        R_secondary = R_D;
        R_delta     = R_A ^ R_D;

        // Mode 1: barrel-delay deduplication
        if ((R_D == R_0) && (R_0 == T)) begin
            mode             = MODE_DELAY_SHARE;
            compressed_valid = 1'b1;

            R_primary   = R_A;
            R_secondary = R_D;
            R_delta     = '0;
        end

        // Mode 2: Agreement and Disagreement are identical
        else if (R_A == R_D) begin
            mode             = MODE_RA_RD_SHARE;
            compressed_valid = 1'b1;

            R_primary   = R_A;
            R_secondary = R_0;
            R_delta     = T;
        end

        // Mode 3: Delta encoding is useful when relation delta is sparse
        else if ($countones(R_A ^ R_D) <= (WIDTH / 2)) begin
            mode             = MODE_DELTA;
            compressed_valid = 1'b1;

            R_primary   = R_A;
            R_secondary = R_0;
            R_delta     = R_A ^ R_D;
        end
    end

endmodule
