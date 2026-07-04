module ifa_rom (
    input  logic [9:0] addr,
    output logic [15:0] instr
);

    logic [15:0] mem [0:1023];

    initial begin
        $readmemh("program.hex", mem);
    end

    always_comb begin
        instr = mem[addr];
    end

endmodule
