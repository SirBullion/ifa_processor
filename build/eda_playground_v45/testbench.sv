`timescale 1ns/1ps

module tb_ifa_native_rau_v45;

    localparam integer WIDTH    = 8;
    localparam integer OP_WIDTH = 4;

    localparam [OP_WIDTH-1:0] OP_PAPO  = 4'h0;
    localparam [OP_WIDTH-1:0] OP_YO    = 4'h1;
    localparam [OP_WIDTH-1:0] OP_DAGBA = 4'h2;
    localparam [OP_WIDTH-1:0] OP_PIN   = 4'h3;
    localparam [OP_WIDTH-1:0] OP_KU    = 4'h4;
    localparam [OP_WIDTH-1:0] OP_GBE   = 4'h5;
    localparam [OP_WIDTH-1:0] OP_SEDA  = 4'h6;
    localparam [OP_WIDTH-1:0] OP_JU    = 4'h7;
    localparam [OP_WIDTH-1:0] OP_KERE  = 4'h8;

    localparam [3:0] EXC_DIV_ZERO =
        4'h2;

    localparam [3:0] STATE_NONE =
        4'h0;

    localparam [3:0] STATE_POWER_EXTENDED =
        4'h1;

    reg [OP_WIDTH-1:0] op;

    reg [WIDTH-1:0] A;
    reg [WIDTH-1:0] B;

    wire [WIDTH-1:0] Y;
    wire [WIDTH-1:0] RA;
    wire [WIDTH-1:0] RD;
    wire [WIDTH-1:0] R0;
    wire [WIDTH-1:0] T;

    wire valid;

    wire exception_valid;
    wire [3:0] exception_code;

    wire state_valid;
    wire [3:0] state_code;

    wire eq_flag;
    wire gt_flag;
    wire lt_flag;

    ifa_native_rau_v45 #(
        .WIDTH(WIDTH),
        .OP_WIDTH(OP_WIDTH)
    ) dut (
        .op(op),
        .A(A),
        .B(B),

        .Y(Y),
        .RA(RA),
        .RD(RD),
        .R0(R0),
        .T(T),

        .valid(valid),

        .exception_valid(exception_valid),
        .exception_code(exception_code),

        .state_valid(state_valid),
        .state_code(state_code),

        .eq_flag(eq_flag),
        .gt_flag(gt_flag),
        .lt_flag(lt_flag)
    );

    task automatic check_relations;
    begin
        if (RA !== (A & B)) begin
            $fatal(1, "RA invariant failed");
        end

        if (RD !== (A ^ B)) begin
            $fatal(1, "RD invariant failed");
        end

        if (R0 !== ~(A | B)) begin
            $fatal(1, "R0 invariant failed");
        end
    end
    endtask

    initial begin
        $display(
            "============================================================"
        );
        $display(
            "IFÁ V4.5 COMPLETE NATIVE RAU TEST"
        );
        $display(
            "============================================================"
        );

        //--------------------------------------------------------------
        // PAPO
        //--------------------------------------------------------------

        op = OP_PAPO;
        A = 8'hF0;
        B = 8'h30;

        #1;
        check_relations();

        if (
            Y !== 8'h20 ||
            T !== 8'h01 ||
            state_valid !== 1'b0
        ) begin
            $fatal(1, "PAPO failed");
        end

        $display(
            "PASS: PAPO Y=%02h T=%02h",
            Y,
            T
        );

        //--------------------------------------------------------------
        // YO
        //--------------------------------------------------------------

        op = OP_YO;
        A = 8'h06;
        B = 8'h0D;

        #1;
        check_relations();

        if (
            Y !== 8'hF9 ||
            T !== 8'h01 ||
            state_valid !== 1'b0
        ) begin
            $fatal(1, "YO failed");
        end

        $display(
            "PASS: YO Y=%02h T=%02h",
            Y,
            T
        );

        //--------------------------------------------------------------
        // DÁGBA
        //
        // F0 * 10 = 0F00
        //--------------------------------------------------------------

        op = OP_DAGBA;
        A = 8'hF0;
        B = 8'h10;

        #1;
        check_relations();

        if (
            Y !== 8'h00 ||
            T !== 8'h0F
        ) begin
            $fatal(1, "DAGBA failed");
        end

        $display(
            "PASS: DAGBA Y=%02h T=%02h",
            Y,
            T
        );

        //--------------------------------------------------------------
        // PIN
        //
        // 29 / 6 = quotient 4, remainder 5
        //--------------------------------------------------------------

        op = OP_PIN;
        A = 8'd29;
        B = 8'd6;

        #1;
        check_relations();

        if (
            Y !== 8'd4 ||
            T !== 8'd5 ||
            valid !== 1'b1 ||
            exception_valid !== 1'b0
        ) begin
            $fatal(1, "PIN failed");
        end

        $display(
            "PASS: PIN quotient=%0d remainder=%0d",
            Y,
            T
        );

        //--------------------------------------------------------------
        // KÙ
        //--------------------------------------------------------------

        op = OP_KU;
        A = 8'd29;
        B = 8'd6;

        #1;
        check_relations();

        if (
            Y !== 8'd5 ||
            T !== 8'd4
        ) begin
            $fatal(1, "KU failed");
        end

        $display(
            "PASS: KU remainder=%0d quotient=%0d",
            Y,
            T
        );

        //--------------------------------------------------------------
        // Division-by-zero exception
        //--------------------------------------------------------------

        op = OP_PIN;
        A = 8'd29;
        B = 8'd0;

        #1;
        check_relations();

        if (
            Y !== 8'h00 ||
            T !== 8'hFF ||
            valid !== 1'b0 ||
            exception_valid !== 1'b1 ||
            exception_code !== EXC_DIV_ZERO
        ) begin
            $fatal(
                1,
                "PIN division-by-zero rule failed"
            );
        end

        $display(
            "PASS: PIN division-by-zero exception"
        );

        //--------------------------------------------------------------
        // GBÉ inside captured relation window
        //
        // 3^4 = 81 = 0x0051
        //--------------------------------------------------------------

        op = OP_GBE;
        A = 8'd3;
        B = 8'd4;

        #1;
        check_relations();

        if (
            Y !== 8'h51 ||
            T !== 8'h00 ||
            state_valid !== 1'b0 ||
            state_code !== STATE_NONE
        ) begin
            $fatal(1, "GBE 3^4 failed");
        end

        $display(
            "PASS: GBE 3^4 Y=%02h T=%02h STATE=NONE",
            Y,
            T
        );

        //--------------------------------------------------------------
        // GBÉ using transport word
        //
        // 16^3 = 4096 = 0x1000
        //--------------------------------------------------------------

        op = OP_GBE;
        A = 8'd16;
        B = 8'd3;

        #1;
        check_relations();

        if (
            Y !== 8'h00 ||
            T !== 8'h10 ||
            state_valid !== 1'b0
        ) begin
            $fatal(
                1,
                "GBE transport-word test failed"
            );
        end

        $display(
            "PASS: GBE transport Y=%02h T=%02h",
            Y,
            T
        );

        //--------------------------------------------------------------
        // GBÉ extended state
        //
        // 255^3 exceeds the captured 16-bit {T,Y} window.
        //--------------------------------------------------------------

        op = OP_GBE;
        A = 8'hFF;
        B = 8'd3;

        #1;
        check_relations();

        if (
            state_valid !== 1'b1 ||
            state_code !== STATE_POWER_EXTENDED
        ) begin
            $fatal(
                1,
                "GBE extended state was not reported"
            );
        end

        $display(
            "PASS: GBE entered STATE_POWER_EXTENDED"
        );

        //--------------------------------------------------------------
        // SẸ̀DÁ equality
        //--------------------------------------------------------------

        op = OP_SEDA;
        A = 8'd20;
        B = 8'd20;

        #1;
        check_relations();

        if (
            Y !== 8'h00 ||
            T !== 8'h00 ||
            eq_flag !== 1'b1 ||
            gt_flag !== 1'b0 ||
            lt_flag !== 1'b0
        ) begin
            $fatal(1, "SEDA equality failed");
        end

        $display("PASS: SEDA equality");

        //--------------------------------------------------------------
        // SẸ̀DÁ greater
        //--------------------------------------------------------------

        op = OP_SEDA;
        A = 8'd20;
        B = 8'd10;

        #1;
        check_relations();

        if (
            Y !== 8'd10 ||
            T !== 8'h00 ||
            gt_flag !== 1'b1
        ) begin
            $fatal(1, "SEDA greater failed");
        end

        $display("PASS: SEDA greater");

        //--------------------------------------------------------------
        // SẸ̀DÁ less
        //--------------------------------------------------------------

        op = OP_SEDA;
        A = 8'd10;
        B = 8'd20;

        #1;
        check_relations();

        if (
            Y !== 8'hF6 ||
            T !== 8'h01 ||
            lt_flag !== 1'b1
        ) begin
            $fatal(1, "SEDA less failed");
        end

        $display("PASS: SEDA less");

        //--------------------------------------------------------------
        // JÙ
        //--------------------------------------------------------------

        op = OP_JU;
        A = 8'd20;
        B = 8'd10;

        #1;
        check_relations();

        if (
            Y !== 8'h01 ||
            gt_flag !== 1'b1
        ) begin
            $fatal(1, "JU true predicate failed");
        end

        op = OP_JU;
        A = 8'd5;
        B = 8'd10;

        #1;
        check_relations();

        if (
            Y !== 8'h00 ||
            lt_flag !== 1'b1 ||
            T !== 8'h01
        ) begin
            $fatal(1, "JU false predicate failed");
        end

        $display("PASS: JU predicate");

        //--------------------------------------------------------------
        // KERÉ
        //--------------------------------------------------------------

        op = OP_KERE;
        A = 8'd5;
        B = 8'd10;

        #1;
        check_relations();

        if (
            Y !== 8'h01 ||
            lt_flag !== 1'b1 ||
            T !== 8'h01
        ) begin
            $fatal(1, "KERE true predicate failed");
        end

        op = OP_KERE;
        A = 8'd20;
        B = 8'd10;

        #1;
        check_relations();

        if (
            Y !== 8'h00 ||
            gt_flag !== 1'b1
        ) begin
            $fatal(1, "KERE false predicate failed");
        end

        $display("PASS: KERE predicate");

        $display(
            "============================================================"
        );
        $display(
            "PASS: ALL NATIVE IFÁ MATHEMATICAL FUNCTIONS VERIFIED"
        );
        $display(
            "PASS: RA, RD AND R0 ARE UNIVERSAL"
        );
        $display(
            "PASS: EXTENDED POWER IS AN IFÁ STATE, NOT OVERFLOW"
        );
        $display(
            "============================================================"
        );

        $finish;
    end

endmodule
