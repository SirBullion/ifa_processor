`timescale 1ns/1ps

module tb_ifa_v4_onile_delegation_top;

    logic clk;
    logic rst;

    logic active_yara;
    logic in_valid;
    logic [7:0] A;
    logic [7:0] B;

    logic babalawo_mode;

    logic grant_valid;
    logic revoke_valid;
    logic admin_source_yara;
    logic admin_destination_yara;

    logic share_commit;
    logic share_source_yara;
    logic share_destination_yara;

    logic rmu_hit;
    logic rmu_miss;

    logic [7:0] out_y;
    logic [7:0] out_ra;
    logic [7:0] out_rd;
    logic [7:0] out_r0;
    logic [7:0] out_t;

    logic share_allowed;
    logic share_denied;
    logic share_done;
    logic explicit_permission;

    logic [31:0] allowed_share_count;
    logic [31:0] denied_share_count;

    logic [31:0] yara0_hits;
    logic [31:0] yara0_misses;
    logic [31:0] yara0_imports;

    logic [31:0] yara1_hits;
    logic [31:0] yara1_misses;
    logic [31:0] yara1_imports;

    logic captured_allowed;
    logic captured_denied;
    logic captured_done;

    ifa_v4_onile_delegation_top dut (
        .clk(clk),
        .rst(rst),

        .active_yara(active_yara),
        .in_valid(in_valid),
        .A(A),
        .B(B),

        .babalawo_mode(babalawo_mode),

        .grant_valid(grant_valid),
        .revoke_valid(revoke_valid),
        .admin_source_yara(admin_source_yara),
        .admin_destination_yara(admin_destination_yara),

        .share_commit(share_commit),
        .share_source_yara(share_source_yara),
        .share_destination_yara(share_destination_yara),

        .rmu_hit(rmu_hit),
        .rmu_miss(rmu_miss),

        .out_y(out_y),
        .out_ra(out_ra),
        .out_rd(out_rd),
        .out_r0(out_r0),
        .out_t(out_t),

        .share_allowed(share_allowed),
        .share_denied(share_denied),
        .share_done(share_done),
        .explicit_permission(explicit_permission),

        .allowed_share_count(allowed_share_count),
        .denied_share_count(denied_share_count),

        .yara0_hits(yara0_hits),
        .yara0_misses(yara0_misses),
        .yara0_imports(yara0_imports),

        .yara1_hits(yara1_hits),
        .yara1_misses(yara1_misses),
        .yara1_imports(yara1_imports)
    );

    always #5 clk = ~clk;

    task automatic execute_relation(
        input logic room,
        input logic [7:0] a,
        input logic [7:0] b
    );
    begin
        @(negedge clk);

        active_yara = room;
        A = a;
        B = b;
        in_valid = 1'b1;

        @(negedge clk);
        in_valid = 1'b0;

        #1;

        $display("EXEC YARA=%0d A=%02h B=%02h hit=%0d miss=%0d Y=%02h RA=%02h RD=%02h R0=%02h T=%02h",
                 room, a, b, rmu_hit, rmu_miss,
                 out_y, out_ra, out_rd, out_r0, out_t);
    end
    endtask

    task automatic administer_grant(
        input logic src,
        input logic dst
    );
    begin
        @(negedge clk);

        admin_source_yara = src;
        admin_destination_yara = dst;
        grant_valid = 1'b1;

        @(posedge clk);
        #1;

        @(negedge clk);
        grant_valid = 1'b0;

        $display("ONILE GRANT %0d -> %0d permission=%0d",
                 src, dst, explicit_permission);
    end
    endtask

    task automatic administer_revoke(
        input logic src,
        input logic dst
    );
    begin
        @(negedge clk);

        admin_source_yara = src;
        admin_destination_yara = dst;
        revoke_valid = 1'b1;

        @(posedge clk);
        #1;

        @(negedge clk);
        revoke_valid = 1'b0;

        $display("ONILE REVOKE %0d -> %0d", src, dst);
    end
    endtask

    task automatic request_delegation(
        input logic src,
        input logic dst
    );
    begin
        @(negedge clk);

        share_source_yara = src;
        share_destination_yara = dst;
        share_commit = 1'b1;

        #1;
        captured_allowed = share_allowed;
        captured_denied  = share_denied;

        @(posedge clk);
        #1;
        captured_done = share_done;

        $display("DELEGATE %0d -> %0d babalawo=%0d permission=%0d allowed=%0d denied=%0d done=%0d",
                 src, dst, babalawo_mode, explicit_permission,
                 captured_allowed, captured_denied, captured_done);

        @(negedge clk);
        share_commit = 1'b0;
    end
    endtask

    initial begin
        $dumpfile("sim/v4/ifa_v4_onile_delegation_top.vcd");
        $dumpvars(0, tb_ifa_v4_onile_delegation_top);

        clk = 0;
        rst = 1;

        active_yara = 0;
        in_valid = 0;
        A = 0;
        B = 0;

        babalawo_mode = 0;

        grant_valid = 0;
        revoke_valid = 0;
        admin_source_yara = 0;
        admin_destination_yara = 1;

        share_commit = 0;
        share_source_yara = 0;
        share_destination_yara = 1;

        captured_allowed = 0;
        captured_denied = 0;
        captured_done = 0;

        repeat (3) @(negedge clk);
        rst = 0;

        $display("============================================================");
        $display("IFÁ V4 ONÍLẸ̀ AUTHORIZED DELEGATION INTEGRATION TEST");
        $display("============================================================");

        // YÀRÁ 0 stores the relation to be delegated.
        execute_relation(0, 8'h21, 8'h42);

        if (rmu_miss !== 1'b1)
            $fatal(1, "YARA 0 first relation should MISS");

        // Normal mode: denied.
        request_delegation(0, 1);

        if (captured_denied !== 1'b1)
            $fatal(1, "Normal-mode delegation must be denied");

        // Babaláwo mode alone: still denied.
        babalawo_mode = 1'b1;

        request_delegation(0, 1);

        if (captured_denied !== 1'b1)
            $fatal(1, "Babalawo mode alone must not authorize sharing");

        // Explicit directional grant.
        administer_grant(0, 1);

        request_delegation(0, 1);

        if (captured_allowed !== 1'b1)
            $fatal(1, "Granted delegation should be allowed");

        if (captured_done !== 1'b1)
            $fatal(1, "Authorized Relation Frame import did not complete");

        if (yara1_imports !== 32'd1)
            $fatal(1, "Destination should record one imported frame");

        // Return to normal mode.
        babalawo_mode = 1'b0;

        // Destination should now get a real local RMU hit.
        execute_relation(1, 8'h21, 8'h42);

        if (rmu_hit !== 1'b1)
            $fatal(1, "Delegated frame should produce destination HIT");

        if (
            out_y  !== 8'h63 ||
            out_ra !== 8'h00 ||
            out_rd !== 8'h63 ||
            out_r0 !== 8'h9C ||
            out_t  !== 8'h00
        )
            $fatal(1, "Delegated Relation Frame content was corrupted");

        // Revoke and prove future delegation is blocked.
        babalawo_mode = 1'b1;
        administer_revoke(0, 1);

        request_delegation(0, 1);

        if (captured_denied !== 1'b1)
            $fatal(1, "Revoked delegation must be denied");

        $display("");
        $display("FINAL COUNTERS");
        $display("------------------------------------------------------------");
        $display("Allowed share requests = %0d", allowed_share_count);
        $display("Denied share requests  = %0d", denied_share_count);
        $display("YARA 0 hits/misses/imports = %0d/%0d/%0d",
                 yara0_hits, yara0_misses, yara0_imports);
        $display("YARA 1 hits/misses/imports = %0d/%0d/%0d",
                 yara1_hits, yara1_misses, yara1_imports);

        $display("============================================================");
        $display("PASS: Normal-mode frame delegation is denied");
        $display("PASS: Babaláwo mode alone does not bypass isolation");
        $display("PASS: Onílẹ̀ grant authorizes real frame delegation");
        $display("PASS: Destination reuses delegated frame as local RMU HIT");
        $display("PASS: Onílẹ̀ revocation blocks later delegation");
        $display("============================================================");

        $finish;
    end

endmodule
