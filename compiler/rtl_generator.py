import re


class SystemVerilogGenerator:
    def generate(self, program, design_name="ifa_program"):
        sections = [self.module(design_name + "_main", program.instructions)]
        for function in program.functions.values():
            name = design_name + "_" + function.name.lower().replace(".", "_")
            sections.append(self.module(name, function.instructions))
        return "\n\n".join(sections) + "\n"

    @staticmethod
    def safe_name(name):
        value = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        return value if not value[:1].isdigit() else "ifa_" + value

    def module(self, name, instructions):
        name = self.safe_name(name)
        labels = {i.operands[0]: n for n, i in enumerate(instructions) if i.opcode == "LABEL"}
        registers = sorted({operand for ins in instructions for operand in self.flatten(ins.operands) if isinstance(operand, str) and re.fullmatch(r"r\d+", operand)}, key=lambda r: int(r[1:]))
        variables = sorted({ins.operands[0] for ins in instructions if ins.opcode == "STORE"})
        reg_index = {register: index for index, register in enumerate(registers)}
        var_index = {variable: index for index, variable in enumerate(variables)}
        width = max(1, (max(1, len(instructions)) - 1).bit_length())
        lines = [
            f"module {name}(",
            "    input logic clk, input logic reset, input logic start,",
            "    output logic done, output logic signed [63:0] result,",
            "    output logic call_valid, output logic [31:0] call_target,",
            "    output logic signed [63:0] call_arg0, call_arg1,",
            "    input logic call_done, input logic signed [63:0] call_result",
            ");",
            f"logic [{width - 1}:0] state;",
            f"logic signed [63:0] regs [0:{max(0, len(registers) - 1)}];",
            f"logic signed [63:0] vars [0:{max(0, len(variables) - 1)}];",
            "always_ff @(posedge clk) begin",
            "  if (reset) begin state <= '0; done <= 1'b0; result <= '0; call_valid <= 1'b0; end",
            "  else if (start && !done) begin",
            "    case (state)",
        ]
        for index, instruction in enumerate(instructions):
            lines.append(f"      {width}'d{index}: begin")
            lines.extend("        " + line for line in self.emit(instruction, index, labels, reg_index, var_index))
            lines.append("      end")
        lines.extend(["      default: begin done <= 1'b1; end", "    endcase", "  end", "end", "endmodule"])
        return "\n".join(lines)

    def emit(self, instruction, index, labels, registers, variables):
        op, a = instruction.opcode, instruction.operands
        nxt = f"state <= state + 1'b1;"
        reg = lambda value: f"regs[{registers[value]}]"
        val = lambda value: reg(value) if value in registers else str(int(value or 0))
        if op == "LOAD_CONST" and isinstance(a[1], (int, float, bool)): return [f"{reg(a[0])} <= 64'sd{int(a[1])};", nxt]
        if op == "LOAD": return [f"{reg(a[0])} <= vars[{variables.get(a[1], 0)}];", nxt]
        if op == "STORE": return [f"vars[{variables[a[0]]}] <= {val(a[1])};", nxt]
        binary = {"ADD":"+", "SUB":"-", "MUL":"*", "DIV":"/", "MOD":"%", "CMP_EQ":"==", "CMP_GT":">", "CMP_LT":"<"}
        if op in binary: return [f"{reg(a[0])} <= {val(a[1])} {binary[op]} {val(a[2])};", nxt]
        if op == "JUMP": return [f"state <= {len(bin(max(1,len(labels))))}'d{labels[a[0]]};"]
        if op == "JUMP_IF_FALSE": return [f"if (!{val(a[0])}) state <= {labels[a[1]]}; else state <= state + 1'b1;"]
        if op == "LABEL": return [nxt]
        if op == "CALL": return ["call_valid <= 1'b1;", f"call_target <= 32'h{abs(hash(a[1])) & 0xffffffff:08x};", f"call_arg0 <= {val(a[2][0]) if a[2] else '0'};", f"call_arg1 <= {val(a[2][1]) if len(a[2]) > 1 else '0'};", f"if (call_done) begin {reg(a[0])} <= call_result; call_valid <= 1'b0; state <= state + 1'b1; end"]
        if op == "RETURN": return [f"result <= {val(a[0]) if a[0] else '0'};", "done <= 1'b1;"]
        if op == "HALT": return ["done <= 1'b1;"]
        return [nxt]

    def flatten(self, values):
        for value in values:
            if isinstance(value, (tuple, list)):
                yield from self.flatten(value)
            else:
                yield value


systemverilog_generator = SystemVerilogGenerator()
