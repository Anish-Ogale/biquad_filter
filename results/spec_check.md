# Spec check — pre-layout prototype scope

Date 2026-11-22. Verdicts: **PASS** (meets spec), **WITHIN 20 %** (within
20 % of the limit), **FAIL** (outside). Scope reminder: behavioral + op-amp
level only; transistor-level SC filter = post-acceptance. Labels:
**[SIM]** ngspice, **[ANALYTICAL]** exact z-domain / closed form,
**[EST]** estimate. Full details in `results/summary.md`.

| # | Spec (typ / max) | Simulated / estimated value | Verdict | Evidence |
|---|---|---|---|---|
| 1 | f0 accuracy ±1 % / ±3 %, all (K,Q) | Quantization worst **+1.24 %** at K=200/Q=5, ≤0.93 % everywhere else [ANALYTICAL]; MiM 1σ adds ≤0.25 % (K=200) | typ **FAIL** at K=200/Q≥2.83 (+24 % over limit), PASS elsewhere; max **PASS** (worst ~1.5 %, inc. 1σ) | `results/capbudget_table.md` `f0_quant_err_pct`, `sigma_mim_pct`; f0 extract [SIM] +0.30 % at K=100/Q=5 (multisine, results/behav_tones.csv); ±0.00 % in the gain/GBW sweep (results/behav_sweep.csv) |
| 2 | Q accuracy ±5 % typ; ±15 % max (Q≤2), ±20 % max (Q>2) | Quantization ≤0.98 % [ANALYTICAL]; behavioral: step-ringing fit +4.2 % residual at K=100/Q=5 for every op-amp setting [SIM]; multisine fit −3.36 % Q err same setting [SIM]; worst measured |Q err| 4.3 % | typ: Q≤2 **PASS**; Q>2 **PASS** (worst 4.3 % of the 20 % budget), residual flagged for transistor-level re-measure; max: **PASS** | results/behav_sweep.csv; results/capbudget_table.md `Q_quant_err_pct` |
| 3 | Gain error ±0.5 / ±1 dB | ≤0.007 dB across the A0 × GBW sweep (worst −0.024 dB at A0=40 dB) [SIM]; attenuator makes gain independent of f0/Q (docs/architecture §8) | **PASS** | behav_sweep A0 table |
| 4 | THD −60 / −50 dB @ 1 Vpp diff, f=f0/4 | Not simulated at prototype scope (needs transistor-level switches+op-amp) | **FAIL (not measured)** — planned | Post-acceptance work item |
| 5 | Output noise 150 typ / 400 max µVrms (0.1 Hz–50 kHz) | **70–80 µVrms** kT/C + op-amp budget [EST] (analytical; sum of sampled kT/C of CI/Cs/Cd at CI=8 pF, 2× noise bandwidth) | typ **PASS** (est.); noise sim planned before quoting max | analytical estimate [EST]; transient noise sim planned |
| 6 | Output offset ±30 mV (0 dB, Q≤2) / ±60 mV (all settings), incl. 5 mV op-amp offset | **11.6 mV** worst (Q≤2); **23.6 mV** worst (all settings, K=200/Q=5) [SIM], VOS = +5 mV on both op-amps same polarity (worst case), settled beyond 50× envelope decay | **PASS** (both rows) | results/offset_test.md, results/plots/fig_offset_map_tt.png |
| 7 | Clock feedthrough 5 typ / 20 max mVpp | Not measured (needs switch charge-injection, transistor level) | **FAIL (not measured)** — planned | Post-acceptance; early-phase bottom-plate sampling mitigates |
| 8 | IDDA @1 MHz, 0.8 typ / 1.5 max mA | 2 × 578 µA + 60 µA replica = **1.22 mA typ** (tt, 3.3 V); ss: ~1.02 mA; ff: ~1.43 mA [SIM, op-amp corners ×2] | typ **FAIL** (+52 %); max **PASS** (ff at 95 % of limit — marginal) | results/opamp_corners.md |
| 9 | IDDD 40 typ / 100 max µA | Clock generation out of prototype scope (external clocks assumed); est. < 40 µA for gate booking [EST] | n/a — planned | architecture.md I/O |
| 10 | Area ≤ 0.12 mm² | MiM caps: **max 0.0351 mm²** across all 32 (K,Q) settings at CI=8 pF [ANALYTICAL]; switches/routing not in prototype scope | **PASS** (caps use 29 % of area spec) | results/capbudget_table.md |
| 11 | MiM caps only | All caps are `cap_mim` (2.0 fF/µm² + 0.19 fF/µm perimeter, density checked) | **PASS** | capbudget.py mim_area |
| 12 | Op-amp: A0 ≥ 300 (50 dB) min, 80 dB target; GBW ≥ 10 MHz; PM ≥ 45° | **A0 = 50 dB (316×)**, GBW 10.6 MHz, PM 56.3°, Idd 578 µA (tt) [SIM]. A0 is at the minimum bar, not the 80 dB target | **WITHIN 20 %** of goal; A0 shortfall documented as known v3 limitation | results/opamp_corners.md, results/behav_sweep.csv |

## Specs revised (proposals — user sign-off required, nothing relaxed silently)

1. **f0 typ accuracy at K=200, Q≥2.83**: measured +0.93…+1.24 % vs ±1 %.
   Proposal: keep max ±3 %; split typ — ±1 % for K≤100, **±1.5 % for K=200**;
   alternatively re-quantize with the fine trim prioritized for f0 (Cs at
   K=200/Q=5 sits 1.2 % above ideal = within one 1/8-unit trim step; a trim
   sweep verifying a recovered typ is planned, not yet run).
2. **IDDA typ**: measured 1.22 mA vs 0.8 mA. Proposal: typ **1.2 mA**,
   keep max 1.5 mA (ff corner simulates 1.43 mA — only 4.7 % margin; if the
   challenge demands more, cut Cc to 4 pF → GBW 13 MHz, Idd −15 %, PM −5°… −50°:
   rejected, PM floor). Alternative: class-AB second stage (post-acceptance).
3. **Q>2 typ budget**: no revision needed (4.2 % of 20 %), but the +4.2 %
   systematic residual must be re-measured at transistor level before the
   proposal quotes typ ±5 %…±20 % Q accuracy as settled.
4. **THD / noise / feedthrough**: spec rows retained unchanged; marked
   "not measured at prototype scope" rather than revised.
