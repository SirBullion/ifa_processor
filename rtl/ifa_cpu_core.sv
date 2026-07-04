module ifa_cpu_core (
    input  logic clk,
    input  logic reset,
    input  logic [15:0] instr_in,

    output logic [9:0] pc,
    output logic [15:0] ir,
    output logic halted,

    output logic [7:0] data_reg,
    output logic [7:0] original_reg,
    output logic [7:0] encoded_reg,
    output logic [7:0] corrupted_reg,
    output logic [7:0] recovered_reg,
    output logic [7:0] error_reg,
    output logic [7:0] delta_reg,
    output logic [7:0] corrected_reg,
    output logic [7:0] output_reg,
    output logic [3:0] output_index,
    output logic [127:0] output_buffer_flat,
    output logic out_valid,
    output logic [7:0] out_byte
);

    localparam OP_NOP         = 4'h0;
    localparam OP_LOAD        = 4'h1;
    localparam OP_P8          = 4'h2;
    localparam OP_INJECT      = 4'h3;
    localparam OP_INV_CORRUPT = 4'h4;
    localparam OP_CORRECT     = 4'h5;
    localparam OP_FINAL_INV   = 4'h6;
    localparam OP_OUT         = 4'h7;
    localparam OP_ADD         = 4'h8;
    localparam OP_SUB         = 4'h9;
    localparam OP_XOR_IMM     = 4'hA;
    localparam OP_DEC         = 4'hB;
    localparam OP_JMP         = 4'hC;
    localparam OP_JZ          = 4'hD;
    localparam OP_PRINT_ODU   = 4'hE;
    localparam OP_HALT        = 4'hF;

    logic [3:0] opcode;
    logic [7:0] imm;

    logic [7:0] p8_out;
    logic [7:0] inv_corrupt_out;
    logic [7:0] inv_corrected_out;
    logic [7:0] error_from_delta;

    logic printing_odu;
    logic [7:0] odu_value;
    logic [5:0] odu_pos;

    assign opcode = instr_in[15:12];
    assign imm    = instr_in[7:0];

    ifa_p8 p8_unit (.x(data_reg), .y(p8_out));
    ifa_p8_inv inv_corrupt_unit (.y(corrupted_reg), .x(inv_corrupt_out));
    ifa_p8_inv inv_corrected_unit (.y(corrected_reg), .x(inv_corrected_out));
    ifa_t8 t_delta (.e(delta_reg), .delta(error_from_delta));

    function automatic [7:0] force_agreement_value(input logic [7:0] x);
        begin
            force_agreement_value[7] = x[7];
            force_agreement_value[6] = x[7];

            force_agreement_value[5] = x[5];
            force_agreement_value[4] = x[5];

            force_agreement_value[3] = x[3];
            force_agreement_value[2] = x[3];

            force_agreement_value[1] = x[1];
            force_agreement_value[0] = x[1];
        end
    endfunction

    function automatic [7:0] force_disagreement_value(input logic [7:0] x);
        begin
            force_disagreement_value[7] = x[7];
            force_disagreement_value[6] = ~x[7];

            force_disagreement_value[5] = x[5];
            force_disagreement_value[4] = ~x[5];

            force_disagreement_value[3] = x[3];
            force_disagreement_value[2] = ~x[3];

            force_disagreement_value[1] = x[1];
            force_disagreement_value[0] = ~x[1];
        end
    endfunction


    function automatic [3:0] odu_len(input logic [3:0] idx);
        case (idx)
            4'h0: odu_len = 4'd6; // Ògbè
            4'h1: odu_len = 4'd9; // Ògúndá
            4'h2: odu_len = 4'd10; // Ìretẹ̀
            4'h3: odu_len = 4'd9; // Ìròsùn
            4'h4: odu_len = 4'd8; // Òtúrá
            4'h5: odu_len = 4'd5; // Òsé
            4'h6: odu_len = 4'd5; // Òdí
            4'h7: odu_len = 4'd8; // Òbàrà
            4'h8: odu_len = 4'd5; // Òsá
            4'h9: odu_len = 4'd8; // Ìwòrì
            4'hA: odu_len = 4'd6; // Òfún
            4'hB: odu_len = 4'd5; // Ìká
            4'hC: odu_len = 4'd10; // Òwónrín
            4'hD: odu_len = 4'd13; // Òtúrúpọn
            4'hE: odu_len = 4'd10; // Òkànràn
            4'hF: odu_len = 4'd8; // Òyèkú
            default: odu_len = 4'd0;
        endcase
    endfunction

    function automatic [7:0] odu_char(input logic [3:0] idx, input logic [5:0] pos);
        logic [9:0] addr;
        begin
            addr = {idx, pos[3:0]};
            odu_char = 8'h00;

            case (addr)
                10'd0: odu_char = 8'hC3;
                10'd1: odu_char = 8'h92;
                10'd2: odu_char = 8'h67;
                10'd3: odu_char = 8'h62;
                10'd4: odu_char = 8'hC3;
                10'd5: odu_char = 8'hA8;
                10'd6: odu_char = 8'h00;
                10'd7: odu_char = 8'h00;
                10'd8: odu_char = 8'h00;
                10'd9: odu_char = 8'h00;
                10'd10: odu_char = 8'h00;
                10'd11: odu_char = 8'h00;
                10'd12: odu_char = 8'h00;
                10'd13: odu_char = 8'h00;
                10'd14: odu_char = 8'h00;
                10'd15: odu_char = 8'h00;
                10'd16: odu_char = 8'hC3;
                10'd17: odu_char = 8'h92;
                10'd18: odu_char = 8'h67;
                10'd19: odu_char = 8'hC3;
                10'd20: odu_char = 8'hBA;
                10'd21: odu_char = 8'h6E;
                10'd22: odu_char = 8'h64;
                10'd23: odu_char = 8'hC3;
                10'd24: odu_char = 8'hA1;
                10'd25: odu_char = 8'h00;
                10'd26: odu_char = 8'h00;
                10'd27: odu_char = 8'h00;
                10'd28: odu_char = 8'h00;
                10'd29: odu_char = 8'h00;
                10'd30: odu_char = 8'h00;
                10'd31: odu_char = 8'h00;
                10'd32: odu_char = 8'hC3;
                10'd33: odu_char = 8'h8C;
                10'd34: odu_char = 8'h72;
                10'd35: odu_char = 8'h65;
                10'd36: odu_char = 8'h74;
                10'd37: odu_char = 8'hE1;
                10'd38: odu_char = 8'hBA;
                10'd39: odu_char = 8'hB9;
                10'd40: odu_char = 8'hCC;
                10'd41: odu_char = 8'h80;
                10'd42: odu_char = 8'h00;
                10'd43: odu_char = 8'h00;
                10'd44: odu_char = 8'h00;
                10'd45: odu_char = 8'h00;
                10'd46: odu_char = 8'h00;
                10'd47: odu_char = 8'h00;
                10'd48: odu_char = 8'hC3;
                10'd49: odu_char = 8'h8C;
                10'd50: odu_char = 8'h72;
                10'd51: odu_char = 8'hC3;
                10'd52: odu_char = 8'hB2;
                10'd53: odu_char = 8'h73;
                10'd54: odu_char = 8'hC3;
                10'd55: odu_char = 8'hB9;
                10'd56: odu_char = 8'h6E;
                10'd57: odu_char = 8'h00;
                10'd58: odu_char = 8'h00;
                10'd59: odu_char = 8'h00;
                10'd60: odu_char = 8'h00;
                10'd61: odu_char = 8'h00;
                10'd62: odu_char = 8'h00;
                10'd63: odu_char = 8'h00;
                10'd64: odu_char = 8'hC3;
                10'd65: odu_char = 8'h92;
                10'd66: odu_char = 8'h74;
                10'd67: odu_char = 8'hC3;
                10'd68: odu_char = 8'hBA;
                10'd69: odu_char = 8'h72;
                10'd70: odu_char = 8'hC3;
                10'd71: odu_char = 8'hA1;
                10'd72: odu_char = 8'h00;
                10'd73: odu_char = 8'h00;
                10'd74: odu_char = 8'h00;
                10'd75: odu_char = 8'h00;
                10'd76: odu_char = 8'h00;
                10'd77: odu_char = 8'h00;
                10'd78: odu_char = 8'h00;
                10'd79: odu_char = 8'h00;
                10'd80: odu_char = 8'hC3;
                10'd81: odu_char = 8'h92;
                10'd82: odu_char = 8'h73;
                10'd83: odu_char = 8'hC3;
                10'd84: odu_char = 8'hA9;
                10'd85: odu_char = 8'h00;
                10'd86: odu_char = 8'h00;
                10'd87: odu_char = 8'h00;
                10'd88: odu_char = 8'h00;
                10'd89: odu_char = 8'h00;
                10'd90: odu_char = 8'h00;
                10'd91: odu_char = 8'h00;
                10'd92: odu_char = 8'h00;
                10'd93: odu_char = 8'h00;
                10'd94: odu_char = 8'h00;
                10'd95: odu_char = 8'h00;
                10'd96: odu_char = 8'hC3;
                10'd97: odu_char = 8'h92;
                10'd98: odu_char = 8'h64;
                10'd99: odu_char = 8'hC3;
                10'd100: odu_char = 8'hAD;
                10'd101: odu_char = 8'h00;
                10'd102: odu_char = 8'h00;
                10'd103: odu_char = 8'h00;
                10'd104: odu_char = 8'h00;
                10'd105: odu_char = 8'h00;
                10'd106: odu_char = 8'h00;
                10'd107: odu_char = 8'h00;
                10'd108: odu_char = 8'h00;
                10'd109: odu_char = 8'h00;
                10'd110: odu_char = 8'h00;
                10'd111: odu_char = 8'h00;
                10'd112: odu_char = 8'hC3;
                10'd113: odu_char = 8'h92;
                10'd114: odu_char = 8'h62;
                10'd115: odu_char = 8'hC3;
                10'd116: odu_char = 8'hA0;
                10'd117: odu_char = 8'h72;
                10'd118: odu_char = 8'hC3;
                10'd119: odu_char = 8'hA0;
                10'd120: odu_char = 8'h00;
                10'd121: odu_char = 8'h00;
                10'd122: odu_char = 8'h00;
                10'd123: odu_char = 8'h00;
                10'd124: odu_char = 8'h00;
                10'd125: odu_char = 8'h00;
                10'd126: odu_char = 8'h00;
                10'd127: odu_char = 8'h00;
                10'd128: odu_char = 8'hC3;
                10'd129: odu_char = 8'h92;
                10'd130: odu_char = 8'h73;
                10'd131: odu_char = 8'hC3;
                10'd132: odu_char = 8'hA1;
                10'd133: odu_char = 8'h00;
                10'd134: odu_char = 8'h00;
                10'd135: odu_char = 8'h00;
                10'd136: odu_char = 8'h00;
                10'd137: odu_char = 8'h00;
                10'd138: odu_char = 8'h00;
                10'd139: odu_char = 8'h00;
                10'd140: odu_char = 8'h00;
                10'd141: odu_char = 8'h00;
                10'd142: odu_char = 8'h00;
                10'd143: odu_char = 8'h00;
                10'd144: odu_char = 8'hC3;
                10'd145: odu_char = 8'h8C;
                10'd146: odu_char = 8'h77;
                10'd147: odu_char = 8'hC3;
                10'd148: odu_char = 8'hB2;
                10'd149: odu_char = 8'h72;
                10'd150: odu_char = 8'hC3;
                10'd151: odu_char = 8'hAC;
                10'd152: odu_char = 8'h00;
                10'd153: odu_char = 8'h00;
                10'd154: odu_char = 8'h00;
                10'd155: odu_char = 8'h00;
                10'd156: odu_char = 8'h00;
                10'd157: odu_char = 8'h00;
                10'd158: odu_char = 8'h00;
                10'd159: odu_char = 8'h00;
                10'd160: odu_char = 8'hC3;
                10'd161: odu_char = 8'h92;
                10'd162: odu_char = 8'h66;
                10'd163: odu_char = 8'hC3;
                10'd164: odu_char = 8'hBA;
                10'd165: odu_char = 8'h6E;
                10'd166: odu_char = 8'h00;
                10'd167: odu_char = 8'h00;
                10'd168: odu_char = 8'h00;
                10'd169: odu_char = 8'h00;
                10'd170: odu_char = 8'h00;
                10'd171: odu_char = 8'h00;
                10'd172: odu_char = 8'h00;
                10'd173: odu_char = 8'h00;
                10'd174: odu_char = 8'h00;
                10'd175: odu_char = 8'h00;
                10'd176: odu_char = 8'hC3;
                10'd177: odu_char = 8'h8C;
                10'd178: odu_char = 8'h6B;
                10'd179: odu_char = 8'hC3;
                10'd180: odu_char = 8'hA1;
                10'd181: odu_char = 8'h00;
                10'd182: odu_char = 8'h00;
                10'd183: odu_char = 8'h00;
                10'd184: odu_char = 8'h00;
                10'd185: odu_char = 8'h00;
                10'd186: odu_char = 8'h00;
                10'd187: odu_char = 8'h00;
                10'd188: odu_char = 8'h00;
                10'd189: odu_char = 8'h00;
                10'd190: odu_char = 8'h00;
                10'd191: odu_char = 8'h00;
                10'd192: odu_char = 8'hC3;
                10'd193: odu_char = 8'h92;
                10'd194: odu_char = 8'h77;
                10'd195: odu_char = 8'hC3;
                10'd196: odu_char = 8'hB3;
                10'd197: odu_char = 8'h6E;
                10'd198: odu_char = 8'h72;
                10'd199: odu_char = 8'hC3;
                10'd200: odu_char = 8'hAD;
                10'd201: odu_char = 8'h6E;
                10'd202: odu_char = 8'h00;
                10'd203: odu_char = 8'h00;
                10'd204: odu_char = 8'h00;
                10'd205: odu_char = 8'h00;
                10'd206: odu_char = 8'h00;
                10'd207: odu_char = 8'h00;
                10'd208: odu_char = 8'hC3;
                10'd209: odu_char = 8'h92;
                10'd210: odu_char = 8'h74;
                10'd211: odu_char = 8'hC3;
                10'd212: odu_char = 8'hBA;
                10'd213: odu_char = 8'h72;
                10'd214: odu_char = 8'hC3;
                10'd215: odu_char = 8'hBA;
                10'd216: odu_char = 8'h70;
                10'd217: odu_char = 8'hE1;
                10'd218: odu_char = 8'hBB;
                10'd219: odu_char = 8'h8D;
                10'd220: odu_char = 8'h6E;
                10'd221: odu_char = 8'h00;
                10'd222: odu_char = 8'h00;
                10'd223: odu_char = 8'h00;
                10'd224: odu_char = 8'hC3;
                10'd225: odu_char = 8'h92;
                10'd226: odu_char = 8'h6B;
                10'd227: odu_char = 8'hC3;
                10'd228: odu_char = 8'hA0;
                10'd229: odu_char = 8'h6E;
                10'd230: odu_char = 8'h72;
                10'd231: odu_char = 8'hC3;
                10'd232: odu_char = 8'hA0;
                10'd233: odu_char = 8'h6E;
                10'd234: odu_char = 8'h00;
                10'd235: odu_char = 8'h00;
                10'd236: odu_char = 8'h00;
                10'd237: odu_char = 8'h00;
                10'd238: odu_char = 8'h00;
                10'd239: odu_char = 8'h00;
                10'd240: odu_char = 8'hC3;
                10'd241: odu_char = 8'h92;
                10'd242: odu_char = 8'h79;
                10'd243: odu_char = 8'hC3;
                10'd244: odu_char = 8'hA8;
                10'd245: odu_char = 8'h6B;
                10'd246: odu_char = 8'hC3;
                10'd247: odu_char = 8'hBA;
                10'd248: odu_char = 8'h00;
                10'd249: odu_char = 8'h00;
                10'd250: odu_char = 8'h00;
                10'd251: odu_char = 8'h00;
                10'd252: odu_char = 8'h00;
                10'd253: odu_char = 8'h00;
                10'd254: odu_char = 8'h00;
                10'd255: odu_char = 8'h00;
                default: odu_char = 8'h00;
            endcase
        end
    endfunction

    function automatic [5:0] odu_stream_len(input logic [7:0] value);
        odu_stream_len = odu_len(value[7:4]) + 6'd1 + odu_len(value[3:0]) + 6'd1;
    endfunction

    function automatic [7:0] odu_stream_byte(input logic [7:0] value, input logic [5:0] pos);
        logic [3:0] hlen;
        logic [3:0] llen;
        begin
            hlen = odu_len(value[7:4]);
            llen = odu_len(value[3:0]);

            if (pos < hlen)
                odu_stream_byte = odu_char(value[7:4], pos[3:0]);
            else if (pos == hlen)
                odu_stream_byte = " ";
            else if (pos < hlen + 1 + llen)
                odu_stream_byte = odu_char(value[3:0], pos - hlen - 1);
            else
                odu_stream_byte = 8'h0A;
        end
    endfunction

    always_ff @(posedge clk) begin
        if (reset) begin
            pc <= 10'h000;
            ir <= 16'h0000;
            halted <= 1'b0;

            data_reg <= 8'h00;
            original_reg <= 8'h00;
            encoded_reg <= 8'h00;
            corrupted_reg <= 8'h00;
            recovered_reg <= 8'h00;
            error_reg <= 8'h00;
            delta_reg <= 8'h00;
            corrected_reg <= 8'h00;
            output_reg <= 8'h00;
            output_index <= 4'h0;
            output_buffer_flat <= 128'h0;
            out_valid <= 1'b0;
            out_byte <= 8'h00;
            printing_odu <= 1'b0;
            odu_value <= 8'h00;
            odu_pos <= 6'h00;
        end else if (!halted) begin
            out_valid <= 1'b0;

            if (printing_odu) begin
                out_valid <= 1'b1;
                out_byte <= odu_stream_byte(odu_value, odu_pos);
                output_reg <= odu_stream_byte(odu_value, odu_pos);

                if (output_index < 4'd15) begin
                    output_buffer_flat[output_index*8 +: 8] <= odu_stream_byte(odu_value, odu_pos);
                    output_index <= output_index + 1;
                end

                if (odu_pos == odu_stream_len(odu_value) - 1) begin
                    printing_odu <= 1'b0;
                    odu_pos <= 6'h00;
                    pc <= pc + 1;
                end else begin
                    odu_pos <= odu_pos + 1;
                end
            end else begin
                ir <= instr_in;

                case (opcode)
                    OP_NOP: begin
                        case (imm)
                            8'h01: data_reg <= data_reg ^ 8'h55; // FLIP_AGREEMENT
                            8'h02: data_reg <= force_agreement_value(data_reg);
                            8'h03: data_reg <= force_disagreement_value(data_reg);
                            default: data_reg <= data_reg;
                        endcase
                        pc <= pc + 1;
                    end

                    OP_LOAD: begin
                        data_reg <= imm;
                        original_reg <= imm;
                        pc <= pc + 1;
                    end

                    OP_P8: begin
                        encoded_reg <= p8_out;
                        data_reg <= p8_out;
                        pc <= pc + 1;
                    end

                    OP_INJECT: begin
                        error_reg <= imm;
                        corrupted_reg <= encoded_reg ^ imm;
                        data_reg <= encoded_reg ^ imm;
                        pc <= pc + 1;
                    end

                    OP_INV_CORRUPT: begin
                        recovered_reg <= inv_corrupt_out;
                        delta_reg <= original_reg ^ inv_corrupt_out;
                        data_reg <= inv_corrupt_out;
                        pc <= pc + 1;
                    end

                    OP_CORRECT: begin
                        corrected_reg <= corrupted_reg ^ error_from_delta;
                        data_reg <= corrupted_reg ^ error_from_delta;
                        pc <= pc + 1;
                    end

                    OP_FINAL_INV: begin
                        recovered_reg <= inv_corrected_out;
                        data_reg <= inv_corrected_out;
                        pc <= pc + 1;
                    end

                    OP_OUT: begin
                        output_reg <= data_reg;
                        if (output_index < 4'd15) begin
                            output_buffer_flat[output_index*8 +: 8] <= data_reg;
                            output_index <= output_index + 1;
                        end
                        out_valid <= 1'b1;
                        out_byte <= data_reg;
                        pc <= pc + 1;
                    end

                    OP_ADD: begin
                        data_reg <= data_reg + imm;
                        pc <= pc + 1;
                    end

                    OP_SUB: begin
                        data_reg <= data_reg - imm;
                        pc <= pc + 1;
                    end

                    OP_XOR_IMM: begin
                        data_reg <= data_reg ^ imm;
                        pc <= pc + 1;
                    end

                    OP_DEC: begin
                        data_reg <= data_reg - 8'h01;
                        pc <= pc + 1;
                    end

                    OP_JMP: begin
                        pc <= imm;
                    end

                    OP_JZ: begin
                        if (data_reg == 8'h00)
                            pc <= imm;
                        else
                            pc <= pc + 1;
                    end

                    OP_PRINT_ODU: begin
                        printing_odu <= 1'b1;
                        odu_value <= data_reg;
                        odu_pos <= 6'h00;
                    end

                    OP_HALT: begin
                        halted <= 1'b1;
                    end

                    default: begin
                        pc <= pc + 1;
                    end
                endcase
            end
        end
    end

endmodule
