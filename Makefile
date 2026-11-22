# SPDX-License-Identifier: Apache-2.0
#
# sky130_ip_scbiquad -- simulation-only feasibility prototype
#
# Targets:
#   make cap    : capacitor-ratio table for every (K, Q)  -> results/capbudget_table.md
#   make behav  : behavioral biquad -- op-amp requirement sweep, gain test,
#                 offset matrix, real-op-amp offset check, Q evidence, f0/Q
#                 extraction
#   make opamp  : transistor-level op-amp, 3 corners (tt, ss/110C, ff/-40C)
#   make qcross : step-ring vs multisine Q cross-check
#   make q2     : targeted Q<=2 / 18 dB A0-GBW requirement check
#   make plots  : regenerate results/plots/*.png and the figure snapshot
#   make all    : all of the above simulation targets (not plots)
#
# Prerequisites: python3 (numpy, matplotlib), ngspice, Sky130A PDK.
# PDK_ROOT may point at the directory containing sky130A or at sky130A
# itself (default: ~/.volare).

PYTHON  ?= python3
NGSPICE ?= ngspice
PDK_ROOT ?= $(HOME)/.volare
export PDK_ROOT

.PHONY: all cap behav opamp qcross q2 plots clean

all: cap behav opamp

cap:
	$(PYTHON) sim/capbudget.py

behav:
	$(PYTHON) sim/behavioral/run_sweep.py
	$(PYTHON) sim/behavioral/run_sweep.py --mode gain
	$(PYTHON) sim/behavioral/run_sweep.py --mode offset
	$(PYTHON) sim/behavioral/run_sweep.py --mode offset-opamp
	$(PYTHON) sim/behavioral/run_sweep.py --mode qcheck
	$(PYTHON) sim/behavioral/q2_check.py
	$(PYTHON) sim/behavioral/extract_f0_q.py

opamp:
	bash design/opamp/run_corners.sh

qcross:
	$(PYTHON) sim/behavioral/q_crosscheck.py

q2:
	$(PYTHON) sim/behavioral/q2_check.py

plots: cap
	$(PYTHON) sim/plots.py

clean:
	rm -f sim/behavioral/*.dat sim/behavioral/*.gen.spice results/*.csv
	rm -f design/opamp/*.gen.spice design/opamp/*.dat design/opamp/*.log
	find . -name __pycache__ -type d -exec rm -rf {} +
