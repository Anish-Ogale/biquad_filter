# Plan — milestones against Chipalooza review gates

Challenge #4 review gates (Chip Foundry schedule):

| Gate | Date | Deliverable expected |
|---|---|---|
| Proposal | 2026-11-23 | This feasibility study + spec (spec/spec.md) |
| **Schematic review** | week of **2026-12-28** | complete xschem schematics: biquad, attenuator, bias, test support, pins; pass conceptual review |
| **Layout review** | week of **2027-02-01** | full layout, DRC/LVS clean, floorplan within 0.12 mm² |
| **Final submission** | week of **2027-02-22** | extracted simulation results over PVT, final report |

## Milestones

Single-team effort; owners to be assigned at M1. Proposal (M0) complete.

### M0 — Proposal (done 2026-11-23)
- [x] Toolchain audit, exact z-domain model, cap budget, behavioral biquad
      validated against the z-model, behavioral op-amp requirement sweep,
      offset test across all gain/Q, transistor-level op-amp (xschem
      schematic, netlist-equivalence-verified) at 3 corners — all in `results/`.

### M1 — Schematic-complete (schematic review, week of 2026-12-28)
1. xschem: input attenuator + biquad core (double-plate switching per
   docs/architecture.md §3), op-amp (done, `design/opamp/`), bias block
   (60 µA replica), non-overlap clock generator + level interfaces, BIT
   oscillator/divider, I/O assignment.
2. Behavioral full-chip testbench (ideal clocks + transistor blocks mixed as
   needed) revalidating f0/Q/gain at the 4 K × 8 Q matrix.
3. Freeze cap values incl. trim arrays; update `sim/capbudget.py` outputs.
Risks at this gate: absent 3.3 V PMOS (already mitigated: 5 V devices);
missing 5 V mismatch models in stock PDK (manual Pelgrom compensation, must be
documented in the review packet); BP gain = G·Q normalization decision.

### M2 — Layout (week of 2027-02-01)
1. Floorplan: cap array (dominant, ~50–78 pF MiM ≈ 0.04–0.05 mm² with dummies)
   + op-amp + switches + clocking, target ≤ 0.12 mm².
2. Matching strategy: common-centroid CI/Cs/Cd, unit-cap layout, guard rings;
   early-phase clock routing matched to the fF.
3. DRC/LVS clean, then RC extraction.
Risks: MiM cap density rules (2 fF/µm² + perimeter term) inflate area if
perimeter dominates at small Cd; switch leakage at 110 °C; CMFB stability
under layout parasitics; clock feedthrough through substrate.

### M3 — Post-layout PVT + submission (week of 2027-02-22)
1. Extracted sims: full 5-proc × 3-supply × 3-temp grid + MC on the extracted
   netlist; the −40…+110 °C proposal commitment is met or specs revised.
2. Final report: spec-check table, test plan (docs/test_plan.md), revised
   specs, measured-vs-simulated mapping for silicon bring-up.

## Risk list (tracked)

| # | Risk | Impact | Mitigation / status |
|---|---|---|---|
| 1 | Op-amp A0 ≈ 50 dB is near the 316× behavioral floor | Q accuracy at Q = 5 drifts a few % | characterized [SIM]; if transistor-level biquad shows Q err beyond typ, add a gain boost (cascode or longer-L), costs headroom — decide at M1 |
| 2 | No 3.3 V PMOS in Sky130 | levels/complexity | 5 V CMOS everywhere on the analog side (frozen) |
| 3 | PDK mismatch models disabled (MC_MM_SWITCH, vth0_slope=0) | offset/noise MC optimistic | manual Pelgrom Vth + MiM 2.8 %/√WL Python MC; disclosed in every spec-check row it touches |
| 4 | Offset at 18 dB / Q = 5 | worst-case ±60 mV row | behavioral offset test across all settings (python3 sim/behavioral/run_sweep.py --mode offset) |
| 5 | Damping cap 50 fF at K=200/Q=5 vs CI 8 pF | Q accuracy, junction effects | CI=8 pF decision + 3-bit trim; flagged red in capbudget |
| 6 | Charge injection / clock feedthrough | clock feedthrough 5/20 mVpp rows | double-plate + early phase; quantify at M1 with transistor-level switches |
| 7 | Fast schedule (schematic gate 5 weeks after proposal) | review readiness | scope frozen to the 24-hour-critical-path subset; full PVT deferred to M3 |
| 8 | ngspice-47 + sky130 corner lib quirks (subckt OP basins, hsa B-source parsing, clock pulse units, NFET bulk) | wasted simulation cycles | all traps documented in results/summary.md "toolchain notes" and encoded in the generators |
| 9 | f0 typ ±1 % fails at K=200/Q≥2.83 by quantization alone (+0.93…+1.24 %) | one spec row FAIL at proposal time | measured [ANALYTICAL]; proposal: split typ ±1 % (K≤100) / ±1.5 % (K=200), or fine-trim priority for f0 — needs user sign-off (spec_check.md §revised) |
| 10 | IDDA typ 0.8 mA vs measured 1.22 mA (2×op-amp + replica) | spec row FAIL at typ; ff corner 1.43 mA is at 95 % of the 1.5 mA max | measured [SIM]; proposal: typ 1.2 mA, or post-acceptance class-AB second stage / bias mode scaling with fclk |
