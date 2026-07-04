module ifa_odu_printer (
    input  logic clk,
    input  logic reset,

    input  logic start,
    input  logic [7:0] value,

    output logic busy,
    output logic out_valid,
    output logic [7:0] out_byte,
    input  logic out_ready,

    output logic done
);

    logic [7:0] odu_value;
    logic [5:0] pos;

    function automatic [3:0] odu_len(input logic [3:0] idx);
        case (idx)
            4'h0: odu_len = 4'd6;  // Ògbè
            4'h1: odu_len = 4'd8;  // Ògúndá
            4'h2: odu_len = 4'd10; // Ìretẹ̀
            4'h3: odu_len = 4'd9;  // Ìròsùn
            4'h4: odu_len = 4'd8;  // Òtúrá
            4'h5: odu_len = 4'd5;  // Òsé
            4'h6: odu_len = 4'd5;  // Òdí
            4'h7: odu_len = 4'd8;  // Òbàrà
            4'h8: odu_len = 4'd5;  // Òsá
            4'h9: odu_len = 4'd8;  // Ìwòrì
            4'hA: odu_len = 4'd6;  // Òfún
            4'hB: odu_len = 4'd5;  // Ìká
            4'hC: odu_len = 4'd10; // Òwónrín
            4'hD: odu_len = 4'd12; // Òtúrúpọn
            4'hE: odu_len = 4'd10; // Òkànràn
            4'hF: odu_len = 4'd8;  // Òyèkú
            default: odu_len = 4'd0;
        endcase
    endfunction

    function automatic [7:0] odu_char(input logic [3:0] idx, input logic [5:0] p);
        logic [9:0] addr;
        begin
            addr = {idx, p[3:0]};
            odu_char = 8'h00;

            case (addr)
                // Ògbè
                10'd0: odu_char=8'hC3; 10'd1: odu_char=8'h92; 10'd2: odu_char=8'h67; 10'd3: odu_char=8'h62; 10'd4: odu_char=8'hC3; 10'd5: odu_char=8'hA8;
                // Ògúndá
                10'd16: odu_char=8'hC3; 10'd17: odu_char=8'h92; 10'd18: odu_char=8'h67; 10'd19: odu_char=8'hC3; 10'd20: odu_char=8'hBA; 10'd21: odu_char=8'h6E; 10'd22: odu_char=8'h64; 10'd23: odu_char=8'hC3; 10'd24: odu_char=8'hA1;
                // Ìretẹ̀
                10'd32: odu_char=8'hC3; 10'd33: odu_char=8'h8C; 10'd34: odu_char=8'h72; 10'd35: odu_char=8'h65; 10'd36: odu_char=8'h74; 10'd37: odu_char=8'hE1; 10'd38: odu_char=8'hBA; 10'd39: odu_char=8'hB9; 10'd40: odu_char=8'hCC; 10'd41: odu_char=8'h80;
                // Ìròsùn
                10'd48: odu_char=8'hC3; 10'd49: odu_char=8'h8C; 10'd50: odu_char=8'h72; 10'd51: odu_char=8'hC3; 10'd52: odu_char=8'hB2; 10'd53: odu_char=8'h73; 10'd54: odu_char=8'hC3; 10'd55: odu_char=8'hB9; 10'd56: odu_char=8'h6E;
                // Òtúrá
                10'd64: odu_char=8'hC3; 10'd65: odu_char=8'h92; 10'd66: odu_char=8'h74; 10'd67: odu_char=8'hC3; 10'd68: odu_char=8'hBA; 10'd69: odu_char=8'h72; 10'd70: odu_char=8'hC3; 10'd71: odu_char=8'hA1;
                // Òsé
                10'd80: odu_char=8'hC3; 10'd81: odu_char=8'h92; 10'd82: odu_char=8'h73; 10'd83: odu_char=8'hC3; 10'd84: odu_char=8'hA9;
                // Òdí
                10'd96: odu_char=8'hC3; 10'd97: odu_char=8'h92; 10'd98: odu_char=8'h64; 10'd99: odu_char=8'hC3; 10'd100: odu_char=8'hAD;
                // Òbàrà
                10'd112: odu_char=8'hC3; 10'd113: odu_char=8'h92; 10'd114: odu_char=8'h62; 10'd115: odu_char=8'hC3; 10'd116: odu_char=8'hA0; 10'd117: odu_char=8'h72; 10'd118: odu_char=8'hC3; 10'd119: odu_char=8'hA0;
                // Òsá
                10'd128: odu_char=8'hC3; 10'd129: odu_char=8'h92; 10'd130: odu_char=8'h73; 10'd131: odu_char=8'hC3; 10'd132: odu_char=8'hA1;
                // Ìwòrì
                10'd144: odu_char=8'hC3; 10'd145: odu_char=8'h8C; 10'd146: odu_char=8'h77; 10'd147: odu_char=8'hC3; 10'd148: odu_char=8'hB2; 10'd149: odu_char=8'h72; 10'd150: odu_char=8'hC3; 10'd151: odu_char=8'hAC;
                // Òfún
                10'd160: odu_char=8'hC3; 10'd161: odu_char=8'h92; 10'd162: odu_char=8'h66; 10'd163: odu_char=8'hC3; 10'd164: odu_char=8'hBA; 10'd165: odu_char=8'h6E;
                // Ìká
                10'd176: odu_char=8'hC3; 10'd177: odu_char=8'h8C; 10'd178: odu_char=8'h6B; 10'd179: odu_char=8'hC3; 10'd180: odu_char=8'hA1;
                // Òwónrín
                10'd192: odu_char=8'hC3; 10'd193: odu_char=8'h92; 10'd194: odu_char=8'h77; 10'd195: odu_char=8'hC3; 10'd196: odu_char=8'hB3; 10'd197: odu_char=8'h6E; 10'd198: odu_char=8'h72; 10'd199: odu_char=8'hC3; 10'd200: odu_char=8'hAD; 10'd201: odu_char=8'h6E;
                // Òtúrúpọn
                10'd208: odu_char=8'hC3; 10'd209: odu_char=8'h92; 10'd210: odu_char=8'h74; 10'd211: odu_char=8'hC3; 10'd212: odu_char=8'hBA; 10'd213: odu_char=8'h72; 10'd214: odu_char=8'hC3; 10'd215: odu_char=8'hBA; 10'd216: odu_char=8'h70; 10'd217: odu_char=8'hE1; 10'd218: odu_char=8'hBB; 10'd219: odu_char=8'h8D; 10'd220: odu_char=8'h6E;
                // Òkànràn
                10'd224: odu_char=8'hC3; 10'd225: odu_char=8'h92; 10'd226: odu_char=8'h6B; 10'd227: odu_char=8'hC3; 10'd228: odu_char=8'hA0; 10'd229: odu_char=8'h6E; 10'd230: odu_char=8'h72; 10'd231: odu_char=8'hC3; 10'd232: odu_char=8'hA0; 10'd233: odu_char=8'h6E;
                // Òyèkú
                10'd240: odu_char=8'hC3; 10'd241: odu_char=8'h92; 10'd242: odu_char=8'h79; 10'd243: odu_char=8'hC3; 10'd244: odu_char=8'hA8; 10'd245: odu_char=8'h6B; 10'd246: odu_char=8'hC3; 10'd247: odu_char=8'hBA;
                default: odu_char=8'h00;
            endcase
        end
    endfunction

    function automatic [5:0] stream_len(input logic [7:0] v);
        stream_len = odu_len(v[7:4]) + 6'd1 + odu_len(v[3:0]) + 6'd1;
    endfunction

    function automatic [7:0] stream_byte(input logic [7:0] v, input logic [5:0] p);
        logic [3:0] hlen;
        logic [3:0] llen;
        begin
            hlen = odu_len(v[7:4]);
            llen = odu_len(v[3:0]);

            if (p < hlen)
                stream_byte = odu_char(v[7:4], p);
            else if (p == hlen)
                stream_byte = " ";
            else if (p < hlen + 1 + llen)
                stream_byte = odu_char(v[3:0], p - hlen - 1);
            else
                stream_byte = 8'h0A;
        end
    endfunction

    always_ff @(posedge clk) begin
        if (reset) begin
            busy <= 0;
            out_valid <= 0;
            out_byte <= 0;
            done <= 0;
            pos <= 0;
            odu_value <= 0;
        end else begin
            done <= 0;

            if (start && !busy) begin
                busy <= 1;
                pos <= 0;
                odu_value <= value;
                out_valid <= 1;
                out_byte <= stream_byte(value, 0);
            end else if (busy && out_valid && out_ready) begin
                if (pos == stream_len(odu_value) - 1) begin
                    busy <= 0;
                    out_valid <= 0;
                    done <= 1;
                    pos <= 0;
                end else begin
                    pos <= pos + 1;
                    out_byte <= stream_byte(odu_value, pos + 1);
                    out_valid <= 1;
                end
            end
        end
    end

endmodule
