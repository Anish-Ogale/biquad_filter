# Step-ring versus multisine Q extraction

Same behavioral deck, gain and ideal op-amp parameters (A0=80 dB, GBW=20 MHz, SR=5 V/us, Ron=1 kohm, CI=8 pF). The exact ideal discrete-time model target is the design Q. A finite-A0 closed-form discrete-time model is not available in this prototype; the 80 dB/20 MHz run is the near-ideal numerical reference. [SIM]

| K | Q | gain dB | Q target | Q step | Q multisine | step err % | multisine err % | step-vs-multisine % | f0 step err % | f0 multisine err % |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | 5 | 0 | 5 | 5.216 | 4.847 | +4.32 | -3.07 | +7.62 | +0.00 | +0.50 |
| 100 | 5 | 18 | 5 | 5.191 | 4.847 | +3.82 | -3.07 | +7.11 | +0.00 | +0.50 |
| 200 | 5 | 0 | 5 | 5.010 | 5.026 | +0.20 | +0.52 | -0.31 | +0.00 | +0.05 |
| 200 | 5 | 18 | 5 | 4.993 | 5.023 | -0.14 | +0.47 | -0.60 | +0.00 | +0.00 |

The multisine fit is the more trustworthy Q method when the record is long enough: it fits many coherent tones and does not depend on peak detection. The step-ring fit is faster but assumes a clean, single-mode decaying sinusoid; it loses validity when the ringing has too few clean peaks or the response is dominated by settling/slew. The K=25/Q=1 18 dB ss step-ring run is marked `fit=0` in results/qcheck.md for that reason; the multisine method is preferred there.
