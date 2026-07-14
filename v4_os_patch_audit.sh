#!/bin/bash

OUT=~/ifa_v4_os_patch_audit.txt

echo "============================================================" > "$OUT"
echo "IFA V4 OS PATCH AUDIT" >> "$OUT"
echo "============================================================" >> "$OUT"
echo >> "$OUT"

echo "PWD" >> "$OUT"
pwd >> "$OUT"
echo >> "$OUT"

echo "============================================================" >> "$OUT"
echo "DIRECTORY STRUCTURE" >> "$OUT"
echo "============================================================" >> "$OUT"
find monitor language_v3 tools rtl rtl_v2 rtl_v3 rtl/v4 tb/v4 2>/dev/null | sort >> "$OUT"
echo >> "$OUT"

echo "============================================================" >> "$OUT"
echo "MONITOR FILE" >> "$OUT"
echo "============================================================" >> "$OUT"
cat monitor/ifa_monitor.py 2>/dev/null >> "$OUT"
echo >> "$OUT"

echo "============================================================" >> "$OUT"
echo "COMMAND REFERENCES" >> "$OUT"
echo "============================================================" >> "$OUT"
grep -RniE \
"PAPO|YO|SEDA|PRINTODU|PRINTODUALL|OYELA|OYELAA|STATUS|HELP|TRACE|CLEAN|BABALAWO|ONILE|YARA|ITAN|PADA|TUN" \
monitor language_v3 tools 2>/dev/null >> "$OUT"
echo >> "$OUT"

echo "============================================================" >> "$OUT"
echo "BACKEND / EXECUTION REFERENCES" >> "$OUT"
echo "============================================================" >> "$OUT"
grep -RniE \
"subprocess|socket|serial|uart|iverilog|vvp|assemble|assembler|hex|machine|compile|run|execute|writemem|readmem" \
monitor language_v3 tools 2>/dev/null >> "$OUT"
echo >> "$OUT"

echo "============================================================" >> "$OUT"
echo "ODU TABLES" >> "$OUT"
echo "============================================================" >> "$OUT"
grep -RniE \
"OGBE|OYEKU|IWORI|ODI|IROSUN|OWONRIN|OBARA|OKANRAN|OGUNDA|OSA|IKA|OTURUPON|OTURA|IRETE|OSE|OFUN|ODU" \
monitor language_v3 tools python rtl rtl_v2 rtl_v3 rtl/v4 2>/dev/null >> "$OUT"
echo >> "$OUT"

echo "============================================================" >> "$OUT"
echo "BABALAWO / SECURITY" >> "$OUT"
echo "============================================================" >> "$OUT"
grep -RniE \
"BABALAWO|ONILE|privilege|permission|security|grant|revoke|share|yara" \
monitor language_v3 tools rtl/v4 2>/dev/null >> "$OUT"
echo >> "$OUT"

echo "============================================================" >> "$OUT"
echo "END OF REPORT" >> "$OUT"

echo
echo "Saved:"
echo "$OUT"
