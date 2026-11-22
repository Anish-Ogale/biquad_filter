# Prototype summary — clock-programmable differential SC biquad (Sky130)

Pre-layout, simulation-only feasibility prototype for the Chipalooza
Challenge #4 proposal. Everything here is **[SIM]** (ngspice 47),
**[ANALYTICAL]** (exact discrete-time model, closed form) or **[EST]**
(estimate, method stated). Repo: `README.md` lists what is simulated versus
planned; per-spec verdicts in `results/spec_check.md`.

## What was simulated (and with what)

| Deliverable | State | Where |
|---|---|---|
| Cap-budget table, all 32 (K, Q) [ANALYTICAL] | done | `sim/capbudget.py` -> `results/capbudget_table.md` |
| Behavioral biquad (ideal switches, one-pole/slew op-amp, double-plate early sampling) [SIM] | done | `sim/behavioral/biquad_behav.spice` |
| Op-amp gain/GBW sweep finding the behavioral minimum [SIM] | done | `sim/behavioral/run_sweep.py` -> `results/behav_sweep.csv` |
| Offset test, 5 mV op-amp offset, all Q steps + extremes [SIM] | done | `run_sweep.py --mode offset` -> `results/offset_test.{csv,md}` |
| Multisine f0/Q/gain extraction [SIM] | done | `sim/behavioral/extract_f0_q.py` -> `results/behav_tones.csv` |
| Transistor-level op-amp: 3 corners (tt, ss/110 C, ff/-40 C) [SIM] | done | `design/opamp/` -> `results/opamp_corners.md` |
| THD, noise, clock feedthrough, Monte Carlo, full PVT, layout-level SC biquad | planned (post-acceptance) | docs/plan.md M1-M3 |

## Headline numbers

- **Cap budget [ANALYTICAL]**: CI = 8 pF; total 32.6-54.6 pF over all 32
  (K, Q); MiM area max **0.0351 mm2** vs the 0.12 mm2 spec. Worst
  quantization f0 +1.24 % / Q -0.98 % (K=200/Q=5, smallest caps).
- **Behavioral op-amp minimum [SIM]**: A0 >= 50 dB (fails at 40 dB: f0
  -0.99 %, Q -13 %), GBW >= 3 MHz at K=100/Q=5; GBW >= 5 MHz at the
  normalized-bandwidth worst case K=25/Q=1 / fclk=1 MHz (at 3 MHz the
  ringing fit is lost; the overdamped Q=0.5 absolute worst settles to
  -0.001 dB gain error); SR 5 V/us; Ron <= 2 kohm harmless at fclk <= 1 MHz.
- **Multisine extraction [SIM]** (K=100/Q=5, 10 tones): f0 +0.30 %,
  Q -3.36 % vs target; step-ringing extraction shows a systematic
  +4.2 % Q residual at K=100/Q=5 independent of op-amp settings — below
  the Q>2 typ budget but must be re-measured at transistor level.
- **Offset [SIM]** (+5 mV on both op-amps, worst-case sign): worst
  **11.6 mV** for Q <= 2 (spec 30), **23.6 mV** overall at K=200/Q=5
  (spec 60). Gain-invariant by construction (attenuator has no DC path
  into the summing nodes).
- **Transistor-level op-amp [SIM]** (CL = 16 pF/side): tt 27 C: 50.0 dB /
  10.6 MHz / PM 56.3 deg / **578 uA**; ss 110 C 2.97 V: 49.0 / 7.82 /
  52.1 / 485 uA; ff -40 C 3.63 V: 50.5 / 13.94 / 61.6 / 687 uA.
  Chip IDDA estimate: 2 x 578 uA + 60 uA replica = **1.22 mA typ** vs the
  0.8 mA target — revision proposed in `spec_check.md`.

## Toolchain notes (traps that cost time; read before re-running)

1. ngspice `ph()`/`cph()` on complex vectors return wrong values on this
   build; `wrdata` the raw complex vector and unwrap `atan2` in numpy.
2. xschem netlist output wraps the top cell in `**.subckt` comments and a
   trailing `.end`; both must be fixed before ngspice can include it
   (`design/opamp/opamp_2stage.spice` is the fixed committed copy).
3. Capacitor device values that are parameters must be braced (`{CI}`) or
   they silently become 0 F.
4. High-Q settling is slow: settle cycles ~ ln(0.02)/ln(r), r =
   exp(-theta/2Q) (K=200/Q=5: ~1250 cycles). All settled-state benches size
   `tstop` from the pole radius.
5. ngspice model load is ~10 s per invocation; batch analyses per deck.
6. Element names must start with the type letter under ngbehavior=hsa;
   lowercase `v()` in B-sources; ns-suffix rise/fall in PULSE.

## Spec-check snapshot

Full table with verdicts and the "specs revised" section:
`results/spec_check.md` (f0 typ FAIL at K=200/Q>=2.83 by quantization and
IDDA typ FAIL at 1.22 mA — both carry revision proposals; nothing relaxed
silently).
