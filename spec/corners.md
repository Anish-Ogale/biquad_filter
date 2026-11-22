# PVT corners

Chipalooza Challenge #4 proposal commitment: the finished block must work over
**tt/ss/ff/sf/fs × VDDA 2.97/3.3/3.63 V × VDDD 1.62/1.8/1.98 V ×
−40/27/110 °C**, with post-layout −40…+110 °C qualification required in the
proposal.

## Full corner grid (target qualification)

| Axis | Values |
|---|---|
| Process | tt, ss, ff, sf, fs (sky130A ngspice corner sections) |
| VDDA | 2.97 V / 3.30 V / 3.63 V |
| VDDD | 1.62 V / 1.80 V / 1.98 V |
| Temperature | −40 °C / 27 °C / 110 °C |

## Corners actually run in this prototype

The prototype is pre-layout and simulation-only; each check states its corners:

| Check | Corners run | Where |
|---|---|---|
| Capacitor-ratio budget (quantization, MiM area) | n/a (closed-form; temperature/process enter only via the MiM density model, 2.0 fF/µm² ± density tolerance) | `results/capbudget_table.md` |
| Behavioral biquad: f0/Q/gain sweeps | tt-type parameters (ideal switches, VDD 3.3 V) with op-amp A0/GBW/SR swept to emulate PVT | `results/summary.md` |
| Behavioral offset test (5 mV VOS) | tt-type, zero input, fclk = 500 kHz | `results/summary.md` |
| Transistor-level op-amp | **tt / 27 °C / 3.3 V**, **ss / 110 °C / 2.97 V**, **ff / −40 °C / 3.63 V** | `design/opamp/run_corners.sh` → `results/summary.md` |
| THD, noise, clock feedthrough, transistor-level biquad, full PVT, Monte Carlo | **planned** — post-acceptance | `docs/plan.md`, `results/spec_check.md` |

Corner rationale for the op-amp subset:

- **tt / 27 °C / 3.30 V** — nominal center point.
- **ss / 2.97 V / 110 °C** — slow devices, low supply, high temperature:
  worst case for GBW, output swing and current headroom.
- **ff / 3.63 V / −40 °C** — fast devices, high supply, low temperature:
  worst case for power (Idd max) and, with the excess loop gain, a
  phase-margin stress point.

## Known PDK caveats that affect corners

- Stock sky130A corners ship with mismatch disabled: `MC_MM_SWITCH` is
  undefined (defaults 0) and the 5 V FETs have `vth0_slope = 0`. Any
  offset/noise Monte-Carlo claim therefore needs an explicit
  `.param MC_MM_SWITCH=1` plus a manual Pelgrom Vth term for the 5 V devices;
  results using this compensation are labelled **[SIM+MC-manual]**.
- Analog devices are the 5 V thick-oxide FETs
  (`nfet_g5v0d10v5` / `pfet_g5v0d10v5`) — Sky130 has no 3.3 V PMOS, only the
  `nfet_03v3_nvt` native NMOS with no PMOS complement. They are used at
  VDDA = 3.3 V.
