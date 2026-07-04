module tb_ifa_compare_4;

    logic [3:0] A;
    logic [3:0] B;

    logic [3:0] R_D;
    logic       EQ;
    logic       GT;
    logic       LT;

    logic [3:0] D;
    logic [3:0] T;

    ifa_compare_4 dut (
        .A(A),
        .B(B),
        .R_D(R_D),
        .EQ(EQ),
        .GT(GT),
        .LT(LT),
        .D(D),
        .T(T)
    );

    initial begin

        $display("");
        $display(" A   B |   D    R_D    T   EQ GT LT");
        $display("--------------------------------------");

        A = 4'd13; B = 4'd6;  #1;
        $display("%2d %2d | %b %b %b  %b  %b  %b",
                 A,B,D,R_D,T,EQ,GT,LT);

        A = 4'd6;  B = 4'd13; #1;
        $display("%2d %2d | %b %b %b  %b  %b  %b",
                 A,B,D,R_D,T,EQ,GT,LT);

        A = 4'd9;  B = 4'd9;  #1;
        $display("%2d %2d | %b %b %b  %b  %b  %b",
                 A,B,D,R_D,T,EQ,GT,LT);

        A = 4'd0;  B = 4'd15; #1;
        $display("%2d %2d | %b %b %b  %b  %b  %b",
                 A,B,D,R_D,T,EQ,GT,LT);

        A = 4'd15; B = 4'd0;  #1;
        $display("%2d %2d | %b %b %b  %b  %b  %b",
                 A,B,D,R_D,T,EQ,GT,LT);

        $finish;

    end

endmodule
