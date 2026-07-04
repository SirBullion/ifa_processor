module tb_ifa_relation_4;

    logic [3:0] A, B;
    logic [3:0] R_A, R_D, R_0;
    logic [3:0] COVER;
    logic       DISJOINT_OK;

    ifa_relation_4 dut (
        .A(A),
        .B(B),
        .R_A(R_A),
        .R_D(R_D),
        .R_0(R_0)
    );

    assign COVER =
        R_A | R_D | R_0;

    assign DISJOINT_OK =
        ((R_A & R_D) == 4'b0000) &&
        ((R_A & R_0) == 4'b0000) &&
        ((R_D & R_0) == 4'b0000);

    initial begin
        $display(" A   B | R_A  R_D  R_0 | COVER DISJOINT");
        $display("-----------------------------------------");

        A = 4'd13; B = 4'd6;  #1;
        $display("%2d %2d | %b %b %b |  %b     %b",
                 A,B,R_A,R_D,R_0,COVER,DISJOINT_OK);

        A = 4'd6;  B = 4'd13; #1;
        $display("%2d %2d | %b %b %b |  %b     %b",
                 A,B,R_A,R_D,R_0,COVER,DISJOINT_OK);

        A = 4'd9;  B = 4'd9;  #1;
        $display("%2d %2d | %b %b %b |  %b     %b",
                 A,B,R_A,R_D,R_0,COVER,DISJOINT_OK);

        A = 4'd0;  B = 4'd15; #1;
        $display("%2d %2d | %b %b %b |  %b     %b",
                 A,B,R_A,R_D,R_0,COVER,DISJOINT_OK);

        A = 4'd0;  B = 4'd0;  #1;
        $display("%2d %2d | %b %b %b |  %b     %b",
                 A,B,R_A,R_D,R_0,COVER,DISJOINT_OK);

        A = 4'd15; B = 4'd15; #1;
        $display("%2d %2d | %b %b %b |  %b     %b",
                 A,B,R_A,R_D,R_0,COVER,DISJOINT_OK);

        $finish;
    end

endmodule
