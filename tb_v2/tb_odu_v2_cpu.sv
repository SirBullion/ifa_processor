`timescale 1ns/1ps


module tb_odu_v2_cpu;

    function automatic [255:0] oju_odu_name(input [7:0] v);
        begin
            case(v[3:0])
                4'h0: oju_odu_name = "ÒGBÈ";
                4'h1: oju_odu_name = "ÒYÈKÚ";
                4'h2: oju_odu_name = "ÌWÒRÌ";
                4'h3: oju_odu_name = "ÒDÍ";
                4'h4: oju_odu_name = "ÌRÒSÙN";
                4'h5: oju_odu_name = "ÒWÓNRÍN";
                4'h6: oju_odu_name = "ÒBÀRÀ";
                4'h7: oju_odu_name = "ÒKÀNRÀN";
                4'h8: oju_odu_name = "ÒGÚNDÁ";
                4'h9: oju_odu_name = "ÒSÁ";
                4'hA: oju_odu_name = "ÌKÁ";
                4'hB: oju_odu_name = "ÒTÚRÚPỌ̀N";
                4'hC: oju_odu_name = "ÒTÚRÁ";
                4'hD: oju_odu_name = "ÌRẸ̀TẸ̀";
                4'hE: oju_odu_name = "ÒṢÉ";
                4'hF: oju_odu_name = "ÒFÚN";
                default: oju_odu_name = "UNKNOWN";
            endcase
        end
    endfunction



    logic clk = 0;
    logic reset = 1;
    logic halted;

    logic [7:0] a_reg;
    logic [7:0] b_reg;
    logic [3:0] addr_reg;

    logic [7:0] out_y, out_ra, out_rd, out_r0, out_t;

    int cycle = 0;

    always #5 clk = ~clk;

    ifa_odu_v2_cpu dut (
        .clk(clk),
        .reset(reset),
        .halted(halted),
        .a_reg(a_reg),
        .b_reg(b_reg),
        .addr_reg(addr_reg),
        .out_y(out_y),
        .out_ra(out_ra),
        .out_rd(out_rd),
        .out_r0(out_r0),
        .out_t(out_t)
    );

    function string instr_name(input logic [15:0] ir);
        case (ir[15:12])
            4'h0: begin
                case (ir[11:8])
                    4'h1: instr_name = "BR_EQ";
                    4'h2: instr_name = "BR_GT";
                    4'h3: instr_name = "BR_LT";
                    4'h4: instr_name = "JMP";
                    default: instr_name = "NOP";
                endcase
            end
            4'h1: instr_name = "LOADA";
            4'h2: instr_name = "LOADB";
            4'h3: instr_name = "ADDR";
            4'h4: instr_name = "ODU_RAW";
            4'h5: instr_name = "ODU_FEEDBACK";
            4'h6: instr_name = "ODU_STORE";
            4'h7: instr_name = "ODU_RECALL";
            4'h8: instr_name = "RPC_ADD";
            4'h9: instr_name = "RPC_SUB";
            4'hA: instr_name = "RPC_COMPARE";
            4'hB: instr_name = "RMU_CLEAR";
            4'hC: instr_name = "RMU_COPY";
            4'hD: instr_name = "RMU_MOVE";
            4'hE: instr_name = "RMU_SWAP";
            4'hF: begin
                case (ir[11:8])
                    4'h1: instr_name = "CALL";
                    4'h2: instr_name = "RET";
                    4'h3: instr_name = "PUSH";
                    4'h4: instr_name = "POP";
                    4'h5: instr_name = "RPUSH";
                    4'h6: instr_name = "RPOP";
                    4'h7: instr_name = "PRINTY";
                    4'h8: instr_name = "PRINTRA";
                    4'h9: instr_name = "PRINTRD";
                    4'hA: instr_name = "PRINTR0";
                    4'hB: instr_name = "PRINTT";
                    4'hC: instr_name = "PRINTA";
                    4'hD: instr_name = "PRINTB";
                    4'hE: instr_name = "PRINTPC";
                    4'hF: instr_name = "PRINTIR";
                    default: instr_name = "HALT";
                endcase
            end
            default: instr_name = "UNKNOWN";
        endcase
    endfunction


task automatic print_oju_odu(input [7:0] v);
    begin
        case (v[3:0])
            4'h0: $display("%02h  ÒGBÈ", v);
            4'h1: $display("%02h  ÒYÈKÚ", v);
            4'h2: $display("%02h  ÌWÒRÌ", v);
            4'h3: $display("%02h  ÒDÍ", v);
            4'h4: $display("%02h  ÌRÒSÙN", v);
            4'h5: $display("%02h  ÒWÓNRÍN", v);
            4'h6: $display("%02h  ÒBÀRÀ", v);
            4'h7: $display("%02h  ÒKÀNRÀN", v);
            4'h8: $display("%02h  ÒGÚNDÁ", v);
            4'h9: $display("%02h  ÒSÁ", v);
            4'hA: $display("%02h  ÌKÁ", v);
            4'hB: $display("%02h  ÒTÚRÚPỌ̀N", v);
            4'hC: $display("%02h  ÒTÚRÁ", v);
            4'hD: $display("%02h  ÌRẸ̀TẸ̀", v);
            4'hE: $display("%02h  ÒṢÉ", v);
            4'hF: $display("%02h  ÒFÚN", v);
        endcase
    end
endtask

    initial begin
        $dumpfile("sim/odu_v2_cpu.vcd");
        $dumpvars(0, tb_odu_v2_cpu);

        #20;
        reset = 0;

        $display("cycle pc state ir    instr        csp cret fsp fy fra frd fr0 ft          A        B        addr OUT_Y    OUT_RA   OUT_RD   OUT_R0   OUT_T");
        $display("------------------------------------------------------------------------------------------------");
        // DÁIFÁ banner now belongs to the Python monitor, not every CPU trace.

        while (!halted && cycle < 200) begin
            @(posedge clk);
            cycle++;
            #1;


            if (dut.print_valid) begin
                case (dut.ir[11:8])
                    4'h7: begin
                        if (dut.print_data <= 8'h0F)
                            print_oju_odu(dut.print_data);
                        else
                            $display(">>> PRINTY  = %02h (%0d)", dut.print_data, dut.print_data);
                    end
                    4'h8: $display(">>> PRINTRA = %02h (%0d)  %s", dut.print_data, dut.print_data, oju_odu_name(dut.print_data));
                    4'h9: $display(">>> PRINTRD = %02h (%0d)  %s", dut.print_data, dut.print_data, oju_odu_name(dut.print_data));
                    4'hA: $display(">>> PRINTR0 = %02h (%0d)  %s", dut.print_data, dut.print_data, oju_odu_name(dut.print_data));
                    4'hB: $display(">>> PRINTT  = %02h (%0d)  %s", dut.print_data, dut.print_data, oju_odu_name(dut.print_data));
                    4'hC: $display(">>> PRINTA  = %02h (%0d)", dut.print_data, dut.print_data);
                    4'hD: $display(">>> PRINTB  = %02h (%0d)", dut.print_data, dut.print_data);
                    4'hE: $display(">>> PRINTPC = %02h (%0d)", dut.print_data, dut.print_data);
                    4'hF: $display(">>> PRINTIR = %02h (%0d)", dut.print_data, dut.print_data);
                    default: $display(">>> PRINT   = %02h (%0d)", dut.print_data, dut.print_data);
                endcase
            end

            $display(
                "%5d %02h %0d %04h  %-13s %0d  %02h  %0d  %02h %02h %02h %02h %02h %08b %08b %0d    %08b %08b %08b %08b %08b",
                cycle,
                dut.pc,
                dut.state,
                dut.ir,
                instr_name(dut.ir),
                dut.call_stack0.sp,
                dut.call_return_pc,
                dut.frame_stack0.sp,
                dut.frame_y,
                dut.frame_ra,
                dut.frame_rd,
                dut.frame_r0,
                dut.frame_t,
                a_reg,
                b_reg,
                addr_reg,
                out_y,
                out_ra,
                out_rd,
                out_r0,
                out_t
            );
        end

        $display("------------------------------------------------------------------------------------------------");
        $display("ODU V2 CPU halted after %0d cycles.", cycle);
        $finish;
    end

endmodule
