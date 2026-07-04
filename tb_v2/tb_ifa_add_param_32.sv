module tb_ifa_add_param_32;

    localparam WIDTH = 34;

    logic [WIDTH-1:0] A;
    logic [WIDTH-1:0] B;

    logic [WIDTH-1:0] C;
    logic [WIDTH-1:0] R_A;
    logic [WIDTH-1:0] R_D;
    logic [WIDTH-1:0] T;

    ifa_add_param #(
        .WIDTH(WIDTH)
    ) dut (
        .A(A),
        .B(B),
        .C(C),
        .R_A(R_A),
        .R_D(R_D),
        .T(T)
    );

    initial begin

        $dumpfile("sim_v2/ifa_add_param_32.vcd");
        $dumpvars(0, tb_ifa_add_param_32);

        // Largest 32-bit prime
        A = 34'd4294967311;

        // Add 1
        B = 34'd1;

        #1;

        $display("--------------------------------------------");
        $display("A   = %u", A);
        $display("B   = %u", B);
        $display("C   = %u", C);
        $display("R_A = %h", R_A);
        $display("R_D = %h", R_D);
        $display("T   = %h", T);
        $display("--------------------------------------------");

        $finish;

    end

endmodule
