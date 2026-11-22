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
- Passband gain 0 / 6 / 12 / 18 dB, implemented by an **input capacitive
  attenuator** ahead of the biquad (decision 2026-11-22)
- Capacitors: Sky130 MiM only (`cap_mim_m3_2` assumed)
- Cap budget ~60–100 pF; area target ≤ 0.12 mm²
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
with parameter sweeps standing in for PVT. Monte Carlo (mismatch) is run where
the PDK models support it; stock Sky130 corners ship with mismatch disabled
(`MC_MM_SWITCH` undefined, 5 V FET `vth0_slope = 0`) — see
`results/summary.md` "specs revised" for the compensating manual Pelgrom
offset model.

## 3. Target specification

| Parameter | Min | Typ | Max | Condition / notes |
|---|---:|---:|---:|---|
| f0 accuracy vs fclk/K | — | ±1 % | ±3 % | PVT + Monte Carlo 3σ; ideal clock in this study |
| Q accuracy, Q ≤ 2 | — | ±5 % | ±15 % | |
| Q accuracy, Q > 2 | — | — | ±20 % | |
| Gain error | — | ±0.5 dB | ±1 dB | LP passband; BP gain is Q-dependent (open item §5) |
| Input range | — | — | ±1 V diff | |
| THD at 1 Vpp diff, f = f0/4 | — | −60 dB | −50 dB | |
| Output noise, 0.1 Hz–50 kHz | — | 150 µVrms | 400 µVrms | |
| Dynamic range (0.5 Vrms FS) | 62 dB | 70 dB | — | |
| Output offset, 0 dB gain, Q ≤ 2, all K | — | ±10 mV | ±30 mV | input at VCM |
| Output offset, all gain/Q, worst case | — | ±20 mV | ±60 mV | 18 dB, Q = 5 is worst case |
| Clock feedthrough | — | 5 mVpp | 20 mVpp | |
| IDDA at fclk = 1 MHz | — | 0.8 mA | 1.5 mA | |
| IDDD at fclk = 1 MHz | — | 40 µA | 100 µA | cannot be verified without digital logic; estimate only |

The offset row was split on 2026-11-22 because output offset in an SC biquad is
not independent of gain and Q: op-amp input offset and switch charge injection
are multiplied by a DC offset gain that grows roughly with the input/damping
capacitor ratio. The 18 dB / Q = 5 corner is the design expectation to confirm.

## 4. Prototype scope (this study)

(a) `sim/capbudget.py` — exact z-domain capacitor-ratio table for every (K, Q)
(b) `sim/behavioral/` — ngspice biquad with ideal switches and a behavioral
    op-amp; gain/GBW sweep giving the minimum op-amp for f0 ±1 % / Q ±5 %;
    5 mV input-referred offset test across all gain × Q settings
(c) `design/opamp/` — one transistor-level fully differential two-stage op-amp
    (xschem) with testbench, run at 3 corners (tt/27 °C, ss/2.97 V/110 °C,
    ff/3.63 V/−40 °C): gain, GBW, phase margin, supply current
(d) `results/` — plots, spec-check table, revised-spec proposals, summary

Transistor-level SC integrator/biquad and full 5×3×3 PVT qualification are
**deferred to the post-acceptance phase** (see `docs/plan.md`). Earlier
No layout, DRC/LVS, pads, level shifters, or digital control logic. Ideal
0/3.3 V non-overlapping clocks with an early phase for bottom-plate sampling.

## 5. Open items

1. **BP gain definition.** For a unity-DC-gain LP Tow-Thomas, the BP peak gain
   at f0 is Q. With the input attenuator, the LP gain is G and the BP peak is
   G·Q. The 0/6/12/18 dB gain steps therefore apply to the LP as specified, and
   the BP peak gain moves with Q unless an extra Q-dependent normalization is
   added. Decision needed before the proposal: state BP gain = G·Q, or add a
   programmable BP gain cap.
2. **Offset at 18 dB / Q = 5** — confirm with simulation; the split spec above
   is the working assumption.
3. **Q values** — √2-spaced assumed: 0.5, 0.71, 1.0, 1.41, 2.0, 2.83, 4.0, 5.0.
4. **MiM flavor** — m3_2 assumed; both m3_1 and m3_2 are 2.0 fF/µm² in the PDK.
5. **Clock guard times** — 5 % non-overlap, 10 % early phase assumed.
