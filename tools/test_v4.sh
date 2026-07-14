#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BRIDGE="sim/v4/ifa_v4_os_bridge.out"
LOG_DIR="sim/v4/regression_logs"

mkdir -p sim/v4 "$LOG_DIR"

pass_count=0

pass() {
    pass_count=$((pass_count + 1))
    printf 'PASS: %s\n' "$1"
}

fail() {
    printf 'FAIL: %s\n' "$1" >&2
    exit 1
}

require_line() {
    local file="$1"
    local pattern="$2"
    local description="$3"

    if grep -Eq "$pattern" "$file"; then
        pass "$description"
    else
        echo
        echo "Expected pattern:"
        echo "    $pattern"
        echo
        echo "Output:"
        cat "$file"
        fail "$description"
    fi
}

echo "============================================================"
echo "IFÁ PROCESSOR V4 REGRESSION"
echo "============================================================"

#======================================================================
# 1. Python syntax
#======================================================================

python3 -m py_compile \
    tools/ifaasm_v4.py \
    tools/ifarun_v4.py \
    tools/ifa_yoruba_frontend_v4.py

pass "V4 Python tools compile"

#======================================================================
# 2. Build the V4 bridge
#======================================================================

rm -f "$BRIDGE"

iverilog -g2012 \
    -o "$BRIDGE" \
    rtl/v4/ifa_program_executor_v4.sv \
    rtl/v4/ifa_native_rau_v4.sv \
    rtl/v4/ifa_relation_memory_controller_admin.sv \
    rtl/v4/ifa_yara_manager.sv \
    rtl/v4/ifa_yara_context_bank.sv \
    rtl/v4/ifa_onile_supervisor.sv \
    rtl/v4/ifa_yara_frame_share_core.sv \
    rtl/v4/ifa_general_memory_guard.sv \
    rtl/v4/ifa_stack_memory_v4.sv \
    rtl/v4/ifa_onile_kernel_v4.sv \
    tb/v4/tb_ifa_v4_os_bridge.sv

pass "V4 RTL bridge compiles"

#======================================================================
# 3. Nine native operations
#
# The release bridge does not require per-instruction TRACE output.
# Verify all nine encodings in the generated listing, then verify that
# sequential execution reaches HALT after OP=8 with a valid result.
#======================================================================

./ifa4 programs_v4/native_nine_test.ifa4 --yara 0 \
    > "$LOG_DIR/native_nine.log"

NATIVE_LISTING="programs_v4/_program_v4.lst"

declare -a native_encodings=(
    '8000  PAPO'
    '8100  YO'
    '8200  DAGBA'
    '8300  PIN'
    '8400  KU'
    '8500  GBE'
    '8600  SEDA'
    '8700  JU'
    '8800  KERE'
)

for expected in "${native_encodings[@]}"; do
    require_line \
        "$NATIVE_LISTING" \
        "${expected}" \
        "Native encoding ${expected}"
done

require_line \
    "$LOG_DIR/native_nine.log" \
    'OK RUN ID=0 PC=0b .* OP=8 .* VALID=1' \
    "Nine native operations execute sequentially through HALT"

#======================================================================
# 4. RMU reuse
#
# The program performs the same PAPO operation twice. The final RUN
# summary accumulates whether any hit and any miss occurred.
#
#     first PAPO  -> MISS
#     second PAPO -> HIT
#
# Therefore the required final summary is HIT=1 MISS=1.
#======================================================================

./ifa4 programs_v4/rmu_reuse_test.ifa4 --yara 0 \
    > "$LOG_DIR/rmu_reuse.log"

require_line \
    "$LOG_DIR/rmu_reuse.log" \
    'OK RUN .*HIT=1 MISS=1 OP=0 .*Y=0b .*VALID=1' \
    "Repeated PAPO produces one RMU miss and one RMU hit"

#======================================================================
# 5. Operation-aware RMU identity
#
# Same operands produce the same relation components for PAPO and YO,
# but OP is part of the RMU key:
#
#     K = {OP, RA, RD, T}
#
# Expected sequence:
#
#     PAPO -> MISS
#     YO   -> MISS
#     PAPO -> HIT
#     YO   -> HIT
#======================================================================

cat > "$LOG_DIR/op_identity_commands.txt" <<'EOF'
BABALAWO ON
CREATE 0
SELECT 0
EXEC PAPO 09 02
EXEC YO 09 02
EXEC PAPO 09 02
EXEC YO 09 02
QUIT
EOF

vvp "$BRIDGE" \
    +CMD_FILE="$LOG_DIR/op_identity_commands.txt" \
    > "$LOG_DIR/op_identity.log"

require_line \
    "$LOG_DIR/op_identity.log" \
    'EXEC ID=0 OP=0 HIT=0 MISS=1 Y=0b RA=00 RD=0b R0=f4 T=00' \
    "PAPO creates its own RMU entry"

require_line \
    "$LOG_DIR/op_identity.log" \
    'EXEC ID=0 OP=1 HIT=0 MISS=1 Y=07 RA=00 RD=0b R0=f4 T=00' \
    "YO creates a separate RMU entry"

require_line \
    "$LOG_DIR/op_identity.log" \
    'EXEC ID=0 OP=0 HIT=1 MISS=0 Y=0b RA=00 RD=0b R0=f4 T=00' \
    "PAPO reuses only the PAPO entry"

require_line \
    "$LOG_DIR/op_identity.log" \
    'EXEC ID=0 OP=1 HIT=1 MISS=0 Y=07 RA=00 RD=0b R0=f4 T=00' \
    "YO reuses only the YO entry"

#======================================================================
# 6. Live YÀRÁ-local RMU isolation
#======================================================================

vvp "$BRIDGE" \
    +CMD_FILE=sim/v4/os_commands_yara_isolation.txt \
    > "$LOG_DIR/yara_isolation.log"

require_line \
    "$LOG_DIR/yara_isolation.log" \
    'EXEC ID=0 OP=0 HIT=0 MISS=1' \
    "YÀRÁ 0 first relation misses"

require_line \
    "$LOG_DIR/yara_isolation.log" \
    'EXEC ID=1 OP=0 HIT=0 MISS=1' \
    "YÀRÁ 1 has an independent RMU"

if [ "$(grep -Ec 'EXEC ID=0 OP=0 HIT=1 MISS=0' \
    "$LOG_DIR/yara_isolation.log")" -ge 2 ]; then
    pass "YÀRÁ 0 retains its RMU across switching"
else
    fail "YÀRÁ 0 retains its RMU across switching"
fi

#======================================================================
# 7. Exception and extended state
#======================================================================

./ifa4 programs_v4/pin_div_zero_test.ifa4 --yara 0 \
    > "$LOG_DIR/div_zero.log"

require_line \
    "$LOG_DIR/div_zero.log" \
    'OK RUN .*VALID=0 EXC=1 EXC_CODE=2' \
    "PIN division by zero propagates exception"

./ifa4 programs_v4/gbe_extended_state_test.ifa4 --yara 0 \
    > "$LOG_DIR/gbe_state.log"

require_line \
    "$LOG_DIR/gbe_state.log" \
    'OK RUN .*VALID=1 EXC=0 EXC_CODE=0 STATE=1 STATE_CODE=1' \
    "GBÉ extended state propagates"

#======================================================================
# 8. Branches and jump
#======================================================================

./ifa4 programs_v4/br_gt_test.ifa4 --yara 0 \
    > "$LOG_DIR/br_gt.log"

require_line \
    "$LOG_DIR/br_gt.log" \
    'OK RUN .*ADDR=2a FLAGS=02 .*GT=1 LT=0' \
    "BR_GT taken"

./ifa4 programs_v4/br_lt_test.ifa4 --yara 0 \
    > "$LOG_DIR/br_lt.log"

require_line \
    "$LOG_DIR/br_lt.log" \
    'OK RUN .*ADDR=3c FLAGS=01 .*GT=0 LT=1' \
    "BR_LT taken"

./ifa4 programs_v4/br_gt_not_taken_test.ifa4 --yara 0 \
    > "$LOG_DIR/br_not_taken.log"

require_line \
    "$LOG_DIR/br_not_taken.log" \
    'OK RUN .*ADDR=22 FLAGS=01 .*GT=0 LT=1' \
    "Conditional branch not taken"

./ifa4 programs_v4/jmp_test.ifa4 --yara 0 \
    > "$LOG_DIR/jmp.log"

require_line \
    "$LOG_DIR/jmp.log" \
    'OK RUN .*ADDR=55' \
    "JMP reaches target"

#======================================================================
# 9. Memory security
#======================================================================

vvp "$BRIDGE" \
    +CMD_FILE=sim/v4/os_commands_memory_nonowner_deny.txt \
    > "$LOG_DIR/memory_nonowner.log"

require_line \
    "$LOG_DIR/memory_nonowner.log" \
    'DENY MEMWRITE ID=1 ADDR=3' \
    "Non-owner memory write denied"

vvp "$BRIDGE" \
    +CMD_FILE=sim/v4/os_commands_memory_per_address.txt \
    > "$LOG_DIR/memory_address.log"

require_line \
    "$LOG_DIR/memory_address.log" \
    'OK MEMREAD ID=1 ADDR=3 DATA=a5' \
    "Granted address is readable"

require_line \
    "$LOG_DIR/memory_address.log" \
    'DENY MEMREAD ID=1 ADDR=4' \
    "Permission is isolated per address"

vvp "$BRIDGE" \
    +CMD_FILE=sim/v4/os_commands_memory_per_yara.txt \
    > "$LOG_DIR/memory_yara.log"

require_line \
    "$LOG_DIR/memory_yara.log" \
    'DENY MEMREAD ID=2 ADDR=3' \
    "Permission is isolated per YÀRÁ"

vvp "$BRIDGE" \
    +CMD_FILE=sim/v4/os_commands_memory_destroy_cleanup.txt \
    > "$LOG_DIR/memory_destroy.log"

require_line \
    "$LOG_DIR/memory_destroy.log" \
    'DENY MEMREAD ID=1 ADDR=3' \
    "Destroy clears memory permissions"

#======================================================================
# 10. Lifecycle and invalid IDs
#======================================================================

vvp "$BRIDGE" \
    +CMD_FILE=sim/v4/os_commands_pause_blocks_run.txt \
    > "$LOG_DIR/pause.log"

require_line \
    "$LOG_DIR/pause.log" \
    'DENY RUN YARA_PAUSED ID=0' \
    "Paused YÀRÁ cannot run"

vvp "$BRIDGE" \
    +CMD_FILE=sim/v4/os_commands_resume_allows_run.txt \
    > "$LOG_DIR/resume.log"

require_line \
    "$LOG_DIR/resume.log" \
    'OK RUN ID=0 .*Y=0d .*VALID=1' \
    "Resumed YÀRÁ executes"

vvp "$BRIDGE" \
    +CMD_FILE=sim/v4/os_commands_destroy_blocks_run.txt \
    > "$LOG_DIR/destroy.log"

require_line \
    "$LOG_DIR/destroy.log" \
    'DENY RUN NO_ACTIVE_YARA' \
    "Destroyed YÀRÁ cannot run"

vvp "$BRIDGE" \
    +CMD_FILE=sim/v4/os_commands_invalid_yara_id.txt \
    > "$LOG_DIR/invalid_yara.log"

for command in CREATE SELECT PAUSE RESUME DESTROY; do
    require_line \
        "$LOG_DIR/invalid_yara.log" \
        "DENY ${command} ID=16" \
        "Invalid ${command} ID is denied"
done

#======================================================================
# 11. Frame delegation security
#======================================================================

vvp "$BRIDGE" \
    +CMD_FILE=sim/v4/os_commands_frame_delegation.txt \
    > "$LOG_DIR/frame_delegation.log"

require_line \
    "$LOG_DIR/frame_delegation.log" \
    'DENY SHARE SRC=0 DST=1' \
    "Frame share denied before permission"

require_line \
    "$LOG_DIR/frame_delegation.log" \
    'OK SHARE SRC=0 DST=1' \
    "Frame share allowed after grant"

require_line \
    "$LOG_DIR/frame_delegation.log" \
    'FRAME OP=2 Y=12 RA=00 RD=0b R0=f4 T=00' \
    "Delegation preserves complete operation-aware frame"

vvp "$BRIDGE" \
    +CMD_FILE=sim/v4/os_commands_self_share_deny.txt \
    > "$LOG_DIR/self_share.log"

require_line \
    "$LOG_DIR/self_share.log" \
    'DENY GRANT SRC=0 DST=0' \
    "Self-grant denied"

require_line \
    "$LOG_DIR/self_share.log" \
    'DENY SHARE SRC=0 DST=0' \
    "Self-share denied"

#======================================================================
# 12. Program-controlled output
#======================================================================

./ifa4 programs_v4/print_all_test.ifa4 --yara 0 \
    > "$LOG_DIR/print_all.log"

declare -a prints=(
    'PRINT KIND=1 DATA=02'
    'PRINT KIND=2 DATA=04'
    'PRINT KIND=3 DATA=0b'
    'PRINT KIND=4 DATA=f0'
    'PRINT KIND=5 DATA=01'
    'PRINT KIND=6 DATA=03'
    'PRINT KIND=7 DATA=80'
)

for expected in "${prints[@]}"; do
    require_line \
        "$LOG_DIR/print_all.log" \
        "^${expected}$" \
        "${expected}"
done

#======================================================================
# 13. Yorùbá V4 pipeline
#======================================================================

./ifa4 programs_v4/yoruba_nine_test.ifa4y --yara 0 \
    > "$LOG_DIR/yoruba_nine.log"

for op in 00 01 02 03 04 05 06 07 08; do
    require_line \
        "$LOG_DIR/yoruba_nine.log" \
        "PRINT KIND=6 DATA=${op}" \
        "Yorùbá native OP=${op} executes"
done

require_line \
    "$LOG_DIR/yoruba_nine.log" \
    'OK RUN .*OP=8 .*VALID=1 EXC=0 EXC_CODE=0 STATE=0 STATE_CODE=0 EQ=0 GT=1 LT=0' \
    "Yorùbá program reports latest-operation status"

#======================================================================
# 14. Stack Pointer context isolation and preservation
#======================================================================

cat > "$LOG_DIR/sp_context_isolation.txt" <<'EOF'
BABALAWO ON
CREATE 0
CREATE 1

SELECT 0
CONTEXT 10 1111 aa bb 03 05 2c

SELECT 1
CONTEXT 20 2222 cc dd 04 06 7e

SELECT 0
STATUS

SELECT 1
STATUS

QUIT
EOF

vvp "$BRIDGE" \
    +CMD_FILE="$LOG_DIR/sp_context_isolation.txt" \
    > "$LOG_DIR/sp_context_isolation.log"

require_line \
    "$LOG_DIR/sp_context_isolation.log" \
    'ACTIVE_ID=0' \
    "YÀRÁ 0 selected for SP verification"

require_line \
    "$LOG_DIR/sp_context_isolation.log" \
    'CONTEXT PC=10 IR=1111 A=aa B=bb ADDR=03 FLAGS=05 SP=2c' \
    "YÀRÁ 0 preserves independent SP"

require_line \
    "$LOG_DIR/sp_context_isolation.log" \
    'ACTIVE_ID=1' \
    "YÀRÁ 1 selected for SP verification"

require_line \
    "$LOG_DIR/sp_context_isolation.log" \
    'CONTEXT PC=20 IR=2222 A=cc B=dd ADDR=04 FLAGS=06 SP=7e' \
    "YÀRÁ 1 preserves independent SP"

cat > "$LOG_DIR/sp_run_preserve.txt" <<'EOF'
BABALAWO ON
CREATE 0
SELECT 0

CONTEXT 00 0000 00 00 00 00 2c

LOAD 00 1005
LOAD 01 2008
LOAD 02 8000
LOAD 03 f100

RUN
STATUS
QUIT
EOF

vvp "$BRIDGE" \
    +CMD_FILE="$LOG_DIR/sp_run_preserve.txt" \
    > "$LOG_DIR/sp_run_preserve.log"

require_line \
    "$LOG_DIR/sp_run_preserve.log" \
    'OK RUN ID=0 PC=03 .*A=05 B=08 .*Y=0d .*VALID=1' \
    "Program executes normally with SP context"

require_line \
    "$LOG_DIR/sp_run_preserve.log" \
    'CONTEXT PC=03 IR=8000 A=05 B=08 ADDR=00 FLAGS=00 SP=2c' \
    "Normal program execution preserves SP"

#======================================================================
# 15. IFÁ relation-stack, CALL and RET
#======================================================================

#----------------------------------------------------------------------
# RPUSH/RPOP: restore the complete preserved relation
#----------------------------------------------------------------------

RPOP_RESTORE_LOG="$LOG_DIR/rpop_restore.log"

vvp "$BRIDGE" \
    +CMD_FILE=sim/v4/os_commands_rpop_restore.txt \
    > "$RPOP_RESTORE_LOG"

require_line \
    "$RPOP_RESTORE_LOG" \
    'OK LOAD ADDR=03 IR=f900' \
    "RPUSH encoding F900 executes"

require_line \
    "$RPOP_RESTORE_LOG" \
    'OK LOAD ADDR=05 IR=fa00' \
    "RPOP encoding FA00 executes"

require_line \
    "$RPOP_RESTORE_LOG" \
    'PRINT KIND=1 DATA=02' \
    "RPOP restores relation result Y"

require_line \
    "$RPOP_RESTORE_LOG" \
    'FRAME OP=3 Y=02 RA=04 RD=0b R0=f0 T=01' \
    "RPOP restores complete operation-aware relation"

require_line \
    "$RPOP_RESTORE_LOG" \
    'CONTEXT PC=0d IR=f800 A=0d B=06 ADDR=00 FLAGS=00 SP=00' \
    "RPOP decrements SP after restoration"

require_line \
    "$RPOP_RESTORE_LOG" \
    'STACK TRANSPORT=0 RELATION_ABSENT=0' \
    "Successful RPOP clears relation-stack conditions"

#----------------------------------------------------------------------
# RPOP with no preserved relation
#----------------------------------------------------------------------

RPOP_ABSENT_LOG="$LOG_DIR/rpop_absent.log"

vvp "$BRIDGE" \
    +CMD_FILE=sim/v4/os_commands_rpop_absent.txt \
    > "$RPOP_ABSENT_LOG"

require_line \
    "$RPOP_ABSENT_LOG" \
    'STACK TRANSPORT=0 RELATION_ABSENT=1' \
    "RPOP from an empty relation stack reports RELATION_ABSENT"

require_line \
    "$RPOP_ABSENT_LOG" \
    'CONTEXT PC=01 IR=fa00 A=00 B=00 ADDR=00 FLAGS=00 SP=00' \
    "RELATION_ABSENT leaves SP unchanged"

#----------------------------------------------------------------------
# CALL/RET continuation and relation restoration
#----------------------------------------------------------------------

CALL_RET_LOG="$LOG_DIR/call_ret_basic.log"

vvp "$BRIDGE" \
    +CMD_FILE=sim/v4/os_commands_call_ret_basic.txt \
    > "$CALL_RET_LOG"

require_line \
    "$CALL_RET_LOG" \
    'OK LOAD ADDR=03 IR=fb07' \
    "CALL target encoding FBtt executes"

require_line \
    "$CALL_RET_LOG" \
    'OK LOAD ADDR=08 IR=fc00' \
    "RET encoding FC00 executes"

require_line \
    "$CALL_RET_LOG" \
    'PRINT KIND=6 DATA=03' \
    "RET restores the preserved operation identity"

require_line \
    "$CALL_RET_LOG" \
    'FRAME OP=3 Y=02 RA=04 RD=0b R0=f0 T=01' \
    "RET restores the complete preserved relation"

require_line \
    "$CALL_RET_LOG" \
    'CONTEXT PC=05 IR=f700 A=0d B=06 ADDR=00 FLAGS=00 SP=00' \
    "CALL and RET restore continuation and SP"

require_line \
    "$CALL_RET_LOG" \
    'STACK TRANSPORT=0 RELATION_ABSENT=0' \
    "Successful CALL and RET clear relation-stack conditions"

#----------------------------------------------------------------------
# STACK_TRANSPORT on attempted RPUSH beyond the local relation window
#----------------------------------------------------------------------

STACK_TRANSPORT_LOG="$LOG_DIR/stack_transport.log"

vvp "$BRIDGE" \
    +CMD_FILE=sim/v4/os_commands_stack_transport.txt \
    > "$STACK_TRANSPORT_LOG"

require_line \
    "$STACK_TRANSPORT_LOG" \
    'STACK TRANSPORT=1 RELATION_ABSENT=0' \
    "RPUSH beyond the local relation window reports STACK_TRANSPORT"

require_line \
    "$STACK_TRANSPORT_LOG" \
    'CONTEXT PC=04 IR=f900 A=0d B=06 ADDR=00 FLAGS=00 SP=10' \
    "STACK_TRANSPORT leaves SP unchanged"

#----------------------------------------------------------------------
# CALL transport prevents control transfer
#----------------------------------------------------------------------

CALL_TRANSPORT_LOG="$LOG_DIR/call_transport.log"

vvp "$BRIDGE" \
    +CMD_FILE=sim/v4/os_commands_call_transport.txt \
    > "$CALL_TRANSPORT_LOG"

require_line \
    "$CALL_TRANSPORT_LOG" \
    'STACK TRANSPORT=1 RELATION_ABSENT=0' \
    "CALL beyond the local relation window reports STACK_TRANSPORT"

require_line \
    "$CALL_TRANSPORT_LOG" \
    'CONTEXT PC=05 IR=f700 A=0d B=06 ADDR=00 FLAGS=00 SP=10' \
    "Transported CALL does not enter the target"

require_line \
    "$CALL_TRANSPORT_LOG" \
    'PRINT KIND=6 DATA=03' \
    "Transported CALL preserves the current relation"

#----------------------------------------------------------------------
# Per-YÀRÁ relation-stack isolation
#----------------------------------------------------------------------

STACK_ISOLATION_LOG="$LOG_DIR/stack_yara_isolation.log"

vvp "$BRIDGE" \
    +CMD_FILE=sim/v4/os_commands_stack_yara_isolation.txt \
    > "$STACK_ISOLATION_LOG"

require_line \
    "$STACK_ISOLATION_LOG" \
    'OK STACKREAD SP=03 DATA=a5' \
    "YÀRÁ 0 retains its private stack entry"

require_line \
    "$STACK_ISOLATION_LOG" \
    'OK STACKREAD SP=03 DATA=5a' \
    "YÀRÁ 1 retains its private stack entry"

echo
echo "============================================================"
echo "PASS: IFÁ PROCESSOR V4 REGRESSION"
echo "PASS COUNT: $pass_count"
echo "============================================================"
