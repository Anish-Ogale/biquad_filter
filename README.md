# sky130_ip_scbiquad — clock-programmable SC biquad (Chipalooza #4)

**This repository contains preliminary simulation evidence supporting the
Chipalooza Challenge #4 proposal. It is not the final IC implementation.**

It is a **pre-layout feasibility prototype**: exact z-domain capacitor-budget
analysis, a behavioral ngspice switched-capacitor biquad, behavioral op-amp
requirement sweeps, an offset study, and a **transistor-level two-stage op-amp
proof-of-concept** with a preliminary 3-corner simulation. The transistor-level
switched-capacitor biquad, complete PVT qualification, and layout are **planned
post-acceptance implementation**.

**Reviewer path:** proposed architecture → exact z-domain / capacitor sizing →
behavioral verification → op-amp requirements → transistor-level op-amp
proof-of-concept → preliminary 3-corner simulation → known limitations →
post-acceptance plan.

## Proposed architecture

Fully differential, second-order switched-capacitor biquad with simultaneous
**low-pass** and **band-pass** outputs, in Sky130:

- **f0 = fclk/K**, K ∈ {25, 50, 100, 200}, fclk 10 kHz … 1 MHz
  (fclk ≤ 500 kHz at K = 25) → f0 = 50 Hz … 20 kHz
- **Q** in 8 steps, 0.5 … 5 (√2-spaced), exact z-domain (LDI) design
- **Gain** 0 / 6 / 12 / 18 dB by the input-branch cap `Cs1 = G*Cs`
  (G = 1, 2, 3.98, 7.94); LP gain = G, BP peak = G*Q, f0/Q unchanged
- **MiM capacitors only**, target budget ≤120 pF (exact table: 33.6–68.7 pF
  at 0 dB, 37.2–117.6 pF at 18 dB), area target ≤ 0.12 mm²
  (worst simulated MiM area 0.0585 mm²; MiM only, excludes switches,
  op-amps, bias and routing)
- VDDA 3.3 V (2.97–3.63), VDDD 1.8 V; 5 V devices for the analog core
  (Sky130 has no 3.3 V PMOS)
- **Built-in test**: an internal square wave (fclk/64 … /4096) can drive the
  input so f0/Q are measurable with just a scope
- Chip resources: 4 shared analog lines, 1 dedicated digital pad (CLK_IN),
  harness bias references, up to 24 control bits, 12 test outputs

## Demonstrated now

- exact capacitor-ratio / z-domain budget for all 32 (K, Q) settings
- behavioral switched-capacitor biquad compared with the exact discrete map
- LP gain steps 0/6/12/18 dB by the input-branch cap Cs1 = G*Cs
- behavioral op-amp gain/GBW/SR requirement sweeps
- differential-Q evidence at the real op-amp corners, step-ring vs multisine
  cross-check, and the targeted 18 dB / Q≤2 A0 requirement check
- input-offset study with a 5 mV op-amp offset, at 0 and 18 dB
- transistor-level two-stage op-amp (xschem schematic + committed netlist)
- preliminary 3-corner simulation of that op-amp (tt, ss, ff)
- reproducible figures with a committed provenance/values snapshot

## Planned after acceptance

- transistor-level switched-capacitor biquad
- complete 45-corner PVT qualification (5 processes × 3 supplies × 3 temperatures)
- mismatch / Monte Carlo verification
- THD verification
- final noise verification
- clock-feedthrough verification
- layout
- DRC/LVS
- pads and integration

## How to reproduce

Prerequisites: Python ≥ 3.10 with `numpy` and `matplotlib`, plus `ngspice`
for the simulation targets. A Sky130 PDK is required **only** for the
transistor-level op-amp and for viewing the Xschem schematic.

### PDK-free: exact analysis and behavioral verification

```bash
python3 -m pip install numpy matplotlib

make cap        # exact z-domain / capacitor table
make behav      # behavioral biquad sweeps, gain/offset/Q tests, f0/Q extraction
make plots      # regenerate results/plots/*.png and the figure snapshot
```

`make cap` needs only Python; `make behav` and `make plots` need ngspice but
use only the ideal/behavioral deck for the behavioral figures. Neither reads
the Sky130 PDK (the op-amp Bode figure in `make plots` is skipped when the PDK
is absent).

### Sky130-dependent: transistor-level op-amp and schematic

```bash
# PDK_ROOT may point to the directory containing sky130A, or to sky130A itself.
export PDK_ROOT=/path/to/sky130A     # e.g. $HOME/.volare/sky130A

make opamp                           # 3-corner Sky130 op-amp simulation
xschem design/opamp/opamp_2stage.sch # Sky130 MOSFET symbols in xschem
```

The op-amp simulation uses Sky130 ngspice models; the schematic uses the
Sky130 xschem symbol library. `make all` runs `cap`, `behav`, and `opamp`,
so `make all` requires the Sky130 PDK.

| Command | Sky130 needed? | Dependency / writes |
|---|---|---|
| `make cap` | no | Python only; writes `results/capbudget_table.md` and `results/data/capbudget_table.csv` (committed snapshot) |
| `make behav` | no | ngspice + behavioral deck; writes the committed CSV snapshots and Markdown under `results/behavioral/`, plus `results/data/` |
| `make opamp` | yes | Sky130 models; writes `results/opamp/opamp_corners.md` |
| `make qcross` | no | step-ring vs multisine Q cross-check; updates section (c) of `results/behavioral/q_evidence.md` |
| `make q2` | no | targeted Q≤2 / 18 dB A0/GBW check; updates section (b) of `results/behavioral/q_evidence.md` |
| `make plots` | no (op-amp panel: yes) | `sim/plots.py`; regenerates `results/plots/*.png` and `results/plots/README.md` |
| `make all` | yes | runs `cap`, `behav`, `opamp` (not `plots`) |
| `xschem …` | yes (symbols) | interactive schematic viewing only |

The CSV files under `results/data/` are committed snapshots, regenerated by
the make targets. The Markdown summaries and plots in `results/` are the
readable evidence; `results/README.md` indexes them.

## Status — simulated versus planned

| Check | Status | Result | Evidence |
|---|---|---|---|
| Capacitor budget | **simulated** [ANALYTICAL] | 33.6–68.7 pF at 0 dB, 37.2–117.6 pF at 18 dB (≤120 pF target); MiM area ≤0.0585 mm²; worst quantization f0 +1.24 % at K=200/Q=5 | `results/capbudget_table.md`, `results/spec_check.md` |
| Gain | **simulated** | LP gain 0/6/12/18 dB by `Cs1 = G*Cs`; worst gain error 0.060 dB | `results/behavioral/gain_test.md`, `results/spec_check.md` |
| Q | **simulated** | Differential-Q evidence at real corners; Q≤2 at 18 dB needs A0 ≥60 dB; K=200/Q=5 step-ring residual is not confirmed by multisine and is treated as an extraction artifact pending transistor-level measurement | `results/behavioral/q_evidence.md`, `results/spec_check.md` |
| Offset | **simulated** | 29.4 mV worst at 0 dB/Q≤2; 45.5 mV over all gain/Q; adopted max 40/60 mV | `results/behavioral/offset_test.md`, `results/behavioral/offset_opamp.md`, `results/spec_check.md` |
| Op-amp | **simulated** | A0 49.0–50.5 dB, GBW 7.8–13.9 MHz; ss misses the 50 dB/10 MHz minimums; all corners are below the 60 dB needed at 18 dB | `results/opamp/opamp_corners.md`, `results/spec_check.md` |
| Planned | **post-acceptance** | Full PVT, Monte Carlo, THD, noise, clock feedthrough, transistor-level biquad, layout/DRC/LVS | `results/spec_check.md`, `docs/plan.md` |

Spec changes are not silent: the adopted f0, IDDA, offset and cap-budget
adjustments are listed with their measured justification in
`results/spec_check.md`. Remaining misses (ss op-amp, the 60 dB A0 needed at
18 dB including the Q≤2 row, and the unconfirmed K=200/Q=5 step-ring
residual) are stated as limitations.

## Target specification (copy of `spec/spec.md` §3)

| Parameter | typ | max |
|---|---|---|
| f0 accuracy | ±1 % (K≤100), ±1.5 % (K=200) | ±3 % |
| Q accuracy | ±5 % | ±15 % (Q≤2), ±20 % (Q>2) |
| Gain error | ±0.5 dB | ±1 dB |
| Output swing | — | ±1 V differential (usable input = ±1 V / G; BP peak = G*Q) |
| THD (1 Vpp differential at LP output, f = f0/4) | −60 dB | −50 dB |
| Output noise (0.1 Hz–50 kHz) | 150 µVrms | 400 µVrms |
| Dynamic range | 70 dB | 62 dB min |
| Output offset | — | ±40 mV (0 dB, Q≤2, all K); ±60 mV (all gain/Q); assumed 5 mV op-amp input offset |
| Clock feedthrough | 5 mVpp | 20 mVpp |
| IDDA @ fclk = 1 MHz | 1.3 mA | 2.0 mA |
| IDDD @ 1 MHz | 40 µA | 100 µA |

## Current limitations

This proposal-stage prototype does **not** yet include:

- a transistor-level switched-capacitor biquad (the biquad itself is behavioral:
  ideal switches and behavioral op-amps)
- full 45-corner PVT qualification (only 3 op-amp corners are simulated)
- complete Monte Carlo mismatch verification
- THD verification
- final noise verification
- clock-feedthrough verification
- layout, DRC/LVS, pads, or digital control logic

Known quantitative limitations, already documented rather than hidden:

- **f0 typ at K=200/Q≥2.83**: quantization gives +0.93 … +1.24 %. This
  passes the adopted ±1.5 % K=200 typ spec but would fail the old ±1 %
  target; the max ±3 % target is met. An f0-priority trim remains an option.
- **IDDA**: 2 × op-amp current + replica gives 1.22 mA at tt; adopted spec is
  1.3 mA typ / 2.0 mA max at 1 MHz. The ff corner is 1.43 mA. The adopted max
  excludes output buffers, bias, CMFB and clock generation.
- **Op-amp gain/GBW**: A0 is 50.0/49.0/50.5 dB and GBW is 10.6/7.82/13.94 MHz
  (tt/ss/ff). tt/ff meet the 50 dB and 10 MHz minimums; ss misses both
  (49.0 dB, 7.82 MHz). All three fall short of the 60 dB A0 needed at 18 dB
  gain; the 80 dB goal is not met.
- **K=200/Q=5 Q accuracy**: the step-ring extraction gives Q −14.8 % (0 dB)
  and −15.1 % (18 dB) at the ideal 80 dB/10 MHz point, but the multisine
  cross-check gives +0.5 % and does not confirm this. It is likely a
  K=200 step-ring extraction artifact (few clean ringing peaks) and must be
  re-measured at transistor level.
- **Q≤2 at 18 dB**: with the current 49–50 dB op-amp corners the differential
  Q error is 5.0–6.3 % (K=25/Q=2 and K=200/Q=2), outside the ±5 % typ row but
  inside the ±15 % max. A targeted sweep shows 1.9 % worst at A0=60 dB,
  nearly independent of GBW 7.82–20 MHz (`results/behavioral/q_evidence.md`
  section b).
- **Offset**: 29.4 mV worst at 0 dB/Q≤2 and 45.5 mV over all gain/Q; both are
  within the adopted max 40/60 mV. Real tt/ss worst cases are 35.3/34.0 mV;
  ideal 80 dB worst is 53.5 mV.
- **Cap budget at 18 dB**: worst total 117.6 pF at K=25/Q=0.5, inside the
  adopted ≤120 pF target; MiM area is 0.0585 mm², below 0.12 mm².
- **Noise**: 66.7 µVrms at 0 dB and 87.2 µVrms at 18 dB are kT/C-only
  estimates [EST]; 1/f, op-amp, THD and clock-feedthrough terms are not
  included.
- **Q residual at 18 dB**: the real tt/ss op-amps give Q −11.2/−11.9 % at
  K=100/Q=5, inside the Q>2 max ±20 % but outside the Q±5 % sweep criterion.
  This and the unconfirmed K=200/Q=5 step-ring residual must be re-measured at
  transistor level.

## Tools and PDK

| Tool | Version | Notes |
|---|---|---|
| xschem | 3.4.8RC | schematic: `design/opamp/opamp_2stage.sch` |
| ngspice | 47 (KLU) | `.lib $PDK_ROOT/sky130A/libs.tech/ngspice/sky130.lib.spice <corner>` |
| Python | ≥ 3.10 (tested 3.14) | numpy, matplotlib only (no scipy/pandas) |
| PDK | sky130A (volare) | `PDK_ROOT` env var, default `~/.volare`; may point to the parent directory or to `sky130A` itself |

The repository ships a project-local `xschemrc`; it adds the Sky130 xschem
symbol library at `$PDK_ROOT/sky130A/libs.tech/xschem` and keeps the stock
xschem device symbols (`devices/lab_pin.sym`, `devices/capa.sym`, …) on the
search path. There are no personal absolute paths in the schematic.

To view the op-amp schematic:

```bash
export PDK_ROOT=/path/to/sky130A        # or its parent directory
cd /path/to/biquad_filter
xschem design/opamp/opamp_2stage.sch
```

Starting xschem from `design/opamp/` also works: its local `xschemrc` forwards
to the repository-root configuration. If the Sky130 symbols are not found,
check that `PDK_ROOT` contains `sky130A/libs.tech/xschem/sky130_fd_pr/`.

Modeling assumptions (what is ideal vs transistor-level) are listed in
`docs/architecture.md` §8; PVT corners actually run vs planned are in
`spec/corners.md`.

## Repository layout

```
spec/    spec.md (single source of truth), corners.md
docs/    architecture.md, io_and_controls.md, test_plan.md, plan.md
sim/     capbudget.py, plots.py; behavioral/ (biquad_behav.spice, run_sweep.py,
         offset_test.spice, extract_f0_q.py, q_crosscheck.py, q2_check.py,
         q_evidence.py)
design/  opamp/ (opamp_2stage.sch/.sym/.spice, tb_ac.spice, tb_step.spice,
         run_corners.sh, xschemrc)
results/ README.md index, summary.md, spec_check.md, capbudget_table.md,
         behavioral/ (sweeps, gain, offset, q_evidence.md),
         opamp/ (opamp_corners.md), data/ (committed CSV snapshots),
         plots/ (PNG figures + README.md snapshot)
xschemrc repository-local xschem library configuration
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
