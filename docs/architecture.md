# Architecture — clock-programmable fully differential SC biquad

Chipalooza Challenge #4, Sky130. Companion to `spec/spec.md`. Everything here
is the frozen baseline for schematics and simulation; numbers come from
`sim/capbudget.py` (exact z-domain) and `results/`.

## 1. Block diagram

```
                    0/6/12/18 dB            +---------+  BP (band-pass)
  VINP/VINN ---> [ input capacitive  ] ---> |  INT 1  | ------------+--->
                    attenuator (2-bit)      | Cs1,Cs3 |      |      |
                                            | Cd, CI1 |   [Cs2 x-couple]
                                            +---------+      v
                                                 ^      +---------+
                                                 |      |  INT 2  |  LP
                                        LP fb    +------| Cs2,CI2 |------> (swap
                                                 (via Cs3) +---------+   outwires)
                          ^                     |
                          |  phi1/phi2/phi1e    | CMFB
                    [ clock gen, ideal in prototype ]

  Bias: 60 uA replica -> PMOS-input two-stage Miller op-amp x1 (shared)
```

- **INT 1** sums: input (Cs1, straight), LP feedback (Cs3, straight), damping
  (Cd, switched across CI1 on phi2). Its output is the **BP**.
- **INT 2** sums: BP sampled through Cs2 **cross-coupled** (p-side plate
  samples the opposite BP wire). Its output is the **LP**; LP DC transfer is
  inverting, corrected by an output-wire swap.
- Both integrators: two-phase SC inverting integrators, sample on phi1,
  integrate on phi2 (one full clock period of loop delay).
- Gain is applied entirely in the input attenuator, so f0, Q, offset gain
  Structure and noise floor are gain-independent.

## 2. Capacitor-ratio equations (exact LDI z-domain)

State update over one full clock period (single-ended half circuit):

```
b[n] = ( b[n-1] + a*v[n] + a*l[n-1] ) / (1 + a_d)     BP  (INT1 out)
l[n] =   l[n-1] - a*b[n-1]                            LP  (INT2 out)

a   = Cs / CI      (Cs = Cs1 = Cs2 = Cs3, switched input caps)
a_d = Cd / CI      (switched damping cap, INT 1 only)
```

Exact design for resonance f0 = fclk/K and quality factor Q (NOT the
2*pi/K small-angle approximation, which errs up to +26 % at K = 25, Q = 0.5):

```
theta = 2*pi/K
r     = exp(-theta/(2*Q))
u     = 2*r*cos(theta) - 1          ; must be > 0  (stability/steps)
a_d   = 1/u - 1                     ; damping ratio Cd/CI
a     = sqrt(r*r/u - 1)             ; input ratio Cs/CI
```

Derived cap values with CI = 8 pF (recommended; see results/capbudget_table.md):

```
Cs = a*CI          Cd = a_d*CI
```

Worst-case damping cap: K = 200, Q = 5 -> Cd = 50 fF (0.4 % of CI, still
matchable with a unit cap array; flagged by `sim/capbudget.py` below 100 fF).

Reference table (CI = 8 pF; see `results/capbudget_table.md` for all 32 rows):

| K | Q | Cs (pF) | Cd (pF) | f0 (kHz) |
|---:|---:|---:|---:|---:|
| 50 | 1.00 | 6.28 | 3.24 | 10.0 |
| 200 | 5.00 | 7.96 | 0.05 | 2.5 |

## 3. Switch network (double-plate, mandatory)

Every input branch capacitor has **both plates switched**:

| Phase | source-side plate | op-amp-side plate |
|---|---|---|
| phi1 (sample) | to its source via phi1**e** (early cut) | to VCM |
| phi2 (transfer) | to VCM | to the op-amp summing node |

- Damping Cd (INT 1): phi1 = both plates shorted to VCM (reset);
  phi2 = paralleled with CI1 -> factor 1/(1 + Cd/CI).
- Negative LP feedback via cross-coupling of Cs2 (p-plate samples the minus
  BP wire).

> History: an earlier draft kept the op-amp-side plate permanently on the
> summing node; net charge transfer per cycle was then exactly zero. Both-plate
> switching is mandatory (validated).

An earlier draft of the
schematic kept the op-amp-side plate tied to the summing node permanently;
that wiring transfers zero net charge (proven in `results/behav_validation.md`)
and must not be resurrected.

## 4. Clock phases (ideal in this study)

0/3.3 V, non-overlapping, 45 % duty + 5 % guard per edge, phi1e (bottom-plate
early cut) opens 10 % of the period before phi1 falls. At transistor level the
clock compatibility note applies: delayed PULSE sources in ngspice-47 need
rise/fall times in seconds with an explicit `n` suffix (a `u`-suffixed small
number silently corrupts the phase).

## 5. I/O table

| Signal | Pins | Direction | Notes |
|---|---:|---|---|
| VINP / VINN | 2 (shared analog) | in | +/-1 V differential max, VCM = 1.65 V |
| VOUT_LP / VOUT_BP | 2 (shared analog) | out | differential, +/-1 V swing |
| fclk | 1 | in | 10 kHz–1 MHz (K = 25 limits fclk <= 500 kHz) |
| test enable | 1 | in | routes built-in square wave to the input |
| VDDA / VSSA | 2 | supply | 3.3 V nominal (2.97–3.63), 5 V devices |
| VDDD / VSSD | 2 | supply | 1.8 V nominal (1.62–1.98), digital only |

## 6. Control-bit allocation (24 bits, proposal baseline)

| Bits | Function | Values |
|---:|---|---|
| 2 | clock division K | 25, 50, 100, 200 |
| 3 | Q | 0.5, 0.71, 1.0, 1.41, 2.0, 2.83, 4.0, 5.0 |
| 2 | gain (input attenuator) | 0, 6, 12, 18 dB |
| 2 | built-in test divider | fclk/64, /256, /1024, /4096 |
| 1 | test input enable | on/off |
| 1 | power-down | active low assumed |
| 2 | Q trim, coarse (cap array) | ±2 steps |
| 2 | f0 trim, coarse (cap array) | ±2 steps |
| 4 | Q trim, fine | 1-of-16 unit weights |
| 4 | f0 trim, fine | 1-of-16 unit weights |
| 1 | bias/CMFB trim | select nominal/low-offset branch |
| **24** | | |

The sim-only prototype implements none of this: it uses ideal clocks and
directly parameterized capacitor values. The 3-bit Q and 2-bit gain columns
above are the arrays `sim/capbudget.py` prices.

## 7. Built-in test (BIT)

- Internal relaxation oscillator generates a square wave at fclk/64, /256,
  /1024, or /4096 (2-bit divider + enable), amplitude ≈ ±0.25 V differential,
  driven to the input attenuator.
- Purpose: lets the tester measure f0/Q with a slow, ample square wave and a
  scope/spectrum analyzer without an external low-distortion source: LP output
  rings at damped resonance (frequency -> f0, log-decrement -> Q), BP shows
  the band-pass envelope.
- In this study the same waveform is injected in the behavioral benches
  (`sim/behavioral/`) to validate the step-based f0/Q extraction method that
  will be used on silicon.

## 8. Modeling assumptions carried by every number in results/

- Ideal 0/3.3 V clocks (5 % guard, 10 % early phase); no clock jitter.
- Op-amp: PMOS-input two-stage Miller, algebraic CMFB (soft tanh clamp);
  transistor-level characterization in `results/opamp_char.md`.
- PDK mismatch is OFF in stock corners (MC_MM_SWITCH undefined; 5 V
  vth0_slope = 0). Offset/noise MC results add a manual Pelgrom Vth term and
  are labelled [SIM+MC-manual].
- Labels: [SIM] ngspice result; [ANALYTICAL] closed form; [SCALED] simulated
  and scaled to system level; [ESTIMATE] not simulable in this study.
