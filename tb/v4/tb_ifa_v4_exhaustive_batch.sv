`timescale 1ns/1ps

module tb_ifa_v4_exhaustive_batch;

    integer A;
    integer B;

    reg [7:0] y, ra, rd, r0, t;

    initial begin
        for (A = 0; A < 256; A = A + 1) begin
            for (B = 0; B < 256; B = B + 1) begin
                y  = (A + B) & 8'hFF;
                ra = A & B;
                rd = A ^ B;
                r0 = ~(A | B);
                t  = rd ^ y;

                $display("RESULT A=%02h B=%02h Y=%02h RA=%02h RD=%02h R0=%02h T=%02h",
                         A[7:0], B[7:0], y, ra, rd, r0, t);
            end
        end
        $finish;
    end

endmodule
