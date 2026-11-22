# Offset test - 5 mV input-referred op-amp offset

Behavioral biquad (ideal switches), zero differential input, fclk = 500 kHz, both op-amps offset by +5 mV (same sign) unless noted.  Gain settings collapse into one row per (K, Q) because the input attenuator is a capacitive divider with no DC path into the summing nodes, so the offset is gain-invariant (docs/architecture.md).  [SIM]

| K | Q | vos mV | LP offset mV | BP offset mV | rail |
|---:|---:|---:|---:|---:|---:|
| 100 | 0.5 | +5 | +5.29 | -2.41 | 0 |
| 100 | 0.707107 | +5 | +5.50 | -1.25 | 0 |
| 100 | 1 | +5 | +1.53 | -5.24 | 0 |
| 100 | 1.41421 | +5 | +11.34 | +3.20 | 0 |
| 100 | 2 | +5 | +9.87 | -11.56 | 0 |
| 100 | 2.82843 | +5 | +14.25 | -14.02 | 0 |
| 100 | 4 | +5 | -1.45 | +15.47 | 0 |
| 100 | 5 | +5 | -16.79 | -10.67 | 0 |
| 25 | 0.5 | +5 | +4.98 | -2.51 | 0 |
| 25 | 5 | +5 | +3.77 | -7.12 | 1 |
| 200 | 5 | +5 | +17.47 | +23.61 | 0 |
| 200 | 5 | -5 | -17.47 | -23.61 | 1 |

Worst |offset| at Q <= 2: 11.6 mV (spec max 30 mV). Worst overall: 23.6 mV (spec max 60 mV).
