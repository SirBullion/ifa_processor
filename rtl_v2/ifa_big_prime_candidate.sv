module ifa_big_prime_candidate #(
    parameter int EXP_WIDTH = 32
)(
    input  logic [EXP_WIDTH-1:0] p,      // exponent
    input  logic [31:0] delta,           // even offset

    output logic [EXP_WIDTH-1:0] exponent,
    output logic [31:0]          offset,
    output logic                 valid_delta,
    output logic                 beats_record
);

    // Candidate represented symbolically:
    // candidate = 2^p - 1 + delta
    //
    // We do NOT expand the 41-million-digit number in hardware.
    // We store the mathematical form safely.

    localparam logic [EXP_WIDTH-1:0] RECORD_EXP = 32'd136279841;

    assign exponent = p;
    assign offset   = delta;

    // To stay odd:
    // 2^p - 1 is odd, so delta must be even.
    assign valid_delta = (delta[0] == 1'b0);

    // Candidate is larger than the current record if:
    // p > record exponent
    // or p == record exponent and delta > 0
    assign beats_record =
        (p > RECORD_EXP) ||
        ((p == RECORD_EXP) && (delta > 32'd0));

endmodule
