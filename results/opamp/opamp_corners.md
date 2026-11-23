# Two-stage op-amp, three-corner characterization (transistor-level)

Testbenches: `design/opamp/tb_ac.spice` (open-loop AC, CL = 16 pF/side)
and `design/opamp/tb_step.spice` (resistive feedback gain -0.5, beta = 1/3,
200 mV diff step, CL = 5 pF/side). Bias: iref = 60 uA, Cc = 5 pF, Rz = 550.
Corners per spec/corners.md; the prototype runs tt / ss@110C / ff@-40C only.
[SIM]

## tb_ac: gain / GBW / phase margin / supply current

| corner | A0 dB | GBW MHz | PM deg | Idd uA |
|---|---:|---:|---:|---:|
| tt | 50.0 | 10.60 | 56.3 | 578 |
| ss_110C | 49.0 | 7.82 | 52.1 | 485 |
| ff_m40C | 50.5 | 13.94 | 61.6 | 687 |

## tb_step: integrator settling

| corner | tau ns | settle 0.1% ns |
|---|---:|---:|
| tt | 10 | 72 |
| ss_110C | 15 | 102 |
| ff_m40C | 5 | 35 |

The tb_step noise analysis is not reported as a system noise result.
The system output-noise figure is the [EST] sampled kT/C budget in
results/spec_check.md and results/capbudget_table.md.

Targets in this proposal: A0 >= 50 dB minimum (80 dB goal), GBW >= 10 MHz
(CL = 5 pF eff), PM >= 45 deg. tt/ff meet the 50 dB and 10 MHz bars;
ss (49.0 dB, 7.82 MHz) misses both. The behavioral sweep at 18 dB gain
requires A0 >= 60 dB and GBW >= 5 MHz, including the 18 dB Q<=2 row
(results/behavioral/q_evidence.md section b); all three transistor corners are below 60 dB A0.
System IDDA is tracked against the adopted 1.3 / 2.0 mA
typ/max budget in results/spec_check.md.
