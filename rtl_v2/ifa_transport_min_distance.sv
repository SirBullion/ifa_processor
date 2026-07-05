module ifa_transport_min_distance #(
    parameter WIDTH = 4
)(
    input  logic [WIDTH-1:0] A,
    input  logic [WIDTH-1:0] B,
    output logic [WIDTH-1:0] T
);

    logic [WIDTH-1:0] diff_abs;
    logic [WIDTH-1:0] diff_wrap;

    always_comb begin
        if (A >= B)
            diff_abs = A - B;
        else
            diff_abs = B - A;

        diff_wrap = (1 << WIDTH) - diff_abs;

        if (diff_abs <= diff_wrap)
            T = diff_abs;
        else
            T = diff_wrap;
    end

endmodule
