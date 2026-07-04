module tb_ifa_sub_4;

    logic [3:0] A;
    logic [3:0] B;

    logic [3:0] D;
    logic [3:0] R_A;
    logic [3:0] R_D;
    logic [3:0] T;
    logic BORROW;
    logic NO_BORROW;

    ifa_sub_4 dut (
        .A(A),
        .B(B),
        .D(D),
        .R_A(R_A),
        .R_D(R_D),
        .T(T),
        .BORROW(BORROW),
        .NO_BORROW(NO_BORROW)
    );

    initial begin
        $display(" A   B  |  D   R_A  R_D  T     BORROW NO_BORROW");
        $display("--------------------------------------------------");

        A = 4'd13; B = 4'd6;  #1;
        $display("%2d  %2d  | %b  %b  %b  %b      %b       %b",
                 A, B, D, R_A, R_D, T, BORROW, NO_BORROW);

        A = 4'd6;  B = 4'd13; #1;
        $display("%2d  %2d  | %b  %b  %b  %b      %b       %b",
                 A, B, D, R_A, R_D, T, BORROW, NO_BORROW);

        A = 4'd9;  B = 4'd9;  #1;
        $display("%2d  %2d  | %b  %b  %b  %b      %b       %b",
                 A, B, D, R_A, R_D, T, BORROW, NO_BORROW);

        A = 4'd0;  B = 4'd15; #1;
        $display("%2d  %2d  | %b  %b  %b  %b      %b       %b",
                 A, B, D, R_A, R_D, T, BORROW, NO_BORROW);

        A = 4'd15; B = 4'd0;  #1;
        $display("%2d  %2d  | %b  %b  %b  %b      %b       %b",
                 A, B, D, R_A, R_D, T, BORROW, NO_BORROW);

        $finish;
    end

endmodule

