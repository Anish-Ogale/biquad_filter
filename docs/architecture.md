# Architecture — clock-programmable fully differential SC biquad

Chipalooza Challenge #4, Sky130. Companion to `spec/spec.md`. Everything here
is the frozen baseline for schematics and simulation; numbers come from
`sim/capbudget.py` (exact z-domain) and `results/`.

## 1. Block diagram

```
                    0/6/12/18 dB            +---------+  BP (band-pass)
  VINP/VINN ---> [ gain branch Cs1 ] -----> |  INT 1  | ------------+--->
                    = G*Cs (2-bit)          | Cs1,Cs3 |      |      |
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
- Gain is applied only by scaling the input-branch capacitor,
  `Cs1 = G*Cs` (G = 1, 2, 3.98, 7.94).  Cs2, Cs3, Cd and CI are unchanged,
  so f0 and Q are gain-independent.  The LP DC gain is G and the BP peak
  gain is G*Q; the output offset is **not** assumed gain-independent and is
  simulated at 0 dB and 18 dB.

## 2. Capacitor-ratio equations (exact LDI z-domain)

State update over one full clock period (single-ended half circuit):

```
b[n] = ( b[n-1] + G*a*v[n] + a*l[n-1] ) / (1 + a_d)   BP  (INT1 out)
l[n] =   l[n-1] - a*b[n-1]                            LP  (INT2 out)

a     = Cs / CI    (Cs2 = Cs3 = Cs, loop caps)
G*a   = Cs1 / CI   (Cs1 = G*Cs, input-branch gain cap)
a_d   = Cd / CI    (switched damping cap, INT 1 only)
```

At DC this gives LP gain = G and BP peak gain = G*Q; f0 and Q depend only
on the loop ratios `a` and `a_d`, so the 0/6/12/18 dB settings do not move
the poles.

Exact design for resonance f0 = fclk/K and quality factor Q (NOT the
2*pi/K small-angle approximation, which errs up to +26 % at K = 25, Q = 0.5):

```
theta = 2*pi/K
r     = exp(-theta/(2*Q))
u     = 2*r*cos(theta) - 1          ; must be > 0  (stability/steps)
a_d   = 1/u - 1                     ; damping ratio Cd/CI
a     = sqrt(r*r/u - 1)             ; loop ratio Cs/CI
```

Derived cap values with CI = 8 pF (recommended; see results/capbudget_table.md):

```
Cs  = a*CI         Cd = a_d*CI         Cs1 = G*Cs
```

Worst-case damping cap: K = 200, Q = 5 -> Cd = 50 fF (0.4 % of CI, still
matchable with a unit cap array; flagged by `sim/capbudget.py` below 100 fF).

Reference table (CI = 8 pF; see `results/capbudget_table.md` for all 32 rows):

| K | Q | Cs (pF) | Cd (pF) | f0 (kHz) |
|---:|---:|---:|---:|---:|
| 50 | 1.00 | 6.28 | 3.24 | 10.0 |
| 200 | 5.00 | 7.96 | 0.05 | 2.5 |

## 3. Switch network (double-plate, mandatory)

Every input branch capacitor has **both plates switched**. The input gain
branch uses the same network with only its capacitance changed to
`Cs1 = G*Cs` (G = 1, 2, 3.98, 7.94); Cs2, Cs3, Cd and CI are unchanged.

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
that wiring transfers zero net charge (verified in the behavioral deck,
`sim/behavioral/biquad_behav.spice`; results in `results/summary.md`) and must
not be resurrected.

## 4. Clock phases (ideal in this study)

0/3.3 V, non-overlapping, 45 % duty + 5 % guard per edge, phi1e (bottom-plate
early cut) opens 10 % of the period before phi1 falls. At transistor level the
clock compatibility note applies: delayed PULSE sources in ngspice-47 need
rise/fall times in seconds with an explicit `n` suffix (a `u`-suffixed small
number silently corrupts the phase).

## 5. I/O table

| Signal | Pins | Direction | Notes |
|---|---:|---|---|
| VINP / VINN | 2 (shared analog) | in | usable differential input = ±1 V / G (G = 1, 2, 3.98, 7.94); VCM = 1.65 V |
| VOUTP / VOUTN | 2 (shared analog) | out | LP and BP share these lines, selected by OUT_SEL; ±1 V differential swing |
| fclk | 1 | in | 10 kHz–1 MHz (K = 25 limits fclk <= 500 kHz) |
| test enable | 1 | in | routes built-in square wave to the input |
| VDDA / VSSA | 2 | supply | 3.3 V nominal (2.97–3.63), 5 V devices |
| VDDD / VSSD | 2 | supply | 1.8 V nominal (1.62–1.98), digital only |

## 6. Control-bit allocation

See `docs/io_and_controls.md` §3 for the single-source-of-truth control-bit
allocation (17 of 24 bits used in this prototype). The sim-only prototype
implemented here uses ideal clocks and directly parameterized capacitor
values, not digital control logic.

## 7. Built-in test (BIT)

- Internal relaxation oscillator generates a square wave at fclk/64, /256,
  /1024, or /4096 (2-bit divider + enable), amplitude ≈ ±0.25 V differential,
  driven to the input gain branch.
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
  transistor-level characterization in `results/opamp/opamp_corners.md`.
- PDK mismatch is OFF in stock corners (MC_MM_SWITCH undefined; 5 V
  vth0_slope = 0). Offset/noise MC results add a manual Pelgrom Vth term and
  are labelled [SIM+MC-manual].
- Labels: [SIM] ngspice result; [ANALYTICAL] closed form; [SCALED] simulated
  and scaled to system level; [ESTIMATE] not simulable in this study.
