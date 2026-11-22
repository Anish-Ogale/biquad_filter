# I/O, pins and control bits (provisional)

The bit mapping below is **provisional** — it exists so the proposal can name
pin and bit budgets; wiring is assigned at schematic review (docs/plan.md M1).
The simulation-only prototype does not implement any digital logic: clocks are
ideal 0/3.3 V sources, control settings are netlist parameters.

## 1. Supplies and references

| Name | Value | Use |
|---|---|---|
| VDDA | 3.3 V (2.97–3.63) | analog, 5 V-rated devices (spec/corners.md) |
| VDDD | 1.8 V (1.62–1.98) | digital (not in the prototype) |
| VCM | VDDA/2 ≈ 1.65 V | analog common mode |
| IREF | harness bias reference | op-amp bias (60 µA replica in the prototype) |

## 2. Pin table

| Pin | Type | Notes |
|---|---|---|
| VINP / VINN | shared analog lines 1–2 | differential input, ±1 V max, VCM ≈ 1.65 V |
| VOUTP / VOUTN | shared analog lines 3–4 | LP **and** BP outputs share these two lines, selected by OUT_SEL; ±1 V differential |
| CLK_IN | **dedicated digital pad** | fclk, 0–1.8 V logic into a level-tolerant buffer (prototype assumes ideal 0/3.3 V) |
| IREF | shared analog (bias) | bias reference from the harness |
| STATUS[3:0] | test outputs | of the 12 test-output resources, 4 used: clock monitor, BIT divider monitor, 2 spare |

Total: 4 shared analog lines (audio-band only), 1 dedicated digital pad,
4 test outputs — inside the chip resources (12 test outputs, 24 control bits).

## 3. Control bits (17 of 24)

| Field | Bits | Encoding |
|---|---:|---|
| K_SEL | 2 | 00: K=25, 01: K=50, 10: K=100, 11: K=200 (f0 = fclk/K) |
| Q_SEL | 3 | 8 √2-spaced steps: 0.5, 0.71, 1.0, 1.41, 2.0, 2.83, 4.0, 5.0 |
| GAIN_SEL | 2 | 00: 0 dB, 01: 6 dB, 10: 12 dB, 11: 18 dB (input attenuator) |
| OUT_SEL | 1 | 0: LP on VOUTP/N, 1: BP (or both where routing allows) |
| SELF_BIAS | 1 | 1: internal bias replica runs, harness IREF unused |
| BIAS_TRIM | 3 | op-amp bias current trim (±3 steps around nominal) |
| TEST_SQ_EN | 1 | 1: internal square wave drives the input (built-in test) |
| TEST_SQ_DIV | 2 | /64, /256, /1024, /4096 of fclk |
| INBIAS_EN | 1 | 1: input termination bias on (for DC-accurate tests) |
| spare | 1 | reserved (24-bit envelope, 17 used now) |

Trim arrays are inside K_SEL/Q_SEL resolution in the prototype
(`sim/capbudget.py` — coarse + 1/8-unit fine trim on Cs and Cd); whether the
4+4 trim bits are exposed separately is decided at M1.

## 4. Clock phases (ideal in the prototype)

Two-phase non-overlapping clock derived from fclk, with the early phase for
bottom-plate sampling (the double-plate networks in
`sim/behavioral/biquad_behav.spice` implement the same charge transfer):

```
phi1e  __/‾‾‾‾\____________________   bottom-plate switch opens first
phi1   ____/‾‾‾‾\__________________   sampling phase
phi2   __________/‾‾‾‾\____________   transfer phase
```

- non-overlap: 5 % of the clock period (50 ns at 1 MHz)
- early phase: 10 % of the period (20 ns at 1 MHz) ahead of the phi1 fall

## 5. Built-in test

TEST_SQ_EN + TEST_SQ_DIV route an internal square wave (±0.25 V around VCM,
fclk/64 … /4096) to the input; the LP step response then gives f0 and Q to a
scope (docs/test_plan.md §2). The behavioral `biquad_behav.spice` step bench
is exactly this stimulus.

## 6. Open interface questions

- fclk level: 1.8 V (digital domain) or 3.3 V? The prototype assumes ideal
  0/3.3 V clocks; no level shifter is in scope.
- Are the 4 shared analog lines exclusive to this block on the test chip?
- Is the harness bias reference fixed or programmable (BIAS_TRIM range)?
