module cpu_ref_v3;

    logic clk = 0;
    always #5 clk = ~clk;

    logic [15:0] imem [0:255];

    logic [7:0] pc = 0;
    logic [15:0] ir = 0;
    logic [7:0] a_reg = 0;
    logic [7:0] b_reg = 0;
    logic [7:0] acc = 0;

    logic zero_flag = 0;

    integer cycles = 0;
    integer instr_count = 0;
    integer relation_unsupported = 0;

    initial begin
        $readmemh("odu_v2_program.hex", imem);
        $dumpfile("sim/cpu_ref_v3.vcd");
        $dumpvars(0, cpu_ref_v3);

        $display("CLASSICAL CPU REFERENCE V3+LOGIC");
        $display("-------------------------------");

        forever begin
            @(posedge clk);
            cycles++;

            ir = imem[pc];
            instr_count++;

            case (ir[15:12])

                // 0x1: LDA immediate
                4'h1: begin
                    a_reg = ir[7:0];
                    pc++;
                end

                // 0x2: LDB immediate
                4'h2: begin
                    b_reg = ir[7:0];
                    pc++;
                end

                // 0x3: AND
                4'h3: begin
                    acc = a_reg & b_reg;
                    zero_flag = (acc == 8'h00);
                    pc++;
                end

                // 0x5: XOR
                4'h5: begin
                    acc = a_reg ^ b_reg;
                    zero_flag = (acc == 8'h00);
                    pc++;
                end

                // 0x6: CMP equality compare A == B
                4'h6: begin
                    zero_flag = (a_reg == b_reg);
                    pc++;
                end

                // 0x7: BRANCH group
                // ir[11:8] = 0x0 => BEQ imm8
                // ir[11:8] = 0x1 => BNE imm8
                4'h7: begin
                    case (ir[11:8])
                        4'h0: begin
                            if (zero_flag)
                                pc = ir[7:0];
                            else
                                pc++;
                        end

                        4'h1: begin
                            if (!zero_flag)
                                pc = ir[7:0];
                            else
                                pc++;
                        end

                        default: begin
                            pc++;
                        end
                    endcase
                end

                // 0x8: ADD
                4'h8: begin
                    acc = a_reg + b_reg;
                    zero_flag = (acc == 8'h00);
                    pc++;
                end

                // 0x9: SUB
                4'h9: begin
                    acc = a_reg - b_reg;
                    zero_flag = (acc == 8'h00);
                    pc++;
                end

                // 0x4: old relation unsupported marker
                4'h4: begin
                    relation_unsupported++;
                    pc++;
                end

                // 0xF0xx: HALT
                4'hF: begin
                    if (ir[11:8] == 4'h0) begin
                        $display("HALT");
                        $display("cycles               = %0d", cycles);
                        $display("instructions         = %0d", instr_count);
                        $display("A                    = 0x%02h", a_reg);
                        $display("B                    = 0x%02h", b_reg);
                        $display("ACC                  = 0x%02h", acc);
                        $display("ZERO_FLAG            = %0d", zero_flag);
                        $display("unsupported_relation = %0d", relation_unsupported);
                        $finish;
                    end else begin
                        pc++;
                    end
                end

                default: begin
                    pc++;
                end
            endcase
        end
    end

endmodule
