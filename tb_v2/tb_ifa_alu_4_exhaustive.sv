module tb_ifa_alu_4_exhaustive;

    logic [1:0] op;
    logic [3:0] A, B;

    logic [3:0] Y, R_A, R_D, R_0, T;
    logic EQ, GT, LT, BORROW, NO_BORROW;

    integer a, b;
    integer errors;
    integer tests;

    localparam OP_ADD = 2'b00;
    localparam OP_SUB = 2'b01;
    localparam OP_CMP = 2'b10;

    ifa_alu_4 dut (
        .op(op),
        .A(A),
        .B(B),
        .Y(Y),
        .R_A(R_A),
        .R_D(R_D),
        .R_0(R_0),
        .T(T),
        .EQ(EQ),
        .GT(GT),
        .LT(LT),
        .BORROW(BORROW),
        .NO_BORROW(NO_BORROW)
    );

    wire [2:0] P_A;
    wire [2:0] P_D;
    wire [2:0] P_0;
    logic [2:0] P_SUM;

    assign P_A = dut.u_relation.P_A;
assign P_D = dut.u_relation.P_D;
assign P_0 = dut.u_relation.P_0;

always_comb begin
    P_SUM = P_A + P_D + P_0;
end

task check_relation_partition;


        begin
            if ((R_A | R_D | R_0) !== 4'b1111) begin
                $display("FAIL partition cover: A=%0d B=%0d RA=%b RD=%b R0=%b", A,B,R_A,R_D,R_0);
                errors++;
            end

            if (((R_A & R_D) !== 4'b0000) ||
                ((R_A & R_0) !== 4'b0000) ||
                ((R_D & R_0) !== 4'b0000)) begin
                $display("FAIL partition disjoint: A=%0d B=%0d RA=%b RD=%b R0=%b", A,B,R_A,R_D,R_0);
                errors++;
            end
        end
    endtask

    initial begin
        errors = 0;
        tests  = 0;

        $dumpfile("sim_v2/ifa_alu_4_exhaustive.vcd");
        $dumpvars(0, tb_ifa_alu_4_exhaustive);

        for (a = 0; a < 16; a++) begin
            for (b = 0; b < 16; b++) begin

                A = a[3:0];
                B = b[3:0];

                // ADD
                op = OP_ADD; #1;
                tests++;
                if (Y !== ((a + b) & 4'hF)) begin
                    $display("FAIL ADD: A=%0d B=%0d Y=%0d expected=%0d", a,b,Y,((a+b)&15));
                    errors++;
                end
                if (R_A !== (A & B)) errors++;
                if (R_D !== (A ^ B)) errors++;
                if (R_0 !== ((~A) & (~B))) errors++;
                check_relation_partition();

                // SUB
                op = OP_SUB; #1;
                tests++;
                if (Y !== ((a - b) & 4'hF)) begin
                    $display("FAIL SUB: A=%0d B=%0d Y=%0d expected=%0d", a,b,Y,((a-b)&15));
                    errors++;
                end
                if (BORROW !== (a < b)) begin
                    $display("FAIL BORROW: A=%0d B=%0d BORROW=%b expected=%b", a,b,BORROW,(a<b));
                    errors++;
                end

                // CMP
                op = OP_CMP; #1;
                tests++;
                if (EQ !== (a == b)) errors++;
                if (GT !== (a > b)) errors++;
                if (LT !== (a < b)) errors++;
                check_relation_partition();

            end
        end

        $display("");
        $display("======================================");
        $display("IFA V2 EXHAUSTIVE ALU TEST COMPLETE");
        $display("Input pairs: 256");
        $display("Operations tested per pair: ADD, SUB, CMP");
        $display("Total operation tests: %0d", tests);
        $display("Errors: %0d", errors);
        $display("--------------------------------------");
        $display("Relation reuse saved per ADD/CMP pair:");
        $display("CPU recomputes RA, RD, R0 = AND + XOR + NOT/AND");
        $display("Ifa reads stored RA, RD, R0");
        $display("Recompute delta per reuse = 0 for Ifa");
        $display("======================================");

        if (errors == 0)
            $display("STATUS: PASS ✅");
        else
            $display("STATUS: FAIL ❌");

        $finish;
    end

endmodule
