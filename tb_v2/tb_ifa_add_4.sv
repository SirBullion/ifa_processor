module tb_ifa_add_4;

    logic [3:0] A;
    logic [3:0] B;

    logic [3:0] C;
    logic [3:0] R_A;
    logic [3:0] R_D;
    logic [3:0] T;

    ifa_add_4 dut (
        .A(A),
        .B(B),
        .C(C),
        .R_A(R_A),
        .R_D(R_D),
        .T(T)
    );

    initial begin
        $display(" A   B  |  C   R_A  R_D  T");
        $display("--------------------------------");

        A = 4'd13; B = 4'd6;  #1;
        $display("%2d  %2d  | %b  %b  %b  %b", A, B, C, R_A, R_D, T);

        A = 4'd6;  B = 4'd13; #1;
        $display("%2d  %2d  | %b  %b  %b  %b", A, B, C, R_A, R_D, T);

        A = 4'd15; B = 4'd1;  #1;
        $display("%2d  %2d  | %b  %b  %b  %b", A, B, C, R_A, R_D, T);

        A = 4'd7;  B = 4'd8;  #1;
        $display("%2d  %2d  | %b  %b  %b  %b", A, B, C, R_A, R_D, T);

        A = 4'd0;  B = 4'd0;  #1;
        $display("%2d  %2d  | %b  %b  %b  %b", A, B, C, R_A, R_D, T);

        $finish;
    end

endmodule
