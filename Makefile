# SPDX-License-Identifier: Apache-2.0
#
# sky130_ip_scbiquad -- simulation-only feasibility prototype
#
# Targets:
#   make cap    : capacitor-ratio table for every (K, Q)  -> results/capbudget_table.md
#   make behav  : behavioral biquad -- op-amp sweep + offset test
#   make opamp  : transistor-level op-amp, 3 corners (tt, ss/110C, ff/-40C)
#   make all    : all of the above
#
# Prerequisites: python3 (numpy, matplotlib), ngspice, Sky130A PDK.
# PDK_ROOT may point at the PDK install (default: ~/.volare).

PYTHON  ?= python3
NGSPICE ?= ngspice
PDK_ROOT ?= $(HOME)/.volare
export PDK_ROOT

.PHONY: all cap behav opamp clean

all: cap behav opamp

cap:
	$(PYTHON) sim/capbudget.py

behav:
	$(PYTHON) sim/behavioral/run_sweep.py
	$(PYTHON) sim/behavioral/run_sweep.py --mode offset
	$(PYTHON) sim/behavioral/extract_f0_q.py

opamp:
	bash design/opamp/run_corners.sh

clean:
	rm -f sim/behavioral/*.dat sim/behavioral/*.gen.spice results/*.csv
	find . -name __pycache__ -type d -exec rm -rf {} +
