module ifa_rmu_compression_logic_only #(
    parameter WIDTH = 4
)(
    input  logic [WIDTH-1:0] R_A,
    input  logic [WIDTH-1:0] R_D,
    input  logic [WIDTH-1:0] R_0,
    input  logic [WIDTH-1:0] T,

    output logic             compressed_valid,
    output logic [1:0]       mode
);

    localparam MODE_FULL        = 2'b00;
    localparam MODE_DELAY_SHARE = 2'b01;
    localparam MODE_RA_RD_SHARE = 2'b10;
    localparam MODE_DELTA       = 2'b11;

    logic [WIDTH-1:0] delta;
    logic [$clog2(WIDTH+1)-1:0] delta_pop;

    assign delta = R_A ^ R_D;

    always_comb begin
        delta_pop = $countones(delta);

        compressed_valid = 1'b0;
        mode = MODE_FULL;

        if ((R_D == R_0) && (R_0 == T)) begin
            compressed_valid = 1'b1;
            mode = MODE_DELAY_SHARE;
        end
        else if (R_A == R_D) begin
            compressed_valid = 1'b1;
            mode = MODE_RA_RD_SHARE;
        end
        else if (delta_pop <= (WIDTH / 2)) begin
            compressed_valid = 1'b1;
            mode = MODE_DELTA;
        end
    end

endmodule
