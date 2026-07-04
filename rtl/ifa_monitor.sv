module ifa_monitor (
    input  logic clk,
    input  logic reset,

    input  logic rx_valid,
    input  logic [7:0] rx_data,

    output logic printodu_start,
    output logic [7:0] printodu_value
);

    logic [7:0] buffer [0:31];
    logic [5:0] len;

    function automatic [3:0] hexval(input logic [7:0] c);
        if (c >= "0" && c <= "9") hexval = c - "0";
        else if (c >= "A" && c <= "F") hexval = c - "A" + 4'd10;
        else if (c >= "a" && c <= "f") hexval = c - "a" + 4'd10;
        else hexval = 4'h0;
    endfunction

    function automatic logic match_printodu;
        begin
            match_printodu =
                buffer[0]=="P" && buffer[1]=="R" && buffer[2]=="I" && buffer[3]=="N" &&
                buffer[4]=="T" && buffer[5]=="O" && buffer[6]=="D" && buffer[7]=="U";
        end
    endfunction

    always_ff @(posedge clk) begin
        if (reset) begin
            len <= 0;
            printodu_start <= 0;
            printodu_value <= 0;
        end else begin
            printodu_start <= 0;

            if (rx_valid) begin
                if (rx_data == 8'h0A || rx_data == 8'h0D) begin
                    if (len >= 10 && match_printodu()) begin
                        printodu_value <= {hexval(buffer[len-2]), hexval(buffer[len-1])};
                        printodu_start <= 1'b1;
                    end
                    len <= 0;
                end else begin
                    if (len < 32) begin
                        buffer[len] <= rx_data;
                        len <= len + 1;
                    end
                end
            end
        end
    end

endmodule
