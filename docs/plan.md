# Plan — milestones against Chipalooza review gates

Challenge #4 review gates (Chip Foundry schedule):

| Gate | Date | Deliverable expected |
|---|---|---|
| Proposal | 2026-11-23 | This feasibility study + spec (spec/spec.md) |
| **Schematic review** | week of **2026-12-28** | complete xschem schematics: biquad, input gain branch, bias, test support, pins; pass conceptual review |
| **Layout review** | week of **2027-02-01** | full layout, DRC/LVS clean, floorplan within 0.12 mm² |
| **Final submission** | week of **2027-02-22** | extracted simulation results over PVT, final report |

## Milestones

Two-person team (analog filter owner, DLL owner is a separate
project); owners per milestone assigned at M1. Proposal (M0) complete.

### M0 — Proposal (completed with the proposal submission)
- [x] Toolchain audit, exact z-domain model, cap budget, behavioral biquad
      validated against the z-model, behavioral op-amp requirement sweep,
      offset test across all gain/Q, transistor-level op-amp (xschem
      schematic, netlist-equivalence-verified) at 3 corners — all in `results/`.

### M1 — Schematic-complete (schematic review, week of 2026-12-28)
1. xschem: input gain cap bank + biquad core (double-plate switching per
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
| 1 | Op-amp A0 is 49.0–50.5 dB; the 18 dB-gain sweep needs A0 ≥60 dB | ss misses 50 dB/10 MHz; Q error is −11…−12 % at 18 dB/K=100/Q=5 and 5.0–6.3 % for Q≤2 at 18 dB | characterized [SIM]; A0=60 dB brings Q≤2 inside 5 % (`results/behavioral/q_evidence.md` section b); improve A0 to ≥60 dB (cascode or longer-L) or qualify only 0/6/12 dB at ss — decide at M1 |
| 2 | No 3.3 V PMOS in Sky130 | levels/complexity | 5 V CMOS everywhere on the analog side (frozen) |
| 3 | PDK mismatch models disabled (MC_MM_SWITCH, vth0_slope=0) | offset/noise MC optimistic | manual Pelgrom Vth + MiM 2.8 %/√WL Python MC; disclosed in every spec-check row it touches |
| 4 | Offset at 18 dB / Q = 5 | worst-case ±60 mV row | behavioral offset test across all settings (python3 sim/behavioral/run_sweep.py --mode offset) |
| 5 | Damping cap 50 fF at K=200/Q=5 vs CI 8 pF | Q accuracy, junction effects | CI=8 pF decision + 3-bit trim; flagged red in capbudget |
| 6 | Charge injection / clock feedthrough | clock feedthrough 5/20 mVpp rows | double-plate + early phase; quantify at M1 with transistor-level switches |
| 7 | Fast schedule (schematic gate 5 weeks after proposal) | review readiness | scope frozen to the 24-hour-critical-path subset; full PVT deferred to M3 |
| 8 | ngspice-47 + sky130 corner lib quirks (subckt OP basins, hsa B-source parsing, clock pulse units, NFET bulk) | wasted simulation cycles | all traps documented in results/summary.md "toolchain notes" and encoded in the generators |
| 9 | f0 typ at K=200/Q≥2.83 is +0.93…+1.24 % by quantization | would fail the old ±1 % typ | measured [ANALYTICAL]; adopted typ **±1 % (K≤100) / ±1.5 % (K=200)**, max ±3 % (`spec_check.md`); f0-priority trim is an optional fallback |
| 10 | IDDA 1.22 mA typ at tt (2×op-amp + replica); ff ≈1.43 mA | old 0.8/1.5 mA spec was too tight | measured [SIM]; adopted **1.3 mA typ / 2.0 mA max at 1 MHz**, excluding output buffers, bias, CMFB and clock generation (`spec_check.md`) |
