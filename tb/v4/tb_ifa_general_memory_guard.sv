`timescale 1ns/1ps

module tb_ifa_general_memory_guard;

    localparam integer WIDTH      = 8;
    localparam integer ADDR_W     = 4;
    localparam integer YARA_COUNT = 2;
    localparam integer YARA_W     = 1;

    logic clk;
    logic rst;

    logic [YARA_W-1:0] active_yara;

    logic mem_request;
    logic mem_write;
    logic [ADDR_W-1:0] mem_address;
    logic [WIDTH-1:0] mem_write_data;

    logic [WIDTH-1:0] mem_read_data;
    logic mem_allowed;
    logic mem_denied;

    logic babalawo_mode;

    logic grant_read_valid;
    logic grant_write_valid;
    logic revoke_read_valid;
    logic revoke_write_valid;

    logic [ADDR_W-1:0] admin_address;
    logic [YARA_W-1:0] admin_yara;

    logic address_owned;
    logic [YARA_W-1:0] address_owner;
    logic active_read_permission;
    logic active_write_permission;

    logic [31:0] read_count;
    logic [31:0] write_count;
    logic [31:0] denied_count;

    ifa_general_memory_guard #(
        .WIDTH(WIDTH),
        .ADDR_W(ADDR_W),
        .YARA_COUNT(YARA_COUNT)
    ) dut (
        .clk(clk),
        .rst(rst),

        .active_yara(active_yara),

        .mem_request(mem_request),
        .mem_write(mem_write),
        .mem_address(mem_address),
        .mem_write_data(mem_write_data),

        .mem_read_data(mem_read_data),
        .mem_allowed(mem_allowed),
        .mem_denied(mem_denied),

        .babalawo_mode(babalawo_mode),

        .grant_read_valid(grant_read_valid),
        .grant_write_valid(grant_write_valid),
        .revoke_read_valid(revoke_read_valid),
        .revoke_write_valid(revoke_write_valid),

        .admin_address(admin_address),
        .admin_yara(admin_yara),

        .address_owned(address_owned),
        .address_owner(address_owner),
        .active_read_permission(active_read_permission),
        .active_write_permission(active_write_permission),

        .read_count(read_count),
        .write_count(write_count),
        .denied_count(denied_count)
    );

    always #5 clk = ~clk;

    task automatic write_memory(
        input logic yara,
        input logic [3:0] address,
        input logic [7:0] data
    );
    begin
        @(negedge clk);

        active_yara   = yara;
        mem_address   = address;
        mem_write_data = data;
        mem_write     = 1'b1;
        mem_request   = 1'b1;

        @(posedge clk);
        #1;

        $display("WRITE YARA=%0d ADDR=%0h DATA=%02h allowed=%0d denied=%0d owner=%0d",
                 yara, address, data, mem_allowed, mem_denied, address_owner);

        @(negedge clk);
        mem_request = 1'b0;
        mem_write   = 1'b0;
    end
    endtask

    task automatic read_memory(
        input logic yara,
        input logic [3:0] address
    );
    begin
        @(negedge clk);

        active_yara = yara;
        mem_address = address;
        mem_write   = 1'b0;
        mem_request = 1'b1;

        @(posedge clk);
        #1;

        $display("READ  YARA=%0d ADDR=%0h DATA=%02h allowed=%0d denied=%0d owner=%0d",
                 yara, address, mem_read_data, mem_allowed, mem_denied, address_owner);

        @(negedge clk);
        mem_request = 1'b0;
    end
    endtask

    task automatic grant_read(
        input logic yara,
        input logic [3:0] address
    );
    begin
        @(negedge clk);

        admin_yara       = yara;
        admin_address    = address;
        grant_read_valid = 1'b1;

        @(posedge clk);
        #1;

        @(negedge clk);
        grant_read_valid = 1'b0;

        $display("ONILE GRANT READ: YARA=%0d ADDR=%0h", yara, address);
    end
    endtask

    task automatic grant_write(
        input logic yara,
        input logic [3:0] address
    );
    begin
        @(negedge clk);

        admin_yara        = yara;
        admin_address     = address;
        grant_write_valid = 1'b1;

        @(posedge clk);
        #1;

        @(negedge clk);
        grant_write_valid = 1'b0;

        $display("ONILE GRANT WRITE: YARA=%0d ADDR=%0h", yara, address);
    end
    endtask

    task automatic revoke_read(
        input logic yara,
        input logic [3:0] address
    );
    begin
        @(negedge clk);

        admin_yara        = yara;
        admin_address     = address;
        revoke_read_valid = 1'b1;

        @(posedge clk);
        #1;

        @(negedge clk);
        revoke_read_valid = 1'b0;

        $display("ONILE REVOKE READ: YARA=%0d ADDR=%0h", yara, address);
    end
    endtask

    initial begin
        $dumpfile("sim/v4/ifa_general_memory_guard.vcd");
        $dumpvars(0, tb_ifa_general_memory_guard);

        clk = 0;
        rst = 1;

        active_yara = 0;

        mem_request = 0;
        mem_write = 0;
        mem_address = 0;
        mem_write_data = 0;

        babalawo_mode = 0;

        grant_read_valid = 0;
        grant_write_valid = 0;
        revoke_read_valid = 0;
        revoke_write_valid = 0;

        admin_address = 0;
        admin_yara = 0;

        repeat (3) @(negedge clk);
        rst = 0;

        $display("============================================================");
        $display("IFÁ V4 SHARED GENERAL MEMORY GUARD TEST");
        $display("============================================================");

        // YÀRÁ 0 claims address 3 and writes AA.
        write_memory(0, 4'h3, 8'hAA);

        if (mem_allowed !== 1'b1)
            $fatal(1, "Owner's first write should be allowed");

        if (address_owner !== 0)
            $fatal(1, "YARA 0 should own address 3");

        // YÀRÁ 1 cannot read by default.
        read_memory(1, 4'h3);

        if (mem_denied !== 1'b1)
            $fatal(1, "Cross-YARA read should be denied by default");

        // Normal mode cannot grant permissions.
        grant_read(1, 4'h3);

        read_memory(1, 4'h3);

        if (mem_denied !== 1'b1)
            $fatal(1, "Normal-mode grant must have no effect");

        // Enter Babaláwo mode and grant read permission.
        babalawo_mode = 1'b1;
        grant_read(1, 4'h3);
        babalawo_mode = 1'b0;

        // Permission remains usable in normal execution mode.
        read_memory(1, 4'h3);

        if (mem_allowed !== 1'b1 || mem_read_data !== 8'hAA)
            $fatal(1, "Granted read should return shared data");

        // Read permission must not imply write permission.
        write_memory(1, 4'h3, 8'h55);

        if (mem_denied !== 1'b1)
            $fatal(1, "Read grant must not imply write access");

        // Explicitly grant write permission.
        babalawo_mode = 1'b1;
        grant_write(1, 4'h3);
        babalawo_mode = 1'b0;

        write_memory(1, 4'h3, 8'h55);

        if (mem_allowed !== 1'b1)
            $fatal(1, "Granted write should be allowed");

        // Owner sees the updated shared value.
        read_memory(0, 4'h3);

        if (mem_read_data !== 8'h55)
            $fatal(1, "Owner did not observe shared-memory update");

        // Revoke YÀRÁ 1 read permission.
        babalawo_mode = 1'b1;
        revoke_read(1, 4'h3);
        babalawo_mode = 1'b0;

        read_memory(1, 4'h3);

        if (mem_denied !== 1'b1)
            $fatal(1, "Revoked read permission should deny access");

        $display("");
        $display("FINAL COUNTERS");
        $display("------------------------------------------------------------");
        $display("Reads   = %0d", read_count);
        $display("Writes  = %0d", write_count);
        $display("Denied  = %0d", denied_count);

        $display("============================================================");
        $display("PASS: General Memory ownership is enforced");
        $display("PASS: Cross-YÀRÁ access is denied by default");
        $display("PASS: Only Babaláwo may administer permissions");
        $display("PASS: Read and write permissions remain separate");
        $display("PASS: Revocation blocks later access");
        $display("============================================================");

        $finish;
    end

endmodule
