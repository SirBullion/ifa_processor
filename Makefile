###############################################################################
# IFÁ REVERSIBLE PROCESSOR
# Makefile
###############################################################################

IVERILOG = iverilog
VVP      = vvp
GTKWAVE  = gtkwave

RTL = rtl
TB  = tb
SIM = sim

SVFLAGS = -g2012


###############################################################################
# Default
###############################################################################

all: p2 p4 p8 rm4 t8 recovery error corrector top

###############################################################################
# P2
###############################################################################

p2:
	$(IVERILOG) $(SVFLAGS) \
	$(RTL)/ifa_p2.sv \
	$(TB)/tb_p2.sv \
	-o $(SIM)/tb_p2.out
	$(VVP) $(SIM)/tb_p2.out

wave-p2:
	$(GTKWAVE) $(SIM)/p2.vcd

###############################################################################
# P4
###############################################################################

p4:
	$(IVERILOG) $(SVFLAGS) \
	$(RTL)/ifa_p2.sv \
	$(RTL)/ifa_p4.sv \
	$(TB)/tb_p4.sv \
	-o $(SIM)/tb_p4.out
	$(VVP) $(SIM)/tb_p4.out

wave-p4:
	$(GTKWAVE) $(SIM)/p4.vcd

###############################################################################
# P8
###############################################################################

p8:
	$(IVERILOG) $(SVFLAGS) \
	$(RTL)/ifa_p2.sv \
	$(RTL)/ifa_p4.sv \
	$(RTL)/ifa_p8.sv \
	$(TB)/tb_p8.sv \
	-o $(SIM)/tb_p8.out
	$(VVP) $(SIM)/tb_p8.out

wave-p8:
	$(GTKWAVE) $(SIM)/p8.vcd

###############################################################################
# Routing Matrix
###############################################################################

rm4:
	$(IVERILOG) $(SVFLAGS) \
	$(RTL)/ifa_rm4.sv \
	$(TB)/tb_rm4.sv \
	-o $(SIM)/tb_rm4.out
	$(VVP) $(SIM)/tb_rm4.out

wave-rm4:
	$(GTKWAVE) $(SIM)/rm4.vcd

###############################################################################
# Transport Matrix
###############################################################################

t8:
	$(IVERILOG) $(SVFLAGS) \
	$(RTL)/ifa_t8.sv \
	$(TB)/tb_t8.sv \
	-o $(SIM)/tb_t8.out
	$(VVP) $(SIM)/tb_t8.out

wave-t8:
	$(GTKWAVE) $(SIM)/t8.vcd

###############################################################################
# Recovery
###############################################################################

recovery:
	$(IVERILOG) $(SVFLAGS) \
	$(RTL)/ifa_p2.sv \
	$(RTL)/ifa_p4.sv \
	$(RTL)/ifa_p8.sv \
	$(RTL)/ifa_p2_inv.sv \
	$(RTL)/ifa_p4_inv.sv \
	$(RTL)/ifa_p8_inv.sv \
	$(TB)/tb_recovery.sv \
	-o $(SIM)/tb_recovery.out
	$(VVP) $(SIM)/tb_recovery.out

wave-recovery:
	$(GTKWAVE) $(SIM)/recovery.vcd

###############################################################################
# Error Transport
###############################################################################

error:
	$(IVERILOG) $(SVFLAGS) \
	$(RTL)/ifa_p2.sv \
	$(RTL)/ifa_p4.sv \
	$(RTL)/ifa_p8.sv \
	$(RTL)/ifa_p2_inv.sv \
	$(RTL)/ifa_p4_inv.sv \
	$(RTL)/ifa_p8_inv.sv \
	$(RTL)/ifa_t8.sv \
	$(TB)/tb_error_transport.sv \
	-o $(SIM)/tb_error_transport.out
	$(VVP) $(SIM)/tb_error_transport.out

wave-error:
	$(GTKWAVE) $(SIM)/error_transport.vcd

###############################################################################
# Corrector
###############################################################################

corrector:
	$(IVERILOG) $(SVFLAGS) \
	$(RTL)/ifa_p2.sv \
	$(RTL)/ifa_p4.sv \
	$(RTL)/ifa_p8.sv \
	$(RTL)/ifa_p2_inv.sv \
	$(RTL)/ifa_p4_inv.sv \
	$(RTL)/ifa_p8_inv.sv \
	$(RTL)/ifa_t8.sv \
	$(RTL)/ifa_corrector.sv \
	$(TB)/tb_corrector.sv \
	-o $(SIM)/tb_corrector.out
	$(VVP) $(SIM)/tb_corrector.out

wave-corrector:
	$(GTKWAVE) $(SIM)/corrector.vcd

###############################################################################
# Complete Processor
###############################################################################

top:
	$(IVERILOG) $(SVFLAGS) \
	$(RTL)/ifa_p2.sv \
	$(RTL)/ifa_p4.sv \
	$(RTL)/ifa_p8.sv \
	$(RTL)/ifa_rm4.sv \
	$(RTL)/ifa_t8.sv \
	$(RTL)/ifa_top.sv \
	$(TB)/tb_top.sv \
	-o $(SIM)/tb_top.out
	$(VVP) $(SIM)/tb_top.out

wave-top:
	$(GTKWAVE) $(SIM)/top.vcd

###############################################################################
# Clean
###############################################################################

clean:
	rm -f $(SIM)/*.out
	rm -f $(SIM)/*.vcd

###############################################################################
# Help
###############################################################################

help:
	@echo ""
	@echo "==============================="
	@echo " IFÁ REVERSIBLE PROCESSOR"
	@echo "==============================="
	@echo ""
	@echo "Simulation Targets"
	@echo "------------------"
	@echo "make p2"
	@echo "make p4"
	@echo "make p8"
	@echo "make rm4"
	@echo "make t8"
	@echo "make recovery"
	@echo "make error"
	@echo "make corrector"
	@echo "make top"
	@echo "make all"
	@echo ""
	@echo "Waveforms"
	@echo "---------"
	@echo "make wave-p2"
	@echo "make wave-p4"
	@echo "make wave-p8"
	@echo "make wave-rm4"
	@echo "make wave-t8"
	@echo "make wave-recovery"
	@echo "make wave-error"
	@echo "make wave-corrector"
	@echo "make wave-top"
	@echo ""
	@echo "Utilities"
	@echo "---------"
	@echo "make clean"
	@echo "make help"

###############################################################################
# CPU ROM Top
###############################################################################

cpu-rom:
	$(IVERILOG) $(SVFLAGS) \
	$(RTL)/ifa_p2.sv \
	$(RTL)/ifa_p4.sv \
	$(RTL)/ifa_p8.sv \
	$(RTL)/ifa_p2_inv.sv \
	$(RTL)/ifa_p4_inv.sv \
	$(RTL)/ifa_p8_inv.sv \
	$(RTL)/ifa_t8.sv \
	$(RTL)/ifa_rom.sv \
	$(RTL)/ifa_cpu_core.sv \
	$(RTL)/ifa_cpu_rom_top.sv \
	$(TB)/tb_cpu_rom_top.sv \
	-o $(SIM)/tb_cpu_rom_top.out
	$(VVP) $(SIM)/tb_cpu_rom_top.out

wave-cpu-rom:
	$(GTKWAVE) $(SIM)/cpu_rom_top.vcd

###############################################################################
# Assemble Demo Program
###############################################################################

assemble:
	python3 tools/ifaasm.py demo.ifa

run-program: assemble cpu-rom

###############################################################################
# Yosys Synthesis
###############################################################################

synth-cpu:
	yosys -s synth_cpu.ys

synth-fpga:
	yosys -s synth_fpga.ys

###############################################################################
# Ifa Monitor v1
###############################################################################

monitor:
	cp programs/monitor_v1.ifa demo.ifa
	python3 tools/ifaasm.py demo.ifa
	$(MAKE) cpu-rom
	@echo ""
	@echo "Monitor output saved to: sim/odu_all_output.txt"
	@echo ""
	@cat sim/odu_all_output.txt

###############################################################################
# IFÁ Processor V4
###############################################################################
V4_RTL = \
        rtl/v4/ifa_program_executor_v4.sv \
        rtl/v4/ifa_native_rau_v4.sv \
        rtl/v4/ifa_relation_memory_controller_admin.sv \
        rtl/v4/ifa_yara_manager.sv \
        rtl/v4/ifa_yara_context_bank.sv \
        rtl/v4/ifa_onile_supervisor.sv \
        rtl/v4/ifa_yara_frame_share_core.sv \
        rtl/v4/ifa_general_memory_guard.sv \
        rtl/v4/ifa_stack_memory_v4.sv \
        rtl/v4/ifa_onile_kernel_v4.sv

V45_RTL = \
        rtl/v45/ifa_phi_p8.sv \
        rtl/v45/ifa_relation_frame.sv \
        rtl/v45/ifa_yara_pe.sv \
        rtl/v45/ifa_yara_pe_bank4.sv \
        rtl/v45/ifa_yara_frame_share_core_v45.sv \
        rtl/v45/ifa_program_executor_v45.sv \
        rtl/v4/ifa_native_rau_v4.sv \
        rtl/v4/ifa_relation_memory_controller_admin.sv \
        rtl/v4/ifa_yara_manager.sv \
        rtl/v4/ifa_yara_context_bank.sv \
        rtl/v4/ifa_onile_supervisor.sv \
        rtl/v4/ifa_general_memory_guard.sv \
        rtl/v4/ifa_stack_memory_v4.sv \
        rtl/v45/ifa_onile_kernel_v45.sv


V4_BRIDGE_TB = tb/v4/tb_ifa_v4_os_bridge.sv
V4_BRIDGE    = sim/v4/ifa_v4_os_bridge.out
V45_BRIDGE_TB = tb/v45/tb_ifa_v45_os_bridge.sv
V45_BRIDGE    = sim/v45/ifa_v45_os_bridge.out

.PHONY: v4-build test-v4 clean-v4

v4-build:
	@mkdir -p sim/v4
	$(IVERILOG) $(SVFLAGS) \
		-o $(V4_BRIDGE) \
		$(V4_RTL) \
		$(V4_BRIDGE_TB)
	@echo "PASS: V4 bridge built"

test-v4:
	./tools/test_v4.sh

clean-v4:
	rm -f sim/v4/*.out
	rm -rf sim/v4/regression_logs
	rm -f programs_v4/_program_v4.hex
	rm -f programs_v4/_program_v4.lst
	rm -f programs_v4/_generated_v4.ifa4
.PHONY: v45-build

v45-build:
	@mkdir -p sim/v45
	$(IVERILOG) $(SVFLAGS) \
		-o $(V45_BRIDGE) \
		$(V45_RTL) \
		$(V45_BRIDGE_TB)
	@echo "PASS: V4.5 bridge built"


.PHONY: relation-frame-v45

relation-frame-v45:
	mkdir -p sim_v45
	iverilog \
		-g2012 \
		-Wall \
		-s tb_ifa_relation_frame \
		-o sim_v45/ifa_relation_frame.vvp \
		rtl/v45/ifa_relation_frame.sv \
		tb/v45/tb_ifa_relation_frame.sv
	vvp sim_v45/ifa_relation_frame.vvp


.PHONY: yara-pe-v45

yara-pe-v45:
	mkdir -p sim_v45
	iverilog \
		-g2012 \
		-Wall \
		-s tb_ifa_yara_pe \
		-o sim_v45/ifa_yara_pe.vvp \
		rtl/v45/ifa_yara_pe.sv \
		tb/v45/tb_ifa_yara_pe.sv
	vvp sim_v45/ifa_yara_pe.vvp

.PHONY: yara-pe-bank4-v45

yara-pe-bank4-v45:
	mkdir -p sim_v45
	iverilog \
		-g2012 \
		-Wall \
		-s tb_ifa_yara_pe_bank4 \
		-o sim_v45/ifa_yara_pe_bank4.vvp \
		rtl/v45/ifa_phi_p8.sv \
		rtl/v45/ifa_yara_pe.sv \
		rtl/v45/ifa_yara_pe_bank4.sv \
		tb/v45/tb_ifa_yara_pe_bank4.sv
	vvp sim_v45/ifa_yara_pe_bank4.vvp
