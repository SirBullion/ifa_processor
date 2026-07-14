`timescale 1ns/1ps

module tb_ifa_yara_frame_delegation;

    localparam integer MAX_YARA = 2;
    localparam integer YARA_W   = 1;

    logic clk;
    logic rst;

    logic [YARA_W-1:0] active_yara;
    logic in_valid;

    logic [7:0] A;
    logic [7:0] B;

    logic [MAX_YARA-1:0] clear_yara;

    logic share_commit;
    logic [YARA_W-1:0] share_source_yara;
    logic [YARA_W-1:0] share_destination_yara;
    logic share_authorized;

    logic rmu_hit;
    logic rmu_miss;

    logic share_done;
    logic share_denied;

    logic last_share_done;
    logic last_share_denied;

    logic [7:0] out_y;
    logic [7:0] out_ra;
    logic [7:0] out_rd;
    logic [7:0] out_r0;
    logic [7:0] out_t;

    logic [31:0] yara0_hits;
    logic [31:0] yara0_misses;
    logic [31:0] yara0_imports;

    logic [31:0] yara1_hits;
    logic [31:0] yara1_misses;
    logic [31:0] yara1_imports;

    ifa_yara_frame_share_core #(
        .WIDTH(8),
        .DEPTH(16),
        .MAX_YARA(MAX_YARA)
    ) dut (
        .clk(clk),
        .rst(rst),

        .active_yara(active_yara),
        .in_valid(in_valid),

        .A(A),
        .B(B),

        .clear_yara(clear_yara),

        .share_commit(share_commit),
        .share_source_yara(share_source_yara),
        .share_destination_yara(share_destination_yara),
        .share_authorized(share_authorized),

        .rmu_hit(rmu_hit),
        .rmu_miss(rmu_miss),

        .share_done(share_done),
        .share_denied(share_denied),

        .out_y(out_y),
        .out_ra(out_ra),
        .out_rd(out_rd),
        .out_r0(out_r0),
        .out_t(out_t),

        .yara0_hits(yara0_hits),
        .yara0_misses(yara0_misses),
        .yara0_imports(yara0_imports),

        .yara1_hits(yara1_hits),
        .yara1_misses(yara1_misses),
        .yara1_imports(yara1_imports)
    );

    always #5 clk = ~clk;

    //==================================================================
    // Execute one relation inside a selected YÀRÁ
    //==================================================================

    task automatic execute_relation(
        input logic [YARA_W-1:0] room,
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

        $display(
            "EXEC YARA=%0d A=%02h B=%02h | hit=%0d miss=%0d | "
            "Y=%02h RA=%02h RD=%02h R0=%02h T=%02h",
            room,
            a,
            b,
            rmu_hit,
            rmu_miss,
            out_y,
            out_ra,
            out_rd,
            out_r0,
            out_t
        );
    end
    endtask

    //==================================================================
    // Attempt relation-frame delegation
    //==================================================================

    task automatic delegate_frame(
        input logic [YARA_W-1:0] src,
        input logic [YARA_W-1:0] dst,
        input logic authorized
    );
    begin
        @(negedge clk);

        share_source_yara = src;
        share_destination_yara = dst;
        share_authorized = authorized;
        share_commit = 1'b1;

        #1;

        last_share_denied = share_denied;

        @(posedge clk);

        #1;

        last_share_done = share_done;

        $display(
            "DELEGATE %0d -> %0d | authorized=%0d done=%0d denied=%0d",
            src,
            dst,
            authorized,
            last_share_done,
            last_share_denied
        );

        @(negedge clk);

        share_commit = 1'b0;
        share_authorized = 1'b0;
    end
    endtask

    //==================================================================
    // Clear exactly one local RMU
    //==================================================================

    task automatic clear_room(
        input logic [YARA_W-1:0] room
    );
    begin
        @(negedge clk);

        clear_yara = '0;
        clear_yara[room] = 1'b1;

        @(negedge clk);

        clear_yara = '0;

        #1;

        $display("CLEAR YARA=%0d", room);
    end
    endtask

    //==================================================================
    // Test sequence
    //==================================================================

    initial begin
        $dumpfile(
            "sim/v4/ifa_yara_frame_delegation.vcd"
        );

        $dumpvars(
            0,
            tb_ifa_yara_frame_delegation
        );

        clk = 1'b0;
        rst = 1'b1;

        active_yara = '0;
        in_valid = 1'b0;

        A = '0;
        B = '0;

        clear_yara = '0;

        share_commit = 1'b0;
        share_source_yara = '0;
        share_destination_yara = 1'b1;
        share_authorized = 1'b0;

        last_share_done = 1'b0;
        last_share_denied = 1'b0;

        repeat (3) @(negedge clk);

        rst = 1'b0;

        $display(
            "============================================================"
        );

        $display(
            "IFÁ V4 GENERIC RELATION FRAME DELEGATION TEST"
        );

        $display(
            "============================================================"
        );

        //==============================================================
        // Test 1:
        // YÀRÁ 0 computes and stores relation X.
        //==============================================================

        execute_relation(
            0,
            8'h0D,
            8'h06
        );

        if (rmu_miss !== 1'b1) begin
            $fatal(
                1,
                "YARA 0 first relation should MISS"
            );
        end

        //==============================================================
        // Test 2:
        // Unauthorized delegation must fail.
        //==============================================================

        delegate_frame(
            0,
            1,
            0
        );

        if (last_share_denied !== 1'b1) begin
            $fatal(
                1,
                "Unauthorized delegation should be denied"
            );
        end

        if (last_share_done !== 1'b0) begin
            $fatal(
                1,
                "Unauthorized delegation must not complete"
            );
        end

        //==============================================================
        // Test 3:
        // YÀRÁ 1 must still MISS for relation X.
        //==============================================================

        execute_relation(
            1,
            8'h0D,
            8'h06
        );

        if (rmu_miss !== 1'b1) begin
            $fatal(
                1,
                "YARA 1 must MISS before authorized delegation"
            );
        end

        //==============================================================
        // Test 4:
        // Store relation Y inside YÀRÁ 0.
        //==============================================================

        execute_relation(
            0,
            8'h21,
            8'h42
        );

        if (rmu_miss !== 1'b1) begin
            $fatal(
                1,
                "YARA 0 second relation should initially MISS"
            );
        end

        //==============================================================
        // Test 5:
        // Authorized delegation imports relation Y into YÀRÁ 1.
        //==============================================================

        delegate_frame(
            0,
            1,
            1
        );

        if (last_share_denied !== 1'b0) begin
            $fatal(
                1,
                "Authorized delegation should not be denied"
            );
        end

        if (last_share_done !== 1'b1) begin
            $fatal(
                1,
                "Authorized delegation should complete"
            );
        end

        if (yara1_imports !== 32'd1) begin
            $fatal(
                1,
                "YARA 1 should contain one imported frame"
            );
        end

        //==============================================================
        // Test 6:
        // Destination must HIT the delegated relation.
        //==============================================================

        execute_relation(
            1,
            8'h21,
            8'h42
        );

        if (rmu_hit !== 1'b1) begin
            $fatal(
                1,
                "Delegated frame should produce a YARA 1 HIT"
            );
        end

        if (
            out_y  !== 8'h63 ||
            out_ra !== 8'h00 ||
            out_rd !== 8'h63 ||
            out_r0 !== 8'h9C ||
            out_t  !== 8'h00
        ) begin
            $fatal(
                1,
                "Delegated full Relation Frame was corrupted"
            );
        end

        //==============================================================
        // Test 7:
        // Clear YÀRÁ 0 only.
        //==============================================================

        clear_room(0);

        execute_relation(
            0,
            8'h21,
            8'h42
        );

        if (rmu_miss !== 1'b1) begin
            $fatal(
                1,
                "Cleared YARA 0 must MISS"
            );
        end

        //==============================================================
        // Test 8:
        // YÀRÁ 1 must still retain the imported frame.
        //==============================================================

        execute_relation(
            1,
            8'h21,
            8'h42
        );

        if (rmu_hit !== 1'b1) begin
            $fatal(
                1,
                "Clearing YARA 0 must not affect YARA 1"
            );
        end

        $display("");
        $display("FINAL COUNTERS");

        $display(
            "YARA 0: hits=%0d misses=%0d imports=%0d",
            yara0_hits,
            yara0_misses,
            yara0_imports
        );

        $display(
            "YARA 1: hits=%0d misses=%0d imports=%0d",
            yara1_hits,
            yara1_misses,
            yara1_imports
        );

        $display(
            "============================================================"
        );

        $display(
            "PASS: Unauthorized delegation was denied"
        );

        $display(
            "PASS: Authorized frame was imported"
        );

        $display(
            "PASS: Destination reused delegated Relation Frame"
        );

        $display(
            "PASS: Local RMU clear remained isolated"
        );

        $display(
            "PASS: Relation key remained {RA,RD,T}"
        );

        $display(
            "============================================================"
        );

        $finish;
    end

endmodule
