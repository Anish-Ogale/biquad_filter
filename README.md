# sky130_ip_scbiquad — clock-programmable SC biquad (Chipalooza #4)

Fully differential, second-order switched-capacitor biquad with simultaneous
**low-pass** and **band-pass** outputs, in Sky130:

- **f0 = fclk/K**, K ∈ {25, 50, 100, 200}, fclk 10 kHz … 1 MHz
  (fclk ≤ 500 kHz at K = 25) → f0 = 50 Hz … 20 kHz
- **Q** in 8 steps, 0.5 … 5 (√2-spaced), exact z-domain (LDI) design
- **Gain** 0 / 6 / 12 / 18 dB via an input capacitive attenuator
  (keeps f0, Q and offset independent of gain)
- **MiM capacitors only**, ~60–100 pF budget, area ≤ 0.12 mm²
- VDDA 3.3 V (2.97–3.63), VDDD 1.8 V; 5 V devices for the analog core
  (Sky130 has no 3.3 V PMOS)
- **Built-in test**: an internal square wave (fclk/64 … /4096) can drive the
  input so f0/Q are measurable with just a scope
- Chip resources: 4 shared analog lines, 1 dedicated digital pad (CLK_IN),
  harness bias references, up to 24 control bits, 12 test outputs

This repository is the **simulation-only, pre-layout feasibility prototype**
for the Chipalooza Challenge #4 proposal: exact discrete-time capacitor
budget, a behavioral ngspice biquad, a transistor-level two-stage op-amp
(xschem schematic + committed netlist), and a spec-check that separates
measured from planned evidence. No layout, no DRC/LVS, no pads.

## Status — simulated vs planned

| Check | Status | Result | Evidence |
|---|---|---|---|
| Capacitor budget, all 4 K × 8 Q (exact z-domain, CI = 8 pF) | **simulated** [ANALYTICAL] | total ≤ 54.6 pF, MiM area ≤ 0.036 mm²; worst quantization f0 +1.24 % at K=200/Q=5 | `results/capbudget_table.md` |
| Behavioral biquad vs exact map | **simulated** | amplitude ≤0.4 % (≤1.8 % at K=200/Q=5), phase ≤0.5° | `results/summary.md`, `results/plots/fig_step_response_tt.png` |
| Op-amp requirement sweep (A0 × GBW; K=100/Q=5 at 500 kHz and K=25/Q=1 at 1 MHz) | **simulated** | min A0 50 dB (40 dB fails: Q err −13 %); GBW ≥ 3 MHz at K=100/Q=5, ≥ 5 MHz at the 1 MHz worst case; SR 5 V/µs | `results/behav_sweep.csv` |
| Multisine f0/Q/gain extraction (10 tones, K=100/Q=5) | **simulated** | f0 +0.30 %, Q −3.36 % vs targets; step-ring fit shows a systematic ≤4.3 % Q residual (inside Q>2 typ budget, flagged) | `results/behav_tones.csv` |
| Offset test (5 mV op-amp VOS, all Q + extremes, both signs) | **simulated** | worst 11.6 mV (Q≤2) / 23.6 mV (all) vs ±30/±60 mV | `results/offset_test.md`, `results/plots/fig_offset_map_tt.png` |
| Transistor-level op-amp, 3 corners (tt, ss/110 °C, ff/−40 °C) | **simulated** | A0 49.0–50.5 dB, GBW 7.8–13.9 MHz, PM 52–62°, Idd 485–687 µA | `results/summary.md`, `results/plots/fig_opamp_bode_tt_ss_ff.png` |
| Transistor-level op-amp, full 45-corner PVT | **planned** | — | post-acceptance (`docs/plan.md`) |
| Op-amp Monte Carlo (mismatch) | **planned** | stock PDK mismatch is disabled; needs manual Pelgrom Vth — see `spec/corners.md` | — |
| THD, noise sim, clock feedthrough, transistor-level biquad | **planned** | noise currently estimated at 70–80 µVrms [EST] | post-acceptance (`docs/plan.md`) |
| Layout, DRC/LVS, pads | **out of scope** | — | proposal phase |

Misses are not relaxed silently: the f0-typ and IDDA-typ spec revisions are
listed in `results/spec_check.md` ("specs revised") and mirrored in
`spec/spec.md`.

## Target specification (copy of `spec/spec.md` §3)

| Parameter | typ | max |
|---|---|---|
| f0 accuracy | ±1 % | ±3 % |
| Q accuracy | ±5 % | ±15 % (Q≤2), ±20 % (Q>2) |
| Gain error | ±0.5 dB | ±1 dB |
| Input range | — | ±1 V diff |
| THD (1 Vpp diff, f = f0/4) | −60 dB | −50 dB |
| Output noise (0.1 Hz–50 kHz) | 150 µVrms | 400 µVrms |
| Dynamic range | 70 dB | 62 dB min |
| Output offset | ±30 mV (0 dB, Q≤2) | ±60 mV (all settings) |
| Clock feedthrough | 5 mVpp | 20 mVpp |
| IDDA @ fclk = 1 MHz | 0.8 mA | 1.5 mA |
| IDDD @ 1 MHz | 40 µA | 100 µA |

## How to run the checks

```bash
# 1. capacitor budget: exact z-domain table for every (K, Q)
make cap        # -> results/capbudget_table.{md,csv}

# 2. behavioral biquad: op-amp gain/GBW sweep, offset test, f0/Q extraction
make behav      # -> console table + results/

# 3. transistor-level op-amp: 3 corners (tt, ss/110C, ff/-40C)
make opamp      # -> one summary line per corner, console + results/

# everything:
make all
```

## Tools and PDK

| Tool | Version | Notes |
|---|---|---|
| xschem | 3.4.8RC | schematic: `design/opamp/opamp_2stage.sch` |
| ngspice | 47 (KLU) | `.lib $PDK_ROOT/sky130A/libs.tech/ngspice/sky130.lib.spice <corner>` |
| Python | ≥ 3.10 (tested 3.14) | numpy, matplotlib only (no scipy/pandas) |
| PDK | sky130A (volare) | `PDK_ROOT` env var, default `~/.volare` |

Modeling assumptions (what is ideal vs transistor-level) are listed in
`docs/architecture.md` §8; PVT corners actually run vs planned are in
`spec/corners.md`.

## Repository layout

```
spec/    spec.md (single source of truth), corners.md
docs/    architecture.md, io_and_controls.md, test_plan.md, plan.md
sim/     capbudget.py; behavioral/ (biquad_behav.spice, run_sweep.py,
         offset_test.spice, extract_f0_q.py)
design/  opamp/ (opamp_2stage.sch/.sym/.spice, tb_ac.spice, tb_step.spice,
         run_corners.sh)
results/ summary.md, spec_check.md, capbudget_table.md, plots/
```

## Plan

Milestones against the Chipalooza review gates (schematic week of
2026-12-28, layout week of 2027-02-01, final design review week of
2027-02-22), with owners and the risk list: **`docs/plan.md`**.

## License

Apache-2.0 — see `LICENSE`. The SPDX header
`SPDX-License-Identifier: Apache-2.0` appears on the first line of every
script and netlist (line 2 of `*.py`, which start with a shebang), and in the
header comment of the xschem `.sch`/`.sym` files (whose first line must stay
the xschem version banner).
