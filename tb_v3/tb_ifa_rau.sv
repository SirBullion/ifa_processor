`timescale 1ns/1ps

module tb_ifa_rau;

    logic [3:0] opcode;
    logic [7:0] A, B;

    logic [7:0] RESULT;
    logic CARRY_OUT;
    logic [7:0] AGREEMENT;
    logic [7:0] DISAGREEMENT;
    logic [7:0] TRANSPORT;

    ifa_rau dut (
        .opcode(opcode),
        .A(A),
        .B(B),
        .RESULT(RESULT),
        .CARRY_OUT(CARRY_OUT),
        .AGREEMENT(AGREEMENT),
        .DISAGREEMENT(DISAGREEMENT),
        .TRANSPORT(TRANSPORT)
    );

    task run_case(input [3:0] op, input [7:0] aa, input [7:0] bb);
        begin
            opcode = op;
            A = aa;
            B = bb;
            #1;

            $display(
                "OP=%0d A=%08b B=%08b RESULT=%08b CARRY=%0b AGREE=%08b DISAGREE=%08b TRANSPORT=%08b",
                opcode, A, B, RESULT, CARRY_OUT, AGREEMENT, DISAGREEMENT, TRANSPORT
            );
        end
    endtask

    initial begin
        $dumpfile("sim/ifa_rau.vcd");
        $dumpvars(0, tb_ifa_rau);

        $display("================================================================================");
        $display("IFÁ RAU TEST — Relation Arithmetic Unit");
        $display("================================================================================");

        // ADD_R = 0
        run_case(4'd0, 8'h0A, 8'h05);
        run_case(4'd0, 8'hA5, 8'h5A);
        run_case(4'd0, 8'hFF, 8'h01);

        // SUB_R = 1
        run_case(4'd1, 8'h10, 8'h01);
        run_case(4'd1, 8'hA5, 8'h05);

        // COMPARE_R = 5
        run_case(4'd5, 8'hA5, 8'hA5);
        run_case(4'd5, 8'hA5, 8'h5A);

        $display("================================================================================");
        $display("RAU test complete.");
        $finish;
    end

endmodule
