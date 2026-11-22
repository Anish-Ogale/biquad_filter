# Two-stage op-amp, three-corner characterization (transistor-level)

Testbenches: `design/opamp/tb_ac.spice` (open-loop AC, CL = 16 pF/side)
and `design/opamp/tb_step.spice` (resistive feedback gain -0.5, beta = 1/3,
200 mV diff step, CL = 5 pF/side). Bias: iref = 60 uA, Cc = 5 pF, Rz = 550.
Corners per spec/corners.md; the prototype runs tt / ss@110C / ff@-40C only.
[SIM]

## tb_ac: gain / GBW / phase margin / supply current

| corner | A0 dB | GBW MHz | PM deg | Idd uA |
|---|---:|---:|---:|---:|
| tt | 50.0 | 10.60 | 56.3 | -578 |
| ss_110C | 49.0 | 7.82 | 52.1 | -485 |
| ff_m40C | 50.5 | 13.94 | 61.6 | -687 |

## tb_step: integrator settling and differential output noise

| corner | tau ns | settle 0.1% ns | inoise uVrms |
|---|---:|---:|---:|
| tt | 10 | 72 | 339.8 |
| ss_110C | 15 | 102 | 350.1 |
| ff_m40C | 5 | 35 | 327.2 |

Targets: gain >= 60 dB, GBW >= 10 MHz (CL = 5 pF eff), PM >= 60 deg,
Idd <= 250 uA. Note: the shipped v3 netlist measures ~578 uA Idd at tt
and ~50 dB A0; see results/spec_check.md for the revised targets.
