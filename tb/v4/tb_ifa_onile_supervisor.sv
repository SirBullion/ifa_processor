`timescale 1ns/1ps

module tb_ifa_onile_supervisor;

    localparam integer YARA_COUNT = 2;
    localparam integer YARA_W = 1;

    logic clk;
    logic rst;

    logic babalawo_mode;

    logic grant_valid;
    logic revoke_valid;

    logic [YARA_W-1:0] admin_source_yara;
    logic [YARA_W-1:0] admin_destination_yara;

    logic share_request;
    logic [YARA_W-1:0] request_source_yara;
    logic [YARA_W-1:0] request_destination_yara;

    logic share_allowed;
    logic share_denied;
    logic explicit_permission;

    logic [31:0] allowed_count;
    logic [31:0] denied_count;

    ifa_onile_supervisor #(
        .YARA_COUNT(YARA_COUNT)
    ) dut (
        .clk(clk),
        .rst(rst),

        .babalawo_mode(babalawo_mode),

        .grant_valid(grant_valid),
        .revoke_valid(revoke_valid),

        .admin_source_yara(admin_source_yara),
        .admin_destination_yara(admin_destination_yara),

        .share_request(share_request),
        .request_source_yara(request_source_yara),
        .request_destination_yara(request_destination_yara),

        .share_allowed(share_allowed),
        .share_denied(share_denied),

        .explicit_permission(explicit_permission),
        .allowed_count(allowed_count),
        .denied_count(denied_count)
    );

    always #5 clk = ~clk;

    task automatic request_share(
        input logic src,
        input logic dst
    );
    begin
        @(negedge clk);

        request_source_yara      = src;
        request_destination_yara = dst;
        share_request            = 1'b1;

        $display("REQUEST YARA %0d -> YARA %0d | babalawo=%0d permission=%0d allowed=%0d denied=%0d",
                 src, dst, babalawo_mode, explicit_permission,
                 share_allowed, share_denied);

        @(negedge clk);
        share_request = 1'b0;
    end
    endtask

    task automatic grant_share(
        input logic src,
        input logic dst
    );
    begin
        @(negedge clk);

        admin_source_yara      = src;
        admin_destination_yara = dst;
        grant_valid            = 1'b1;

        @(negedge clk);
        grant_valid = 1'b0;

        #1;

        $display(
            "ONILE GRANT: YARA %0d -> YARA %0d",
            src,
            dst
        );
    end
    endtask

    task automatic revoke_share(
        input logic src,
        input logic dst
    );
    begin
        @(negedge clk);

        admin_source_yara      = src;
        admin_destination_yara = dst;
        revoke_valid           = 1'b1;

        @(negedge clk);
        revoke_valid = 1'b0;

        #1;

        $display(
            "ONILE REVOKE: YARA %0d -> YARA %0d",
            src,
            dst
        );
    end
    endtask

    initial begin
        $dumpfile("sim/v4/ifa_onile_supervisor.vcd");
        $dumpvars(0, tb_ifa_onile_supervisor);

        clk = 0;
        rst = 1;

        babalawo_mode = 0;

        grant_valid  = 0;
        revoke_valid = 0;

        admin_source_yara      = 0;
        admin_destination_yara = 0;

        share_request            = 0;
        request_source_yara      = 0;
        request_destination_yara = 0;

        repeat (3) @(negedge clk);
        rst = 0;

        $display("============================================================");
        $display("IFÁ V4 ONÍLẸ̀ PERMISSION TEST");
        $display("Isolation by default; sharing by authorization");
        $display("============================================================");

        //--------------------------------------------------------------
        // Test 1:
        // Same-room use is local and must always be allowed.
        //--------------------------------------------------------------

        request_share(0, 0);

        if (share_allowed !== 1'b1)
            $fatal(1, "Local YARA access should be allowed");

        //--------------------------------------------------------------
        // Test 2:
        // Cross-room use in normal mode must be denied.
        //--------------------------------------------------------------

        request_share(0, 1);

        if (share_denied !== 1'b1)
            $fatal(1, "Cross-YARA sharing must be denied in normal mode");

        //--------------------------------------------------------------
        // Test 3:
        // Entering Babaláwo mode alone does not grant permission.
        //--------------------------------------------------------------

        babalawo_mode = 1'b1;

        request_share(0, 1);

        if (share_denied !== 1'b1)
            $fatal(1, "Babalawo mode alone must not authorize sharing");

        //--------------------------------------------------------------
        // Test 4:
        // Onílẹ̀ explicitly grants YARA 0 -> YARA 1.
        //--------------------------------------------------------------

        grant_share(0, 1);

        request_share(0, 1);

        if (share_allowed !== 1'b1)
            $fatal(1, "Granted cross-YARA sharing should be allowed");

        //--------------------------------------------------------------
        // Test 5:
        // Permission is directional.
        // 0 -> 1 grant must not imply 1 -> 0.
        //--------------------------------------------------------------

        request_share(1, 0);

        if (share_denied !== 1'b1)
            $fatal(1, "Permission must remain directional");

        //--------------------------------------------------------------
        // Test 6:
        // Revoke permission and confirm access is denied again.
        //--------------------------------------------------------------

        revoke_share(0, 1);

        request_share(0, 1);

        if (share_denied !== 1'b1)
            $fatal(1, "Revoked sharing permission must be denied");

        //--------------------------------------------------------------
        // Test 7:
        // Leaving Babaláwo mode preserves isolation.
        //--------------------------------------------------------------

        babalawo_mode = 1'b0;

        request_share(0, 1);

        if (share_denied !== 1'b1)
            $fatal(1, "Normal mode must deny cross-YARA sharing");

        $display("");
        $display("FINAL COUNTERS");
        $display("------------------------------------------------------------");
        $display("Allowed requests = %0d", allowed_count);
        $display("Denied requests  = %0d", denied_count);

        $display("============================================================");
        $display("PASS: Local YÀRÁ access is allowed");
        $display("PASS: Cross-YÀRÁ sharing is denied by default");
        $display("PASS: Babaláwo mode alone does not bypass isolation");
        $display("PASS: Onílẹ̀ grants explicit directional permission");
        $display("PASS: Revocation restores isolation");
        $display("============================================================");

        $finish;
    end

endmodule
