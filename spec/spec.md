# Clock-programmable fully differential SC biquad — target specification

Chipalooza Challenge #4, Chip Foundry Sky130 (Open Circuit Design).
Status: **pre-layout, simulation-only feasibility study**. Proposal deadline 2026-11-23.

## 1. Function

Second-order switched-capacitor biquad with simultaneous low-pass (LP) and
band-pass (BP) outputs.

- f0 = fclk / K, K ∈ {25, 50, 100, 200}
- fclk = 10 kHz … 1 MHz; at K = 25, fclk ≤ 500 kHz
- f0 span: 50 Hz … 20 kHz
- Q programmable in 8 steps, 0.5 … 5 (√2-spaced assumed)
- Passband gain 0 / 6 / 12 / 18 dB, implemented by the **input-branch
  capacitor** `Cs1 = G*Cs` (G = 1, 2, 3.98, 7.94), with Cs2, Cs3, Cd and CI
  unchanged. LP DC gain = G; BP peak gain = G*Q (decision 2026-11-22)
- Capacitors: Sky130 MiM only (`cap_mim_m3_2` assumed)
- Cap budget target ≤120 pF; the CI = 8 pF exact table is 33.6–68.7 pF at
  0 dB and 37.2–117.6 pF at 18 dB. Max MiM area is 0.0585 mm², within the
  0.12 mm² area target; the area number is MiM capacitance only (switches,
  op-amps, bias and routing are not included).
- Built-in test: internal square wave at fclk/64, /256, /1024, /4096,
  ≈ ±0.25 V, can drive the input

## 2. Supplies and environment

| Rail | Min | Typ | Max |
|---|---:|---:|---:|
| VDDA | 2.97 V | 3.30 V | 3.63 V |
| VDDD | 1.62 V | 1.80 V | 1.98 V |

### PVT corners exercised in simulation

| Axis | Values |
|---|---|
| Process | tt, ss, ff, sf, fs (sky130A ngspice corner sections) |
| VDDA | 2.97 V, 3.30 V, 3.63 V |
| Temperature | −40 °C, 27 °C, 110 °C |

The full 5-process × 3-supply × 3-temperature grid is the **post-layout**
qualification target (proposal commitment: −40 … +110 °C). In this pre-layout
study the transistor-level op-amp is verified at **3 corners** (tt/27 °C,
ss/2.97 V/110 °C, ff/3.63 V/−40 °C) and the behavioral biquad at tt/27 °C
with parameter sweeps standing in for PVT. Monte Carlo (mismatch) is **not
run in this prototype**: stock Sky130 corners ship with mismatch disabled
(`MC_MM_SWITCH` undefined, 5 V FET `vth0_slope = 0`), so any such claim would
need an explicit switch plus a manual Pelgrom model; that work is planned
post-acceptance. See `results/spec_check.md` for the current limitations and
the adopted specification adjustments.

## 3. Target specification

| Parameter | Min | Typ | Max | Condition / notes |
|---|---:|---:|---:|---|
| f0 accuracy vs fclk/K | — | ±1 % (K≤100), ±1.5 % (K=200) | ±3 % | PVT + Monte Carlo 3σ; ideal clock in this study |
| Q accuracy, Q ≤ 2 | — | ±5 % | ±15 % | |
| Q accuracy, Q > 2 | — | — | ±20 % | |
| Gain error | — | ±0.5 dB | ±1 dB | LP passband; BP peak gain = G*Q |
| Output swing | — | — | ±1 V differential | usable differential input = ±1 V / G; BP peak gain = G*Q |
| THD at f0/4, 1 Vpp differential at LP output | — | −60 dB | −50 dB | output-referred test condition |
| Output noise, 0.1 Hz–50 kHz | — | 150 µVrms | 400 µVrms | |
| Dynamic range (0.5 Vrms FS) | 62 dB | 70 dB | — | |
| Output offset, 0 dB gain, Q ≤ 2, all K | — | — | ±40 mV | assumed 5 mV op-amp input offset |
| Output offset, all gain/Q | — | — | ±60 mV | assumed 5 mV op-amp input offset; 18 dB / Q = 5 worst case |
| Clock feedthrough | — | 5 mVpp | 20 mVpp | |
| IDDA at fclk = 1 MHz | — | 1.3 mA | 2.0 mA | 1.43 mA ff corner excludes buffers/bias/CMFB/clock gen |
| IDDD at fclk = 1 MHz | — | 40 µA | 100 µA | cannot be verified without digital logic; estimate only |

Output offset is not gain-invariant in the SC biquad. The measured
output/input offset gain is about **5.9x** at 0 dB/Q≤2 (baseline 60 dB
behavioral matrix) and **9.1x** over all gain/Q. The real tt/ss op-amp
worst-case reruns give 6.8–7.1x; the ideal 80 dB/10 MHz case gives up to
10.7x over all settings, still below the 60 mV max. A planned post-acceptance
item is to estimate the real 5 V input-pair offset by manual Pelgrom and
re-derive the offset spec from that value [EST].

## 4. Prototype scope (this study)

(a) `sim/capbudget.py` — exact z-domain capacitor-ratio table for every (K, Q)
(b) `sim/behavioral/` — ngspice biquad with ideal switches and a behavioral
    op-amp; gain/GBW sweep giving the minimum op-amp for f0 ±1 % / Q ±5 %;
    5 mV input-referred offset test across all gain × Q settings
(c) `design/opamp/` — one transistor-level fully differential two-stage op-amp
    (xschem) with testbench, run at 3 corners (tt/27 °C, ss/2.97 V/110 °C,
    ff/3.63 V/−40 °C): gain, GBW, phase margin, supply current
(d) `results/` — plots, spec-check table, adopted spec adjustments, summary

Transistor-level SC integrator/biquad and full 5×3×3 PVT qualification are
**deferred to the post-acceptance phase** (see `docs/plan.md`). There is no
layout, DRC/LVS, pads, level shifters, or digital control logic in this study.
Ideal 0/3.3 V non-overlapping clocks with an early phase for bottom-plate
sampling are assumed.

## 5. Open items

1. **BP gain definition (decided 2026-11-22).** The gain steps apply to the
   LP: LP DC gain = G = 1, 2, 3.98, 7.94 (0/6/12/18 dB). With the input-branch
   capacitor `Cs1 = G*Cs`, the BP peak gain at f0 is **G·Q**. No extra BP
   normalization cap is added; the BP gain therefore moves with the selected
   Q. The usable differential input for a ±1 V differential output is ±1 V/G.
2. **Offset at 18 dB / Q = 5** — measured at 0 and 18 dB with same/opposite
   offsets. The max specs are now ±40 mV (0 dB, Q≤2, all K) and ±60 mV (all
   gain/Q) for an assumed 5 mV op-amp offset. Planned: manual Pelgrom estimate
   of the real 5 V input-pair offset, then re-derive the spec [EST].
3. **Q values** — √2-spaced assumed: 0.5, 0.71, 1.0, 1.41, 2.0, 2.83, 4.0, 5.0.
4. **MiM flavor** — m3_2 assumed; both m3_1 and m3_2 are 2.0 fF/µm² in the PDK.
5. **Clock guard times** — 5 % non-overlap, 10 % early phase assumed.
