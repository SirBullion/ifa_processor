`timescale 1ns/1ps

module tb_ifa_rpc;

    logic [3:0] op;
    logic [7:0] A, B;

    logic [7:0] result;
    logic carry_borrow;
    logic eq, gt, lt;

    logic [7:0] ra, rd, r1, r0, a_over_b, b_over_a;

    ifa_rpc dut (
        .op(op),
        .A(A),
        .B(B),
        .result(result),
        .carry_borrow(carry_borrow),
        .eq(eq),
        .gt(gt),
        .lt(lt),
        .ra(ra),
        .rd(rd),
        .r1(r1),
        .r0(r0),
        .a_over_b(a_over_b),
        .b_over_a(b_over_a)
    );

    task run_case(input [3:0] oo, input [7:0] aa, input [7:0] bb);
        begin
            op = oo;
            A = aa;
            B = bb;
            #1;

            $display(
                "OP=%0d A=%02h B=%02h RESULT=%02h CB=%0b EQ=%0b GT=%0b LT=%0b RA=%02h RD=%02h R1=%02h R0=%02h A>B=%02h B>A=%02h",
                op, A, B, result, carry_borrow, eq, gt, lt,
                ra, rd, r1, r0, a_over_b, b_over_a
            );
        end
    endtask

    initial begin
        $dumpfile("sim/ifa_rpc.vcd");
        $dumpvars(0, tb_ifa_rpc);

        $display("============================================================");
        $display("IFÁ RPC TEST");
        $display("============================================================");

        // ADD
        run_case(4'd0, 8'h0A, 8'h05);
        run_case(4'd0, 8'hFF, 8'h01);
        run_case(4'd0, 8'hA5, 8'h5A);

        // SUB
        run_case(4'd1, 8'h10, 8'h01);
        run_case(4'd1, 8'h00, 8'h01);
        run_case(4'd1, 8'hA5, 8'h05);

        // COMPARE
        run_case(4'd2, 8'hA5, 8'hA5);
        run_case(4'd2, 8'hA5, 8'h5A);
        run_case(4'd2, 8'h33, 8'h55);

        $display("============================================================");
        $display("RPC test complete.");
        $finish;
    end

endmodule
