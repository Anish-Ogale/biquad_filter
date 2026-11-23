# Clock-Programmable Second-Order Switched-Capacitor Biquad

**Chipalooza Challenge #4 (Chip Foundry Sky130) — Proposal**

Document version 1.0 · 2026-11-23

| Item | Value |
|---|---|
| IP block | Fully differential, second-order switched-capacitor biquad with low-pass and band-pass outputs |
| Process | SkyWater Sky130, 3.3 V analog (5 V-rated devices), 1.8 V digital |
| Implementation | Mixed-signal hard IP: schematic, layout, extracted views, behavioral model, documentation |
| License | Apache-2.0 |
| Repository | Public git repository; all sources and sign-off data are committed as they are produced |
| Status | Proposal for review. Pre-layout feasibility study complete; transistor-level filter, layout, full PVT and measured results are post-acceptance deliverables. |

This document deliberately contains no personal or institutional details. The
equipment list and designer CVs are supplied as separate attachments, as
required by rules 6.6 and 6.7. The document is intended to become part of the
public repository documentation for the IP block.

Labels used throughout: **[SIM]** = ngspice simulation, **[ANALYTICAL]** =
closed-form or exact discrete-time calculation, **[EST]** = estimate with the
method stated, **[TARGET]** = specification to be confirmed by simulation or
measurement at the stated milestone.

---

## 0. Proposal compliance map

| Rule | Requirement | Where addressed |
|---|---|---|
| 6.1 | Type of IP block | §1 |
| 6.2 | List of I/O, including test ports | §2 |
| 6.3 | Functional description | §3 |
| 6.4 | Target specification with average, minimum, maximum and absolute limits | §4 |
| 6.5 | Outline of a test plan for measurement | §5 |
| 6.6 | Equipment list | Separate attachment; see §11 |
| 6.7 | Designer CVs | Separate attachment; see §11 |
| 7 | Useful within an SoC; stated resource use | §8, §10 |
| 9 | Spec met in post-layout verification; mid-design changes approved | §4.7, §7, §9 |
| 12 | Public git repository | §6 |
| 13 | Verifiable with open-source EDA tools | §6 |
| 14 | All source files for all views | §6 |
| 15 | Behavioral description documented | §3, §6 |
| 16 | No unnecessary data dumps; sign-off data included | §5.11, §6 |
| 17 | Standard open-source license | §6 (Apache-2.0) |
| 19 | Post-layout PVT verification to 110 °C | §4.1, §7 |
| 20 | Standalone layout plus Chipalooza slot wrapper | §6 |
| 21 | Dedicated pin use | §2.5 |
| 22 | Shared analog-line use | §2.6 |

No exceptions to the Challenge #4 resource list are requested.

---

## 1. Type of IP block

The block is a **programmable analog filter**: a fully differential,
second-order switched-capacitor (SC) biquad with low-pass (LP) and band-pass
(BP) outputs from the same core. It is a general-purpose analog
signal-conditioning block for SoCs that need a precise, clock-referenced
filter with digitally programmable corner frequency, quality factor and gain.

| Attribute | Description |
|---|---|
| Signal domain | Differential analog input and output; sampled-data SC core |
| Filter order | Second order (two poles, two zeros) |
| Responses | Low-pass and band-pass from the same core |
| Frequency control | f0 = fclk / K, K = 25, 50, 100, 200 |
| Q control | 8 steps, 0.5 to 5 |
| Gain control | 0, 6, 12, 18 dB (LP DC gain); BP peak gain = G·Q |
| Supplies | VDDA = 3.3 V (2.97-3.63 V), VDDD = 1.8 V (1.62-1.98 V) |
| Process devices | Sky130 5 V thick-oxide FETs in the analog core; 1.8 V logic for control |
| Passives | Sky130 MiM capacitors only in the signal path (`cap_mim_m3_2` assumed; m3_1 and m3_2 are both 2.0 fF/µm²) |
| Deliverable form | Hard IP block (schematic, layout, extracted views, GDS) plus reusable behavioral model and documentation |

The block is **not** an ADC, DAC, PLL or digital filter. It contains no
separate output buffer: the integrator op-amps drive the output pads directly
and are specified for a high-impedance measurement load (RL ≥ 10 kΩ,
CL ≤ 20 pF). The signal path is the biquad core only.

The design fills the category of **programmable filters** that the Challenge #4
rules explicitly name as a useful SoC block, and complements the fixed-function
analog IP produced in Challenge #1. A single instance can provide anti-alias
filtering, channel selection, tone detection or resonant-sensor signal
conditioning, with the corner frequency tied to a system clock rather than to
an RC time constant.

---

## 2. List of I/O, including test ports

### 2.1 Padframe-facing signals

| Signal | Pads / resource | Direction | Domain | Function | Notes |
|---|---|---|---|---|---|
| VINP, VINN | Shared analog lines 1-2 | Input | 3.3 V analog | Differential filter input | VCM = 1.65 V nominal; usable differential range ±1 V / G |
| VOUTP, VOUTN | Shared analog lines 3-4 | Output | 3.3 V analog | LP or BP output, selected by OUT_SEL | ±1 V differential swing; RL ≥ 10 kΩ, CL ≤ 20 pF |
| CLK_IN | Dedicated pin 1 (digital) | Input | 1.8 V CMOS | Master clock, fclk = 10 kHz-1 MHz | Dedicated to avoid shared-mux loading and jitter; on-chip level shifter to the 3.3 V switch domain |
| CTRL[16:0] | Digital control inputs | Input | 1.8 V CMOS | Static configuration (see §2.2) | 17 of the 24 available control bits |
| STATUS[3:0] | Digital test outputs | Output | 1.8 V CMOS | Test and health flags (see §2.3) | 4 of the 12 available test outputs |
| VDDA, VSSA | Analog supply | Supply | 3.3 V | Analog core and switch drivers | 2.97-3.63 V; 5 V-rated devices |
| VDDD, VSSD | Digital supply | Supply | 1.8 V | Control decoders, clock receiver, status logic | 1.62-1.98 V |

The four shared analog lines carry only audio-band signals (f0 ≤ 20 kHz). The
clock is kept on a dedicated digital pad because the shared analog bus is
intended for low-frequency analog signalling and is not a low-jitter clock
path. Two of the three dedicated pins remain unused.

### 2.2 Digital control inputs (17 of 24)

The control map below is the functional allocation. It is frozen at the
schematic review (M1). Capacitor trim is resolved within the same 24-bit
envelope using the spare bits; it is not an additional pin requirement.

| Field | Bits | Encoding | Default | Function |
|---|---:|---|---|---|
| K_SEL | 2 | 00: K=25; 01: K=50; 10: K=100; 11: K=200 | 10 | Sets f0 = fclk / K |
| Q_SEL | 3 | 000: 0.5; 001: 0.707; 010: 1.0; 011: 1.414; 100: 2.0; 101: 2.828; 110: 4.0; 111: 5.0 | 010 | Sets Q (√2-spaced steps) |
| GAIN_SEL | 2 | 00: 0 dB; 01: 6 dB; 10: 12 dB; 11: 18 dB | 00 | Sets LP DC gain via Cs1 = G·Cs |
| OUT_SEL | 1 | 0: LP; 1: BP | 0 | Selects which output drives VOUTP/VOUTN |
| SELF_BIAS | 1 | 0: use harness IREF; 1: on-chip bias replica | 0 | Selects bias source |
| BIAS_TRIM | 3 | 000-111: ±3 steps around nominal | 100 | Op-amp bias-current trim |
| TEST_SQ_EN | 1 | 0: off; 1: BIT square wave drives the input | 0 | Built-in test enable |
| TEST_SQ_DIV | 2 | 00: /64; 01: /256; 10: /1024; 11: /4096 | 00 | BIT divider from fclk |
| INBIAS_EN | 1 | 0: off; 1: input termination bias on | 0 | DC-accurate input bias for test |
| spare | 1 | 0 | 0 | Reserved |
| **Total** | **17** | | | **7 of 24 control bits spare** | 

All control inputs are static: no setup/hold timing relative to fclk is
required. A change of setting takes effect on the following clock phases; the
filter then settles according to its programmed Q (see §5.1).

### 2.3 Digital test outputs (4 of 12)

| Signal | Name | Function | Notes |
|---|---|---|---|
| STATUS[0] | CLK_MON | Buffered fclk/2 | Confirms clock receiver, divider and level shifter |
| STATUS[1] | BIT_MON | BIT square wave before the input attenuator | Confirms BIT divider ratio independent of the filter |
| STATUS[2] | CM_OK | 1 when the output common mode is within ±100 mV of VCM | CMFB health |
| STATUS[3] | BIAS_OK | 1 when the bias current is within ±25% of nominal | Bias/start-up health |

STATUS[2] and STATUS[3] are simple low-current comparators. If the schematic
review decides to omit them, they are tied low and the test plan falls back to
the analog measurements.

### 2.4 Supply, reference and bias resources

| Resource | Value | Use |
|---|---|---|
| VDDA / VSSA | 3.3 V (2.97-3.63 V) | Analog core, switches, op-amps, clock level shifters |
| VDDD / VSSD | 1.8 V (1.62-1.98 V) | Control decoders, clock receiver, status outputs |
| Bandgap voltage reference | Harness VREF | VCM generation and bias reference |
| Bandgap current source | 60 µA nominal, 1 of 2 | Op-amp bias; mirrored and trimmed on-chip |
| VCM | 1.65 V nominal (VDDA/2 at 3.3 V) | Generated on-chip; not a padframe pin |

### 2.5 Resource budget versus Challenge #4 allowance

| Resource | Allowed | Requested | Spare |
|---|---:|---:|---:|
| 3.3 V analog supply | 1 | 1 | 0 |
| 1.8 V digital supply | 1 | 1 | 0 |
| Bandgap-referenced voltage | 1 | 1 | 0 |
| Bandgap-referenced current sources | 2 | 1 | 1 |
| Digital control inputs | 24 | 17 | 7 |
| Digital test outputs | 12 | 4 | 8 |
| Shared analog signal lines | 4 | 4 | 0 |
| Dedicated pins | 3 | 1 (CLK_IN) | 2 |
| Custom pads | With approval | 0 | - |

### 2.6 Interface notes

- **Shared analog bus.** The challenge multiplexer has a nominal on-resistance
  below 5 Ω. With a maximum signal frequency of 20 kHz and a sampling clock of
  at most 1 MHz, the bus RC is negligible; the input sampling network sees the
  bus resistance in series with the sampling switch. A source impedance of
  ≤ 1 kΩ is recommended for full settling at 1 MHz.
- **Digital interface.** All digital I/O are 1.8 V CMOS referenced to VDDD.
  The 1.8 V controls and clock are level-shifted on-chip to the 3.3 V switch
  driver domain. No 3.3 V logic is applied to digital inputs.
- **Output multiplexer.** OUT_SEL uses a break-before-make analog switch so the
  unselected output is high-impedance at the pad. LP and BP are measured
  sequentially under identical settings.
- **ESD and pad types.** Standard Sky130 pad-library cells are used. Analog
  pins are 3.3 V pads; digital pins use the 1.8 V logic interface defined by
  the harness. No custom pads are required.
- **No local power-down.** The harness gates VDDA per slot. The block has no
  separate enable pin; with fclk stopped it draws only the bias current. If the
  harness provides a slot-enable signal, it can be used externally.

---

## 3. Functional description

### 3.1 Summary

The block is a two-integrator loop. The first integrator (INT1) sums the input
charge, the low-pass feedback and a switched damping charge; its output is the
band-pass response. The second integrator (INT2) integrates the band-pass
signal with negative feedback and produces the low-pass response. Both
integrators are fully differential, two-phase SC integrators that sample on
phi1 and transfer on phi2. The loop therefore has one full clock period of
delay, which is included in the exact z-domain design.

The input branch capacitor is scaled to set the gain: `Cs1 = G·Cs`, with
G = 1, 2, 3.98, 7.94 for 0, 6, 12, 18 dB. The loop capacitors `Cs2`, `Cs3`,
the damping capacitor `Cd` and the integrator capacitors `CI` are unchanged by
the gain setting, so f0 and Q do not move when the gain changes.

### 3.2 Signal path and transfer function

In the continuous-time ideal prototype the responses are

```
H_LP(s) = G · ω0² / (s² + (ω0/Q)·s + ω0²)
H_BP(s) = G · (ω0/Q)·s / (s² + (ω0/Q)·s + ω0²)
```

so the LP DC gain is G, the BP peak gain at f0 is G·Q, and both responses share
the same f0 and Q. The discrete-time implementation is designed with the exact
LDI (lossless discrete integrator) z-domain equations rather than the
small-angle approximation. Over one full clock period, for one half circuit:

```
b[n] = ( b[n-1] + G·a·v[n] + a·l[n-1] ) / (1 + a_d)     BP (INT1 output)
l[n] =   l[n-1] - a·b[n-1]                              LP (INT2 output)

a   = Cs / CI          loop capacitor ratio
G·a = Cs1 / CI         input-branch gain ratio
a_d = Cd / CI          switched damping ratio
```

The exact design for a resonance at f0 = fclk/K with quality factor Q is

```
θ  = 2π / K
r  = exp(-θ / (2Q))
u  = 2·r·cos(θ) - 1          (must be > 0)
a_d = 1/u - 1
a   = sqrt(r²/u - 1)
```

The small-angle approximation is not used: at K = 25 and Q = 0.5 it errs by
about +26%, which would fail the f0 accuracy specification. The exact design
also keeps `u > 0` over the full K/Q matrix, so every setting is stable and
realizable with positive capacitor ratios.

The raw LP output of the two-integrator loop is inverting. An output-wire swap
at the LP tap corrects the sign. The BP polarity is set by the input-branch
wiring and is verified in the behavioral deck. These are layout/wiring
details, not signal-processing blocks.

### 3.3 Programmability

| Setting | Range | Implementation |
|---|---|---|
| f0 | 50 Hz-20 kHz | f0 = fclk/K; K = 25, 50, 100, 200; fclk = 10 kHz-1 MHz; fclk ≤ 500 kHz at K = 25 |
| Q | 0.5-5 in 8 steps | Switched capacitor ratios `a` and `a_d`; √2-spaced settings |
| Gain | 0/6/12/18 dB | Input-branch capacitor `Cs1 = G·Cs`; G = 1, 2, 3.98, 7.94 |
| Output | LP or BP | OUT_SEL multiplexes the selected output onto VOUTP/VOUTN |

Because f0 is derived from the clock, it is insensitive to process, supply and
temperature; the absolute frequency accuracy is that of the applied clock. The
on-chip accuracy specification covers capacitor mismatch, quantization of the
capacitor array, finite op-amp gain and charge injection.

The BP gain is deliberately `G·Q`; no additional normalization capacitor is
used. This is stated explicitly because the BP peak gain therefore moves with
the selected Q (from -6 dB at G = 1, Q = 0.5 to +32 dB at G = 7.94, Q = 5).
A user who needs a fixed BP gain can select a lower gain setting or add a
system-level gain stage; the LP gain remains G at DC.

### 3.4 Capacitor sizing and matching

All signal-path capacitors are Sky130 MiM capacitors. The integrator capacitor
is `CI = 8 pF`; the unit capacitor is 25 fF, and the `Cs` and `Cd` values are
quantized to whole units plus a fine trim. This value of CI was chosen to meet
the output-noise target with margin while keeping the MiM area within the
block budget. The total capacitance over all 32 (K, Q) settings is
33.6-68.7 pF at 0 dB and 37.2-117.6 pF at 18 dB, with a maximum MiM area of
0.0585 mm².

Representative rows from the exact capacitor table (CI = 8 pF):

| K | Q | Cs (pF) | Cd (pF) | Cs1 at 18 dB (pF) | Total at 18 dB (pF) | MiM area at 18 dB (mm²) | f0 error | Q error |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 25 | 0.5 | 3.523 | 7.790 | 27.98 | 117.6 | 0.0585 | +0.00% | +0.05% |
| 25 | 5 | 2.111 | 0.998 | 16.75 | 75.9 | 0.0377 | -0.06% | +0.03% |
| 50 | 1 | 1.172 | 1.266 | 9.30 | 57.8 | 0.0287 | +0.03% | +0.05% |
| 100 | 5 | 0.508 | 0.134 | 4.05 | 42.4 | 0.0210 | +0.33% | -0.03% |
| 200 | 5 | 0.253 | 0.0585 | 2.02 | 37.2 | 0.0185 | +1.24% | -0.12% |

The complete 32-row table is generated by `sim/capbudget.py` and committed as
`results/capbudget_table.md`. The worst quantization error is +1.24% in f0 at
K = 200, Q = 5, and +0.98% in Q at K = 200, Q = 2.828; both are inside the
adopted limits. The smallest damping capacitor is 58.5 fF at K = 200, Q = 5
(0.7% of CI); it is built from two 25 fF units plus trim and is flagged as
trim-sensitive. The capacitor array uses common-centroid placement, unit
capacitors, dummy fingers and guard rings; CI, Cs and Cd share the same unit
cell and orientation.

### 3.5 Switch network and clocking

Every input-branch capacitor has **both plates switched**. This is mandatory:
an earlier draft that kept the op-amp-side plate permanently on the summing
node transferred exactly zero net charge per cycle. The implemented network is:

| Phase | Source-side plate | Op-amp-side plate |
|---|---|---|
| phi1 (sample) | connected to its source through phi1e (early cut) | connected to VCM |
| phi2 (transfer) | connected to VCM | connected to the op-amp summing node |

The damping capacitor `Cd` in INT1 is reset with both plates at VCM during
phi1 and placed in parallel with CI1 during phi2, which implements the
`1/(1 + a_d)` damping factor. The LP feedback is negative through the
cross-coupling of `Cs2`: the p-side plate samples the opposite BP wire.

The clock generator produces two non-overlapping phases from fclk with 45%
duty and 5% guard per edge. `phi1e` opens the source-side switch about 10% of
the clock period before `phi1` falls, so the bottom plate is sampled first and
the signal-dependent charge on the top plate is not disturbed by the switch
turn-off. The switch transmission gates use 5 V devices, are sized for a
target on-resistance of ≤ 1 kΩ, and include dummy switches and symmetric
routing to reduce charge injection. The clock-feedthrough target is
5 mVpp typical, 20 mVpp maximum.

### 3.6 Op-amp and CMFB

The op-amp is a fully differential two-stage Miller amplifier in Sky130 5 V
devices: PMOS input pair, NMOS mirror load, NMOS common-source second stage and
PMOS current-source loads. Each side has a 5 pF Miller capacitor in series with
a 550 Ω nulling resistor. The bias current is 60 µA nominal, and the AC
characterization uses CL = 16 pF per side. The topology is committed as a
schematic and a netlist-equivalent SPICE deck in `design/opamp/`.

Simulated transistor-level performance at the three corners run so far:

| Corner | A0 (dB) | GBW (MHz) | PM (deg) | Idd (µA) |
|---|---:|---:|---:|---:|
| tt / 27 °C / 3.3 V | 50.0 | 10.60 | 56.3 | 578 |
| ss / 110 °C / 2.97 V | 49.0 | 7.82 | 52.1 | 485 |
| ff / -40 °C / 3.63 V | 50.5 | 13.94 | 61.6 | 687 |

The behavioral biquad sweep shows that the 18 dB gain setting needs
**A0 ≥ 60 dB and GBW ≥ 5 MHz** to hold the differential Q error inside the
±5% typical limit; the current transistor corners are all below 60 dB, and the
ss corner also misses the 50 dB / 10 MHz minimums. This is the top
implementation risk of the proposal, and it is addressed directly in §9: the
M1 op-amp revision will use a cascode or gain-boosted second stage and a
modest bias-current increase (the 2.0 mA core budget has headroom), targeting
A0 ≥ 60 dB, GBW ≥ 10 MHz and PM ≥ 45° at ss / 110 °C / 2.97 V. If the revision
does not close the gap, a specification change will be requested before layout
review, as required by rule 9.

The common-mode feedback in the pre-layout study is an ideal behavioral model,
used to establish the required loop. The transistor-level CMFB (switched-
capacitor or continuous-time, decided at M1) is part of the schematic review
deliverable. Its targets are output common mode within ±20 mV of VCM and a
CMFB loop phase margin of at least 45°, with no degradation of the
differential response.

### 3.7 Bias

The block takes one 60 µA bandgap-referenced current source from the harness
and mirrors it to the two op-amps through a bias distribution network. A 3-bit
`BIAS_TRIM` adjusts the mirror ratio by ±3 steps around nominal to compensate
process spread. `SELF_BIAS = 1` selects an on-chip replica derived from the
harness bandgap voltage reference, so the harness current source can be left
unconnected; the exact self-bias implementation is fixed at M1. A start-up
circuit ensures the bias mirror leaves the zero-current state at power-up.

### 3.8 Built-in test

An internal square-wave generator divides fclk by 64, 256, 1024 or 4096 and
drives a ±0.25 V differential signal into the input gain branch when
`TEST_SQ_EN = 1`. Its purpose is to let a tester measure f0 and Q with only a
scope or digitizer, without an external low-distortion source:

- the LP output rings at f0 after each edge; the ring frequency gives f0 and
  the log decrement gives Q;
- the BP output shows the band-pass envelope and provides a second estimate
  of f0 and Q;
- at the settings of interest, the divider is chosen so that at least five
  decay time constants fit in one half-period, so the ringing is resolved even
  at Q = 5.

The BIT is specified for the 0 dB and 6 dB gain settings, where ±0.25 V is
inside the ±1 V / G input range. At 12 dB and 18 dB the input range is smaller,
so the external source is used for the primary f0/Q measurement. The BIT is
not a low-distortion sine and is not used for THD or noise.

### 3.9 Control decoding, start-up and power

The static control bits are decoded in the 1.8 V domain and level-shifted to
the 3.3 V switch-driver domain. Only the clock receiver and the BIT divider are
dynamic; all configuration bits are level-sensitive. An internal power-on
reset initializes the divider and status logic when VDDD becomes valid. There
is no external reset pin and no local power-down: the harness gates VDDA per
slot. The block reaches valid output within 1 ms of valid supplies and fclk.

### 3.10 Block diagram

```
                       gain bank                 integrator 1
  VINP ──┬──[ Cs1 = G·Cs ]──┐          ┌──────────────────────┐   BP
         │                  ├─────────►│  INT1 (BP output)    ├──────┬──►[OUT_SEL]──► VOUTP
  VINN ──┴──[ Cs1 = G·Cs ]──┘          │  Cs1, Cs3, Cd, CI1   │      │              VOUTN
                                       └───────▲──────────────┘      │
                                               │ Cs3 (LP feedback)  │
                                       ┌───────┴──────────────┐      │
                                       │  INT2 (LP output)    │◄─────┘ Cs2 cross-coupled
                                       │  Cs2, CI2            ├──────► LP ──►[OUT_SEL]
                                       └──────────────────────┘
```

Clock generation, CMFB, bias, the BIT divider and the control decoders are
shown as support blocks in `docs/architecture.md`. The signal path contains
only MiM capacitors, 5 V CMOS switches and the two op-amps; no resistors are
used in the filter transfer function.

---

## 4. Target specification

### 4.1 Operating conditions and absolute maximum ratings

**Operating conditions.** "Typ" is the expected value at 27 °C, VDDA = 3.3 V,
VDDD = 1.8 V and typical process unless otherwise stated. "Min" and "Max" are
the guaranteed limits over the full operating range. "Absolute limits" are
stress limits, not operating points.

| Parameter | Min | Typ | Max | Unit | Notes |
|---|---:|---:|---:|---:|---|
| VDDA | 2.97 | 3.30 | 3.63 | V | Analog; 5 V-rated devices |
| VDDD | 1.62 | 1.80 | 1.98 | V | Digital |
| VSSA, VSSD | 0 | 0 | 0 | V | Common ground reference |
| Ambient temperature | -40 | 27 | 110 | °C | Operating |
| fclk | 10 k | - | 1 M | Hz | fclk ≤ 500 kHz at K = 25 |
| Input common mode | 1.55 | 1.65 | 1.75 | V | VCM = 1.65 V nominal (VDDA/2 at 3.3 V) |
| Output common mode | 1.63 | 1.65 | 1.67 | V | CMFB, ±20 mV |
| IREF | 54 | 60 | 66 | µA | Harness current source, ±10% |
| Output load RL | 10 k | - | - | Ω | Measurement condition |
| Output load CL | - | - | 20 | pF | Measurement condition |

**Absolute maximum ratings.**

| Parameter | Limit | Notes |
|---|---|---|
| VDDA | 3.63 V | Padframe/PDK limit; do not exceed |
| VDDD | 1.98 V | Digital core limit |
| Analog pin voltage | VSSA - 0.3 V to VDDA + 0.3 V | ESD diode limit, not to exceed the pad-library absolute maximum |
| Digital pin voltage | VSSD - 0.3 V to VDDD + 0.3 V | ESD diode limit, not to exceed the pad-library absolute maximum |
| Ambient operating temperature | -40 to +110 °C | Challenge requirement |
| Storage temperature | -55 to +125 °C | Package dependent |
| Junction temperature | 125 °C | Maximum |
| ESD | 2 kV HBM / 500 V CDM | Pad-library target |
| Latch-up | ±100 mA | Pad-library target |

Operation at the absolute maximum ratings is not implied. All pins are
protected by the standard pad-library ESD structures; the analog core uses
5 V devices, but the padframe and ESD diodes set the pin voltage limits.

### 4.2 Filter transfer characteristics

| Parameter | Min | Typ | Max | Unit | Condition |
|---|---:|---:|---:|---:|---|
| Filter order | - | 2 | - | - | LP and BP outputs |
| f0 range | 50 | - | 20 000 | Hz | f0 = fclk/K |
| Clock range | 10 k | - | 1 M | Hz | K = 25: ≤ 500 kHz |
| K settings | 25 | - | 200 | - | 25, 50, 100, 200 |
| Q range | 0.5 | - | 5 | - | 8 √2-spaced settings |
| LP DC gain | 0 | - | 18 | dB | 0, 6, 12, 18 dB |
| BP peak gain | -6 | - | +32 | dB | G·Q at f0 |
| Differential output swing | - | - | ±1 | V | 2 Vpp differential, RL ≥ 10 kΩ, CL ≤ 20 pF |
| Differential input range | - | - | ±1/G | V | For ±1 V differential output |
| Input common-mode range | 1.55 | 1.65 | 1.75 | V | VCM ± 0.1 V |
| Output common mode | 1.63 | 1.65 | 1.67 | V | CMFB |
| Integrator settling | - | - | 300 | ns | 0.1% target, fclk = 1 MHz, 450 ns phase budget |
| Start-up time | - | - | 1 | ms | Supplies valid and fclk present |

The usable differential input is ±1 V at 0 dB, ±0.5 V at 6 dB, ±0.25 V at
12 dB and ±0.126 V at 18 dB, corresponding to a ±1 V differential output. The
BP output can be larger than the LP output because its peak gain is G·Q; the
user must reduce the input accordingly when BP is selected at high Q.

### 4.3 Accuracy and programmability

| Parameter | Min | Typ | Max | Unit | Condition |
|---|---:|---:|---:|---:|---|
| f0 accuracy vs fclk/K, K ≤ 100 | - | ±1 | ±3 | % | PVT, ideal external clock |
| f0 accuracy vs fclk/K, K = 200 | - | ±1.5 | ±3 | % | PVT, ideal external clock |
| Q accuracy, Q ≤ 2 | - | ±5 | ±15 | % | 0-12 dB guaranteed; 18 dB after A0 upgrade |
| Q accuracy, Q > 2 | - | - | ±20 | % | Guaranteed maximum; design target ±10% |
| Gain accuracy, LP passband | - | ±0.5 | ±1 | dB | 0-18 dB, f << f0 |
| f0 step monotonicity | - | monotonic | - | - | All K settings |
| Q step monotonicity | - | monotonic | - | - | All Q settings |

The f0 typical limits are ±1% for K ≤ 100 and ±1.5% for K = 200 because the
unit-capacitor quantization reaches +1.24% at K = 200, Q = 5. The maximum
±3% includes capacitor process spread, finite op-amp gain and charge
injection. The absolute clock frequency is the user's responsibility; the
block's accuracy is specified relative to fclk/K.

The Q > 2 row has no typical guarantee because the high-Q settling is limited
by finite op-amp gain; the design target is ±10%, and the guaranteed limit is
±20%. The 18 dB Q ≤ 2 row is conditional on the M1 op-amp revision reaching
A0 ≥ 60 dB; with the current 49-50.5 dB op-amps the simulated differential
error is 5.0-6.3%, outside the ±5% typical row but inside the ±15% maximum.

### 4.4 Linearity, noise, offset and clock feedthrough

| Parameter | Min | Typ | Max | Unit | Condition |
|---|---:|---:|---:|---:|---|
| THD | - | -60 | -50 | dB | 1 Vpp differential at LP output, f = f0/4, 0/18 dB |
| Output noise | - | 150 | 400 | µVrms | 0.1 Hz-50 kHz, output-referred, 0/18 dB |
| Dynamic range | 62 | 70 | - | dB | 0.5 Vrms full scale, 0 dB gain |
| Output offset, 0 dB and Q ≤ 2 | - | - | ±40 | mV | VIN = 0, 5 mV op-amp input offset assumed |
| Output offset, all gain/Q | - | - | ±60 | mV | VIN = 0, 5 mV op-amp input offset assumed |
| Clock feedthrough | - | 5 | 20 | mVpp | VIN = 0, fclk = 1 MHz |
| CMRR | 60 | 70 | - | dB | DC-20 kHz |
| PSRR (VDDA), low frequency | 40 | 50 | - | dB | DC-1 kHz |
| PSRR (VDDA), audio band | 30 | 40 | - | dB | 1-20 kHz |

For distortion, a more negative number is better: the typical target is
-60 dB and the guaranteed limit is -50 dB. THD is specified output-referred at
the LP output with a 1 Vpp differential signal, which is inside the ±1 V
differential swing. At 18 dB the input is reduced by G so the output stays at
1 Vpp.

Output noise is dominated by the sampled kT/C noise of the input and feedback
branches. The pre-layout estimate is 66.7 µVrms at 0 dB and 87.2 µVrms at
18 dB (K = 25, Q = 0.5), which leaves margin to the 150 µV typical limit;
1/f, op-amp and clock-feedthrough noise are not yet included and will be
added in the M1 transient-noise simulation. The maximum 400 µVrms is the
guaranteed limit after those terms are included.

Output offset is not gain-invariant. The simulated output/input offset gain is
about 5.9× at 0 dB and Q ≤ 2, and 9.1× over all gain/Q settings, for a 5 mV
op-amp input-referred offset. The ±40 mV and ±60 mV limits correspond to
those factors. The 5 mV assumption is provisional: a manual Pelgrom estimate
of the 5 V input pair will be made at M1, and the input-pair area will be
increased or an offset trim added using spare control bits if the 3σ offset
exceeds 5 mV. Any resulting change to the offset limit will be requested
before layout review.

CMRR and PSRR are included because they are relevant to SoC integration. They
are target specifications: the first simulation at M1 will confirm them, and
the test plan in §5.9 measures them on silicon.

### 4.5 Supply current, power and area

| Parameter | Min | Typ | Max | Unit | Condition |
|---|---:|---:|---:|---:|---|
| IDDA, core | - | 1.3 | 2.0 | mA | Two op-amps + 60 µA bias replica; fclk = 1 MHz, K = 25 |
| IDDA, total block | - | 1.6 | 2.5 | mA | Core + CMFB + clock generation + level shifters + decoders [EST] |
| IDDD | - | 40 | 100 | µA | 1.8 V, static controls, fclk = 1 MHz |
| Total power | - | 5.4 | 8.5 | mW | VDDA + VDDD [EST] |
| MiM capacitor area | - | - | 0.0585 | mm² | Maximum over all 32 K/Q settings at 18 dB [ANALYTICAL] |
| Block area | - | - | 0.12 | mm² | Target including switches, op-amps, bias and routing |
| Slot area | TBD | | | mm² | Harness-defined at slot assignment |

The core current is derived from the op-amp simulations: 2 × 578 µA plus
60 µA = 1.22 mA typical, 1.43 mA at the ff corner, against the 1.3 mA typical
and 2.0 mA maximum specification. The total-block figure adds an estimate for
CMFB, clock generation, level shifters and decoders and is to be confirmed at
M1. The core 2.0 mA maximum is a binding sub-budget; the total 2.5 mA maximum
is the block-level specification. Output buffers are not included because the
op-amps drive the pads directly.

The MiM area is 0.0585 mm², 49% of the 0.12 mm² block target. The remaining
area is for the two op-amps, the switch network, the bias and clock blocks,
guard rings and routing. The layout is sized to the block, not to the slot;
extra slot area is not used for the circuit.

### 4.6 Interface characteristics

| Parameter | Min | Typ | Max | Unit | Condition |
|---|---:|---:|---:|---:|---|
| Digital input high | 1.26 | - | - | V | VDDD = 1.8 V |
| Digital input low | - | - | 0.54 | V | VDDD = 1.8 V |
| Digital input leakage | - | - | 1 | µA | Per pin |
| CLK_IN duty cycle | 40 | 50 | 60 | % | fclk = 10 kHz-1 MHz |
| CLK_IN rise/fall | - | - | 10 | ns | 10-90% |
| Status output high | 1.4 | - | - | V | 1 mA load |
| Status output low | - | - | 0.4 | V | 1 mA load |
| SC input resistance | 72 k | - | 400 M | Ω | Equivalent, depends on fclk and gain |
| Output resistance | - | - | 100 | Ω | DC, closed-loop op-amp |
| Power-up time | - | - | 1 | ms | Supplies valid and fclk present |

The input is a sampling network, not a resistive termination: the equivalent
input resistance is approximately 1/(fclk·Cs1), which gives about 72 kΩ at
the highest gain and clock and up to about 400 MΩ at the lowest. The source
should have a low impedance and be referred to the same VCM as the block.

### 4.7 Measurement boundaries and specification interpretation

To avoid ambiguity in post-layout and silicon verification, the following
boundaries apply:

- **f0 accuracy** is relative to fclk/K with an ideal external clock. Clock
  accuracy and jitter are system-level contributions and are not part of the
  block specification.
- **Gain accuracy** is the LP passband gain at f << f0. The BP peak gain is
  G·Q and inherits the Q error.
- **THD** is output-referred at the LP output, 1 Vpp differential, f = f0/4.
- **Noise** is output-referred, integrated from 0.1 Hz to 50 kHz, with the
  input terminated at VCM, at both 0 dB and 18 dB.
- **Offset** is output-referred after the filter has settled, with VIN = 0
  differential and the input at VCM. The specified limits assume a 5 mV
  op-amp input-referred offset; the actual measured op-amp offset is reported
  separately.
- **IDDA core** covers the two op-amps and the on-chip bias replica.
  **IDDA total** adds CMFB, clock generation, level shifters and decoders.
  Neither includes the output load or the padframe.
- **Area** is the MiM capacitor area for the capacitor row, and the full block
  area including switches, op-amps, bias and routing for the block row.
- **PVT** for the target specification is post-layout: 5 process corners
  (tt, ss, ff, sf, fs) × 3 VDDA values × 3 temperatures, with VDDD at
  1.62/1.80/1.98 V for the digital interface. Silicon measurement covers
  supply and temperature on one process corner; process spread is covered by
  simulation and, if multiple parts are available, by part-to-part
  measurement.

Any change to a target specification after the schematic review will be
submitted for approval before layout, as required by rule 9.

### 4.8 Preliminary evidence and current status

The proposal is supported by a pre-layout feasibility study. It is not a
completed transistor-level filter: the behavioral model, the exact capacitor
sizing and a transistor-level op-amp are complete; the transistor-level
biquad, full PVT, Monte Carlo, THD, noise, clock feedthrough and layout are
post-acceptance.

| Check | Result | Verdict | Evidence |
|---|---|---|---|
| Capacitor budget [ANALYTICAL] | 33.6-68.7 pF at 0 dB; 37.2-117.6 pF at 18 dB; max MiM 0.0585 mm² | Within ≤120 pF / 0.12 mm² target | `results/capbudget_table.md` |
| f0 quantization [ANALYTICAL] | +1.24% worst at K = 200, Q = 5; ≤0.93% elsewhere | Within ±1.5% / ±1% typ | `results/capbudget_table.md` |
| Q quantization [ANALYTICAL] | ≤0.98% | Within ±5% typ | `results/capbudget_table.md` |
| Behavioral SC biquad vs exact map [SIM] | ≤0.09% of output peak | Pass | `results/plots/fig_step_response.png` |
| Gain steps 0/6/12/18 dB [SIM] | Worst 0.060 dB error | Pass ±0.5 dB typ | `results/behavioral/gain_test.md` |
| Offset with 5 mV op-amp offset [SIM] | 29.4 mV (0 dB, Q ≤ 2); 45.5 mV (all gain/Q) | Pass 40/60 mV | `results/behavioral/offset_test.md` |
| Op-amp requirement [SIM] | 18 dB needs A0 ≥ 60 dB, GBW ≥ 5 MHz | Gap: current corners 49-50.5 dB | `results/behavioral/q_evidence.md` |
| Transistor op-amp [SIM] | tt 50.0 dB/10.6 MHz; ss 49.0/7.82; ff 50.5/13.94; PM 52.1-61.6° | ss misses 50 dB/10 MHz; all below 60 dB | `results/opamp/opamp_corners.md` |
| IDDA core [SIM] | 1.22 mA typ; 1.43 mA at ff | Pass 1.3/2.0 mA | `results/opamp/opamp_corners.md` |
| Noise, kT/C only [EST] | 66.7 µVrms at 0 dB; 87.2 µVrms at 18 dB | Pass estimate 150/400 µVrms | `results/capbudget_table.md` |
| THD, clock feedthrough, CMRR/PSRR, full PVT, MC, layout | Not yet simulated | Planned M1-M3 | `docs/plan.md` |

The op-amp gap is reported as a gap, not hidden: the current 49-50.5 dB
corners are below the 60 dB needed at 18 dB, and the ss corner misses the
50 dB / 10 MHz minimums. The M1 revision is the path to close it. The
behavioral study also shows that A0 = 60 dB brings the 18 dB, Q ≤ 2
differential Q error to 1.9% worst, which is inside the ±5% typical limit.

---

## 5. Test plan outline

The test plan maps every specification row to a measurement. The same
procedures are used in pre-layout simulation, post-layout simulation and
silicon characterization; only the stimulus source and the observation
instrument change. The equipment list is supplied separately.

| Specification | Primary method | Section |
|---|---|---|
| Digital interface, status, bring-up | Logic analyzer, DMM, current-limited supplies | 5.1 |
| DC transfer, offset, common mode | 6½-digit DMM, DC source | 5.2 |
| f0, Q, gain | Swept sine / multisine, fit to 2nd-order model | 5.3 |
| Fast f0/Q check | BIT square wave, scope/digitizer | 5.4 |
| THD | Single sine at f0/4, FFT/audio analyzer | 5.5 |
| Output noise | Low-noise preamp + 24-bit ADC / audio analyzer | 5.6 |
| Clock feedthrough | Spectrum at fclk, zero input | 5.7 |
| IDDA, IDDD, power | Precision ammeter / SMU | 5.8 |
| CMRR, PSRR | Common-mode and supply tones | 5.9 |
| PVT, part-to-part | Thermal stream/chuck, supply sweep | 5.10 |
| Data reporting | Plots, tables, raw data on demand | 5.11 |

### 5.1 Bring-up and functional check

1. Inspect the packaged part; verify no supply-to-ground shorts with a DMM.
2. Apply VDDD = 1.8 V from a current-limited supply; check IDDD is below
   100 µA with fclk stopped.
3. Apply VDDA = 3.3 V from a current-limited supply; check IDDA is below
   2.5 mA with fclk stopped.
4. Apply fclk = 100 kHz, 1.8 V CMOS; check STATUS[0] = fclk/2.
5. Set K = 100, Q = 1, gain = 0 dB, OUT_SEL = LP, TEST_SQ_EN = 0. Apply
   VCM = 1.65 V to both inputs; check STATUS[2] = 1 and STATUS[3] = 1.
6. Apply a 100 mVpp differential, 100 Hz sine (f0/10 at K = 100, fclk = 100 kHz);
   verify the LP output is approximately 100 mVpp and in phase with the input
   (after the LP inversion correction).
7. Sweep all 32 K/Q settings and all four gain settings; verify no latch-up,
   no clipping and monotonic behavior. Record IDDA for each setting.
8. If a setting fails, isolate with STATUS[0] (clock), STATUS[3] (bias) and
   STATUS[2] (CM), then repeat at a lower fclk to check settling.

The supplies are always current-limited and ramped; the shared analog bus is
coordinated with the other projects on the test chip before any signal is
applied.

### 5.2 DC transfer, offset and common mode

- **DC transfer.** With fclk = 1 MHz, K = 100, Q = 1, LP selected, sweep the
  differential input from -1 V to +1 V in 10 mV steps at 0 dB; record VOUTP
  and VOUTN with a 6½-digit DMM. The slope gives the LP DC gain; the
  endpoints give the usable swing. Repeat at 6, 12 and 18 dB with the input
  range scaled by 1/G.
- **Offset.** Set VIN = 0 differential and the input common mode to 1.65 V.
  After the output has settled (at least 100 clock periods for Q ≤ 2, and up
  to about 1300 clock periods at K = 200, Q = 5), measure VOUTP - VOUTN.
  Repeat for all 32 K/Q settings at 0 dB and 18 dB. The 0 dB, Q ≤ 2 subset is
  checked against ±40 mV; all settings against ±60 mV. Both output polarities
  are recorded so the sign of the offset is available for comparison with
  simulation.
- **Common mode.** Measure (VOUTP + VOUTN)/2 at each setting; compare with
  1.65 V ±20 mV. Check at the supply extremes (2.97 V and 3.63 V) and at
  -40 °C and 110 °C.
- **Input common-mode range.** At 0 dB, Q = 1, f = 1 kHz, sweep the input
  common mode from 1.55 V to 1.75 V with a small differential signal and
  verify the gain and offset remain within specification.

### 5.3 Frequency response: f0, Q and gain

- **Stimulus.** Use a low-distortion differential sine source, or a
  single-ended source with a wideband balun/transformer. A single-ended drive
  into one input with the other at VCM is acceptable for a sanity check but
  creates a common-mode component; the differential drive is preferred.
- **Amplitude.** Keep the output at or below 1 Vpp differential to avoid
  compression. At 18 dB the input is 1/G of the 0 dB value. A typical input is
  100 mVpp at 0 dB and 12.6 mVpp at 18 dB.
- **Sweep.** 100 points per decade from 0.1·f0 to 10·f0, at each of the 32
  K/Q settings and each gain setting. Measure both LP and BP by changing
  OUT_SEL; allow the filter to settle after each change.
- **Extraction.** Fit the measured complex transfer function to the ideal
  second-order LP and BP models. f0 is the natural frequency and Q is the pole
  Q; do not use the -3 dB frequency as the f0 estimate. Report the LP DC gain,
  the BP peak gain and the BP peak frequency (which should equal f0).
- **Cross-check.** Compare the fitted f0/Q with the BIT step result (§5.4) and
  with the exact z-domain prediction. A disagreement larger than the
  repeatability of the two methods is investigated before the part is
  characterized.
- **Pass criteria.** f0 ±1% typical for K ≤ 100, ±1.5% for K = 200, ±3%
  maximum; Q ±5% typical for Q ≤ 2, ±15% maximum for Q ≤ 2 and ±20% maximum
  for Q > 2; gain ±0.5 dB typical, ±1 dB maximum.

### 5.4 Step and built-in-test measurement

- Set TEST_SQ_EN = 1 and select TEST_SQ_DIV so that at least five decay time
  constants fit in one half-period. For example, at K = 200 and f0 = 1 kHz
  (fclk = 200 kHz), /4096 gives 48.8 Hz; the half-period is 10.25 ms, so
  about six decay time constants at Q = 5 fit before the next edge.
- Capture the LP and BP outputs with a ≥12-bit scope or digitizer. For the LP
  output, extract the ring frequency (f0) and the log decrement (Q) from the
  edge response. For the BP output, extract the envelope and the zero
  crossings.
- Use this test at 0 dB and 6 dB, where the ±0.25 V BIT is inside the input
  range. At 12 dB and 18 dB, use the external source from §5.3.
- This is the fast production test: it requires only a clock and a scope, and
  it exercises the complete signal path including the input gain branch.
- **Pass criteria.** The BIT result agrees with the swept-sine result within
  2% in f0 and 5% in Q. The BIT is a cross-check, not a replacement for the
  full frequency response.

### 5.5 Total harmonic distortion

- Apply a single coherent sine at f = f0/4 with 1 Vpp differential at the LP
  output. Set the input amplitude so that the measured LP output is 1 Vpp
  differential; the required input is the output divided by the LP gain at
  f0/4, which is approximately (1.03-1.07)·G depending on Q.
- Use an audio analyzer with a THD floor below -100 dB, or notch the
  fundamental and measure the harmonic residual with a spectrum analyzer.
- Record 2^13 samples with an integer number of cycles; discard the first 10
  settling periods; apply a Blackman-Harris window; sum harmonics 2-10
  relative to the fundamental.
- Test at Q = 1 and Q = 5, f0 = 1 kHz and 10 kHz, 0 dB and 18 dB, LP and BP.
  The BP output is expected to be worse at high Q because its peak gain is
  G·Q; report it separately.
- **Pass criteria.** -60 dB typical, -50 dB maximum at the LP output for the
  1 Vpp condition.

### 5.6 Output noise

- Terminate both inputs at VCM (zero differential) and run the filter at
  fclk = 1 MHz, 0 dB and 18 dB, Q = 1 and Q = 5.
- Measure the output with a low-noise preamp and a 24-bit ADC or an audio
  analyzer; integrate the power spectral density from 0.1 Hz to 50 kHz.
- Subtract the measurement-system noise floor, or use a cross-correlation
  measurement if the floor is not negligible. Report output-referred µVrms
  and, for information, input-referred µVrms.
- Repeat at fclk = 10 kHz and 100 kHz with K adjusted to keep f0 fixed, to
  check that the integrated noise is stable and that aliasing is understood.
- **Pass criteria.** 150 µVrms typical, 400 µVrms maximum, output-referred,
  0.1 Hz-50 kHz.

### 5.7 Clock feedthrough

- Set VIN = 0 differential and fclk = 1 MHz. Measure the output spectrum at
  fclk and its first few harmonics with a spectrum analyzer or a scope FFT.
- Report the peak-to-peak amplitude of the clock-related components at the LP
  and BP outputs, at 0 dB and 18 dB, Q = 1 and Q = 5.
- The production design uses double-plate switching and the early phase
  (phi1e); the measurement confirms that these choices keep the feedthrough
  inside the limit.
- **Pass criteria.** 5 mVpp typical, 20 mVpp maximum.

### 5.8 Supply current and power

- Insert a precision ammeter or SMU in the VDDA and VDDD supplies. Use the
  harness per-slot supply monitor if it is available and calibrated.
- Measure the quiescent current with fclk stopped, then at fclk = 10 kHz,
  100 kHz and 1 MHz, at K = 25, for all four gain settings and Q = 1 and 5.
- Average over at least 32 clock periods to remove the switching ripple.
  Report the core current (two op-amps plus bias replica) and the total block
  current separately, using the definitions in §4.7.
- **Pass criteria.** IDDA core ≤ 2.0 mA and total ≤ 2.5 mA at 1 MHz;
  IDDD ≤ 100 µA. The typical values are 1.22 mA core, 1.6 mA total and 40 µA
  digital.

### 5.9 CMRR and PSRR

- **CMRR.** Tie both inputs together and apply a 200 mVpp common-mode sine at
  1 kHz, within the input common-mode range; measure the differential output.
  CMRR = 20·log10(Vcm,in / Vout,diff). Sweep 20 Hz-20 kHz at 0 dB and 18 dB,
  Q = 1.
- **PSRR.** Superimpose a 100 mVpp sine on VDDA at 100 Hz, 1 kHz, 10 kHz and
  20 kHz; measure the output. PSRR = 20·log10(Vripple / Vout). Use a bias tee
  or a clean supply with a series resistor and coupling capacitor; verify the
  ripple amplitude at the pin with a scope. Test at 0 dB and 18 dB, Q = 1.
- **Pass criteria.** CMRR ≥ 60 dB, PSRR ≥ 40 dB from DC to 1 kHz and ≥ 30 dB
  from 1 kHz to 20 kHz.

### 5.10 PVT and part-to-part

- Silicon covers one process corner; the five-process-corner matrix is a
  post-layout simulation requirement. On silicon, vary VDDA = 2.97/3.30/3.63 V,
  VDDD = 1.62/1.80/1.98 V and ambient temperature = -40/27/110 °C.
- At each extreme, measure f0/Q/gain at a representative subset (K = 25 and
  200, Q = 0.5 and 5, gain = 0 and 18 dB), plus offset, THD, noise and IDDA.
- Allow the thermal stream/chuck to settle before each measurement; record the
  package temperature and the supply voltages at the pins.
- If multiple packaged parts are available, repeat the key measurements on
  3-5 parts and compare the spread with the post-layout Monte Carlo result.
- **Pass criteria.** All specification rows hold at the extremes, or the
  observed margin is reported and a spec change is requested with data.

### 5.11 Data reporting and pass/fail

- Every measurement records the setting (K, Q, gain, output), the condition
  (supply, temperature, fclk, amplitude), the instrument and the raw data
  file.
- The repository contains summary plots and tables, not raw data dumps, in
  accordance with rule 16. Raw data is reproducible on demand from the
  committed benches and scripts.
- A measured-vs-simulated table is published for every specification row.
  Any row that does not meet the target is reported as a failure with the
  measured value, not omitted.
- The final measurement report is part of the public repository and is the
  basis for the second half of the challenge award, as required by rule 26.

---

## 6. Design flow, verification and deliverables

### 6.1 Open-source flow

The design is created and verified with open-source EDA tools:

| Task | Tool |
|---|---|
| Schematic capture | xschem |
| Circuit simulation | ngspice |
| Layout | magic (with klayout for viewing/DRC checks) |
| DRC / LVS | magic / netgen / klayout |
| Parasitic extraction | magic or the PDK extraction flow |
| Scripting and data analysis | Python 3, Make |
| Documentation | Markdown / plain text |

No proprietary tool is required to use, verify or modify the block. AI tools
may be used in support of the design, but the delivered IP, verification flow
and documentation do not require AI tools.

### 6.2 Repository contents

The public repository is organized as follows:

- `spec/` — the target specification, corner definitions and adopted changes.
- `docs/` — architecture, I/O and control map, test plan and milestone plan;
  this proposal is at the repository root (`PROPOSAL.md`).
- `design/` — xschem schematics and netlists for the op-amp, biquad, bias,
  CMFB, clock generation, BIT and top level; the standalone and slot-wrapper
  layouts.
- `sim/` — behavioral models, transistor-level testbenches, corner and Monte
  Carlo scripts, and the extraction scripts.
- `results/` — summary plots, spec-check tables and the committed sign-off
  data (DRC/LVS reports, extracted netlist, PVT summary).
- `test/` — silicon bring-up and measurement scripts, instrument settings and
  the measurement report template.
- `Makefile` — one-command reproduction of the main verification targets.

At final submission, all source files needed to generate all views of the
design will be present. The repository does not contain unnecessary raw data
dumps; summary plots and tables are committed, and the raw data is regenerated
on demand.

### 6.3 Verification and sign-off

The design is signed off with:

- DRC and LVS clean on the standalone block and on the slot wrapper;
- a full post-layout PVT matrix: 5 process corners (tt, ss, ff, sf, fs) ×
  VDDA 2.97/3.30/3.63 V × temperature -40/27/110 °C, with VDDD at
  1.62/1.80/1.98 V for the digital interface;
- Monte Carlo mismatch on the extracted netlist, with a manual Pelgrom model
  for the 5 V devices because the stock Sky130 corners ship with mismatch
  disabled (`MC_MM_SWITCH` undefined and `vth0_slope = 0` for the 5 V FETs);
- post-layout f0/Q/gain/THD/noise/offset/clock-feedthrough/IDDA results in the
  spec-check table;
- the final DRC and LVS reports committed to the repository.

The pre-layout study already documents the PDK mismatch caveat and uses a
manual Pelgrom Vth term plus a MiM 2.8%/√WL Monte Carlo where a mismatch
claim is made; such results are labelled [SIM+MC-manual].

### 6.4 Two layout forms

As required by rule 20, the project exists in two forms:

1. a **standalone layout** of the biquad block, reusable in other chips; and
2. a **slot-wrapper layout** for the Chipalooza harness chip, containing only
   the slot-specific pad connections and the wrapper cell around the
   standalone block.

The standalone block is the deliverable IP. The slot wrapper is a thin
integration layer and is not part of the reusable IP. The layout is sized to
the circuit, not expanded to fill the slot.

### 6.5 License

The design is released under the **Apache License 2.0**. Every source file
carries an SPDX header. No third-party source with an incompatible license is
included; the Sky130 PDK is used under its own license, and the repository
documents the PDK version and corner files used for sign-off.

---

## 7. Schedule and review gates

The schedule follows the Challenge #4 gates. In this document **M1** is the
schematic review, **M2** the layout review and **M3** the final design review.
The dates are the weeks posted in the rules; the deliverables are the ones
this proposal commits to.

| Gate | Date | Deliverable |
|---|---|---|
| Proposal | 2026-11-23 | This document and the pre-layout feasibility study |
| Schematic review | Week of 2026-12-28 | Complete xschem schematic: biquad, input gain bank, op-amp (revised), CMFB, bias, clock generation and level shifters, BIT, decoders, top level. Pre-layout simulation of the full block. Control map frozen. |
| Layout review | Week of 2027-02-01 | Full standalone layout, DRC/LVS clean, extracted netlist, post-layout simulation of the key rows, area report within 0.12 mm² |
| Final design review | Week of 2027-02-22 | Full post-layout PVT and Monte Carlo, final spec-check table, slot-wrapper layout, final report |
| Tapeout | 2027-05-19 | GDS and sign-off data delivered to the harness |
| Measurement | After packaged parts | Bring-up, characterization, published measurement report |

Work packages:

| WP | Period | Content |
|---|---|---|
| WP1 — Schematic | Nov 23-Dec 28 | Op-amp revision for A0 ≥ 60 dB, CMFB, bias, clock generation and level shifters, BIT, decoders, top-level schematic |
| WP2 — Pre-layout verification | Dec-Jan | Full-block pre-layout simulation, 32-setting f0/Q/gain matrix, offset, THD, noise, clock feedthrough, corner screening |
| WP3 — Layout | Jan-Feb 1 | Floorplan, common-centroid capacitor array, switch network, op-amps, guard rings, DRC/LVS, extraction |
| WP4 — Post-layout | Feb 1-22 | Extracted PVT and Monte Carlo, final spec check, slot wrapper, final report |
| WP5 — Tapeout | Feb-May | GDS review, harness integration, tapeout |
| WP6 — Measurement | After parts | Bring-up, full characterization, measurement report |

The top schedule risk is the op-amp revision in WP1: the schematic review is
five weeks after the proposal. The revision is a bounded change (cascode or
gain-boosted second stage plus bias-current adjustment) on an existing,
characterized topology, and it is the first WP1 task.

---

## 8. Resource request and assumptions

### 8.1 Resource request

| Resource | Requested | Notes |
|---|---|---|
| 3.3 V analog supply | 1 | VDDA = 3.3 V nominal |
| 1.8 V digital supply | 1 | VDDD = 1.8 V nominal |
| Bandgap voltage reference | 1 | VCM and bias reference |
| Bandgap current source | 1 of 2 | 60 µA nominal; the second is not used |
| Digital control inputs | 17 of 24 | 7 spare for capacitor/offset trim if needed |
| Digital test outputs | 4 of 12 | 8 spare |
| Shared analog lines | 4 of 4 | VINP, VINN, VOUTP, VOUTN |
| Dedicated pins | 1 of 3 | CLK_IN (1.8 V digital); 2 spare |
| Custom pads | 0 | Standard pad-library cells |

### 8.2 Assumptions

- The harness supplies 3.3 V analog and 1.8 V digital rails, a bandgap
  voltage reference and at least one bandgap-referenced current source.
- The four shared analog lines are available to this slot and are switched by
  the harness multiplexer with the stated < 5 Ω nominal resistance.
- The clock is a clean 1.8 V CMOS square wave; its absolute accuracy and
  jitter are system-level contributions. The block's f0 accuracy is specified
  relative to fclk/K.
- The analog core uses Sky130 5 V thick-oxide devices at 3.3 V because Sky130
  has no 3.3 V PMOS; the native 3.3 V NMOS has no PMOS complement.
- The harness slot size and pad assignment are TBD. The block is designed to
  the resource envelope above; the MiM capacitor area of 0.0585 mm² leaves
  margin for a smaller-than-expected slot.
- Packaged parts are provided through the challenge. The measurement plan
  assumes the shared analog lines and the digital controls are accessible at
  the package pins and that the equipment listed separately is available.

No exceptions to the resource list are requested.

---

## 9. Risks, mitigations and open items

### 9.1 Risk register

| # | Risk | Impact | Mitigation / status |
|---|---|---|---|
| 1 | Op-amp A0 is 49.0-50.5 dB; the 18 dB gain setting needs A0 ≥ 60 dB | Q error at 18 dB, Q ≤ 2 outside the ±5% typical row (5.0-6.3% simulated) | Top risk. M1 revision: cascode or gain-boosted second stage, bias current increase within the 2.0 mA core budget; target A0 ≥ 60 dB and GBW ≥ 10 MHz at ss. If not closed, request a spec change before layout. |
| 2 | ss corner GBW is 7.82 MHz, below the 10 MHz minimum | Settling and Q accuracy at 110 °C, 2.97 V | Same op-amp revision; increase bias current and/or reduce CL; the 2.0 mA core budget has headroom. |
| 3 | Q > 2 at 18 dB is limited by finite gain; simulated -11.2/-11.9% at K = 100, Q = 5 | May miss the ±20% maximum if the revision is insufficient | The simulated value is inside the ±20% maximum; the A0 ≥ 60 dB revision is expected to improve it. The Q > 2 row has no typical guarantee. |
| 4 | Offset depends on the real 5 V input-pair offset, not the assumed 5 mV | ±40/±60 mV limits could be exceeded | Manual Pelgrom estimate at M1; increase input-pair area and/or add an offset trim using spare control bits. Re-derive the limit with data before layout. |
| 5 | Smallest damping capacitor is 58.5 fF at K = 200, Q = 5 | Q accuracy and matching | CI = 8 pF, 25 fF unit cell, 3-bit trim, common-centroid layout; flagged in the cap table. Verify with post-layout Monte Carlo. |
| 6 | Charge injection and clock feedthrough are not yet characterized | 5/20 mVpp target could be missed | Double-plate switching, early phase, dummy switches, symmetric routing; transistor-level measurement at M1. |
| 7 | THD, CMRR, PSRR and final noise are not yet simulated | Target rows could be missed | First full-block pre-layout simulation in WP2; if a row misses, increase bias/swing or adjust the target with data before layout review. |
| 8 | 45-corner PVT plus Monte Carlo in a 27-week schedule | Review readiness | Behavioral screening first, then targeted transistor corners; parallel simulation; the exact capacitor table removes a large sweep dimension. |
| 9 | Stock Sky130 corners have mismatch disabled (`MC_MM_SWITCH`, `vth0_slope = 0` for 5 V FETs) | Offset/noise Monte Carlo would be optimistic | Manual Pelgrom Vth term and MiM 2.8%/√WL Monte Carlo, labelled [SIM+MC-manual]; documented in the review packet. |
| 10 | Harness slot size and pad assignment are TBD | Late layout change | Design to the resource envelope; MiM area is 0.0585 mm²; the slot wrapper is a thin layer; the standalone block is independent of the slot. |
| 11 | Shared analog bus is intended for low-frequency signals | Input/output degradation if used above the audio band | All signals are ≤ 20 kHz; the clock is on a dedicated pin; the bus resistance is < 5 Ω; source impedance ≤ 1 kΩ recommended. |
| 12 | The 1.8 V/3.3 V interface details are fixed by the harness | Level-shifter mismatch | The block includes its own 1.8 V-to-3.3 V level shifters and is specified for 1.8 V CMOS digital I/O; the harness interface is confirmed at slot assignment. |
| 13 | IDDA total (1.6/2.5 mA) is an estimate; CMFB, clock generation and level shifters are not yet designed | Could exceed the 2.5 mA block budget | Budget each support block at M1; share bias currents; size switch drivers for the 1 MHz load; the core 2.0 mA sub-budget has headroom. |

### 9.2 Open items to close at the schematic review

1. Op-amp revision: cascode vs gain-boosted second stage; final A0, GBW, PM
   and bias current at all corners.
2. CMFB implementation: switched-capacitor vs continuous-time; loop phase
   margin and output common-mode accuracy.
3. Capacitor trim: exact trim word and whether it is exposed on the control
   bus or fixed at test; it must fit the 24-bit envelope.
4. Offset: Pelgrom estimate, input-pair area, and whether an offset trim is
   needed.
5. BIT: final amplitude and divider range; confirm the 0/6 dB restriction and
   the test-time divider selection.
6. Self-bias: exact implementation and reference usage.
7. Harness: slot size, pad assignment, shared analog line availability, and
   the 1.8 V/3.3 V digital interface.
8. Whether STATUS[2] and STATUS[3] are implemented or tied low.

---

## 10. Why this block is useful in an SoC

- **Clock-programmable corner.** f0 is set by fclk/K, so it tracks the system
  clock and is insensitive to RC process spread. A system can change the filter
  corner by changing the clock or the K bits, without changing external
  components.
- **Wide, continuous coverage.** 50 Hz-20 kHz covers audio, voice, sensor and
  control-loop bands. The same block can be an anti-alias filter, a
  reconstruction filter, a channel-select filter or a tone detector.
- **Two responses from one core.** LP and BP outputs share the same f0 and Q;
  a system can select either response without a second filter; both come from
  the same core. The BP output is useful for resonant sensors, lock-in
  detection and band-power estimation.
- **Digital gain and Q control.** 0-18 dB in 6 dB steps and 0.5-5 in
  √2-spaced steps cover a wide dynamic range with no external components.
- **Low power and small area.** 1.22 mA core at 1 MHz from 3.3 V, and
  0.0585 mm² of MiM capacitors, make the block practical for area- and
  power-constrained SoCs.
- **Built-in test.** The internal square wave lets a production tester measure
  f0 and Q at the 0/6 dB settings with a clock and a scope, reducing test cost
  and enabling a quick go/no-go check.
- **Open, reusable IP.** The schematic, layout, extracted views, behavioral
  model and test plan are public and Apache-2.0, so an SoC designer can
  integrate, modify and verify the block with open-source tools.

The block is a natural companion to the fixed-function analog IP produced in
Challenge #1: it provides the analog signal conditioning between a sensor or
audio source and an ADC, and between a DAC and an output driver, with a corner
frequency that is set digitally.

---

## 11. Items sent separately

Per rules 6.6 and 6.7, the following are supplied as separate attachments and
are deliberately not part of this document, which will become public
repository documentation:

- the list of equipment available for measurement;
- the CVs of the designers.

No personal or institutional details appear in this proposal.

---

## Appendix A. Design equations and capacitor table

### A.1 Exact LDI design

For a resonance at f0 = fclk/K and quality factor Q:

```
θ   = 2π/K
r   = exp(-θ/(2Q))
u   = 2r cos(θ) - 1
a_d = 1/u - 1
a   = sqrt(r²/u - 1)
Cs  = a·CI
Cd  = a_d·CI
Cs1 = G·Cs
```

The state update over one clock period is

```
b[n] = (b[n-1] + G·a·v[n] + a·l[n-1])/(1 + a_d)    BP (INT1)
l[n] =  l[n-1] - a·b[n-1]                          LP (INT2)
```

The exact form is used because the small-angle approximation errs by up to
+26% in f0 at K = 25, Q = 0.5.

### A.2 Capacitor table summary

| Quantity | Value |
|---|---|
| CI | 8 pF |
| Unit capacitor | 25 fF |
| Cs range | 0.253-3.523 pF |
| Cd range | 0.0585-7.790 pF |
| Cs1 range at 18 dB | 2.02-27.98 pF |
| Total capacitance at 0 dB | 33.6-68.7 pF |
| Total capacitance at 18 dB | 37.2-117.6 pF |
| Maximum MiM area at 18 dB | 0.0585 mm² |
| Worst f0 quantization | +1.24% (K = 200, Q = 5) |
| Worst Q quantization | +0.98% (K = 200, Q = 2.828) |

The complete 32-row table, including the unit-cap counts and the trim flags,
is in `results/capbudget_table.md` and is regenerated by `sim/capbudget.py`.

### A.3 Op-amp summary

| Parameter | Value |
|---|---|
| Topology | Fully differential two-stage Miller |
| Input pair | PMOS, Sky130 5 V devices |
| First stage load | NMOS mirror |
| Second stage | NMOS common source, PMOS current-source loads |
| Compensation | 5 pF Miller + 550 Ω nulling resistor per side |
| Bias | 60 µA nominal, 3-bit trim |
| Simulated A0 / GBW | tt 50.0 dB/10.6 MHz; ss 49.0 dB/7.82 MHz; ff 50.5 dB/13.94 MHz |
| Simulated PM | 52.1-61.6° |
| Simulated Idd | 485-687 µA |
| M1 target | A0 ≥ 60 dB, GBW ≥ 10 MHz, PM ≥ 45° at ss/110 °C/2.97 V |

---

## Appendix B. Repository map and evidence index

| Path | Contents |
|---|---|
| `PROPOSAL.md` | This proposal document |
| `spec/spec.md` | Target specification and adopted changes |
| `spec/corners.md` | PVT corner definitions and PDK caveats |
| `docs/architecture.md` | Architecture, capacitor equations, switch network, modeling assumptions |
| `docs/io_and_controls.md` | Pin, control-bit and BIT allocation |
| `docs/test_plan.md` | Detailed simulation and silicon test procedures |
| `docs/plan.md` | Milestones, risks and the post-acceptance plan |
| `sim/capbudget.py` | Exact z-domain capacitor table and MiM area |
| `sim/behavioral/` | Behavioral SC biquad, gain/offset/Q sweeps, extraction scripts |
| `design/opamp/` | xschem schematic, SPICE netlist, AC and step testbenches |
| `results/capbudget_table.md` | All 32 (K, Q) capacitor rows |
| `results/spec_check.md` | Per-spec verdicts and adopted adjustments |
| `results/summary.md` | Headline simulation results and toolchain notes |
| `results/opamp/opamp_corners.md` | Transistor-level op-amp corners |
| `results/behavioral/` | Gain, offset, Q evidence and op-amp requirement sweeps |
| `results/plots/` | Committed figures and figure provenance |
| `README.md` | Repository overview and reproduction commands |

The figures referenced in this proposal are:

- `results/plots/fig_capbudget.png` — capacitance and MiM area over all
  settings;
- `results/plots/fig_f0_vs_fclk.png` — f0 versus clock frequency;
- `results/plots/fig_q_vs_setting.png` — f0 and Q quantization error;
- `results/plots/fig_step_response.png` — behavioral SC biquad versus the
  exact discrete-time map;
- `results/plots/fig_offset_map.png` — output offset versus Q at 0 and 18 dB;
- `results/plots/fig_opamp_schematic.png` — op-amp topology;
- `results/plots/fig_opamp_bode_tt_ss_ff.png` — op-amp gain and phase at three
  corners.

All results in this proposal are reproducible from the committed sources with
the commands in `README.md` and the `Makefile`. The pre-layout study is a
feasibility prototype, not a claim of a completed transistor-level filter; the
post-acceptance plan in `docs/plan.md` lists the remaining work and the
review gates.
