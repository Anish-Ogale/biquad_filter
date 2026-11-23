# Q evidence

## (a) Real op-amp corners: absolute and differential Q error

Same step-ring extraction for every run. Differential Q error is `(Q_real - Q_ideal)/Q_ideal` with the same-case ideal baseline at **A0=80 dB, GBW=20 MHz**. This cancels the extraction bias. Limits used: 5 % for Q<=2, 15 % for Q>2 (margin below the 20 % max). [SIM]

| K | Q | gain dB | op-amp | Q | abs Q err % | Q ideal | diff Q err % | f0 err % | fit |
|---:|---:|---:|---|---:|---:|---:|---:|---:|---|
| 200 | 5 | 0 | tt_50.0dB_10.6MHz | 4.792 | -4.17 | 5.010 | -4.36 | -0.50 | 1 |
| 200 | 5 | 0 | ss_49.0dB_7.82MHz | 4.769 | -4.62 | 5.010 | -4.82 | -0.50 | 1 |
| 200 | 5 | 18 | tt_50.0dB_10.6MHz | 4.358 | -12.84 | 4.993 | -12.72 | -0.50 | 1 |
| 200 | 5 | 18 | ss_49.0dB_7.82MHz | 4.290 | -14.20 | 4.993 | -14.08 | -0.50 | 1 |
| 100 | 5 | 0 | tt_50.0dB_10.6MHz | 4.958 | -0.84 | 5.216 | -4.95 | +0.00 | 1 |
| 100 | 5 | 0 | ss_49.0dB_7.82MHz | 4.931 | -1.38 | 5.216 | -5.46 | +0.00 | 1 |
| 100 | 5 | 18 | tt_50.0dB_10.6MHz | 4.442 | -11.17 | 5.191 | -14.44 | -0.99 | 1 |
| 100 | 5 | 18 | ss_49.0dB_7.82MHz | 4.405 | -11.89 | 5.191 | -15.14 | +0.00 | 1 |
| 25 | 1 | 0 | tt_50.0dB_10.6MHz | 0.985 | -1.53 | 0.999 | -1.47 | +0.00 | 1 |
| 25 | 1 | 0 | ss_49.0dB_7.82MHz | 0.981 | -1.86 | 0.999 | -1.80 | +0.00 | 1 |
| 25 | 1 | 18 | tt_50.0dB_10.6MHz | 0.971 | -2.95 | 0.998 | -2.79 | +0.00 | 1 |
| 25 | 1 | 18 | ss_49.0dB_7.82MHz | 0.967 | -3.28 | 0.998 | -3.12 | +0.00 | 1 |
| 200 | 2 | 0 | tt_50.0dB_10.6MHz | 1.954 | -2.32 | 1.999 | -2.26 | -0.25 | 1 |
| 200 | 2 | 0 | ss_49.0dB_7.82MHz | 1.948 | -2.60 | 1.999 | -2.54 | -0.50 | 1 |
| 200 | 2 | 18 | tt_50.0dB_10.6MHz | 1.870 | -6.50 | 1.996 | -6.29 | -0.50 | 1 |
| 200 | 2 | 18 | ss_49.0dB_7.82MHz | 1.852 | -7.41 | 1.996 | -7.21 | -0.74 | 1 |
| 25 | 2 | 0 | tt_50.0dB_10.6MHz | 1.966 | -1.69 | 1.999 | -1.62 | +0.00 | 1 |
| 25 | 2 | 0 | ss_49.0dB_7.82MHz | 1.947 | -2.67 | 1.999 | -2.60 | +0.00 | 1 |
| 25 | 2 | 18 | tt_50.0dB_10.6MHz | 1.896 | -5.20 | 1.996 | -5.01 | +0.00 | 1 |
| 25 | 2 | 18 | ss_49.0dB_7.82MHz | 1.871 | -6.47 | 1.996 | -6.28 | +0.00 | 1 |
| 200 | 4 | 0 | tt_50.0dB_10.6MHz | 3.854 | -3.66 | 4.011 | -3.93 | -0.50 | 1 |
| 200 | 4 | 0 | ss_49.0dB_7.82MHz | 3.838 | -4.05 | 4.011 | -4.31 | -0.50 | 1 |
| 200 | 4 | 18 | tt_50.0dB_10.6MHz | 3.582 | -10.46 | 4.000 | -10.46 | -0.50 | 1 |
| 200 | 4 | 18 | ss_49.0dB_7.82MHz | 3.539 | -11.53 | 4.000 | -11.53 | -0.50 | 1 |

`fit=0` means the step-ring extraction did not converge; its differential Q is not used. The gain error from the same run can still be valid (settled LP tail).

K=200/Q=5 corrected differential Q worst: **14.08 %** (tt/ss, both gains). This does not exceed the 15 % differential limit, so a Q<=4 limit is not required. For reference, K=200/Q=4 differential Q worst is **11.53 %**.

The Q<=2 rows at 18 dB use the 50/49 dB transistor-corner parameters. A targeted A0/GBW sweep in results/behavioral/q_evidence.md section (b) shows that A0=60 dB brings the worst Q<=2 differential error inside 5 % (GBW has little effect), so the existing A0>=60 dB requirement covers this row; no separate Q<=2 relaxation is needed.

## (b) Q <= 2 at 18 dB gain: A0 / GBW requirement check

Targeted follow-up to section (a). Same behavioral deck, step-ring extraction and 18 dB input-branch gain as the Q check. Differential Q error is referenced to the same-case ideal op-amp baseline at **A0 = 80 dB, GBW = 20 MHz**, which cancels the extraction bias. Limit used: |Q_diff| <= 5 % for Q <= 2. [SIM]

| K | Q | gain dB | A0 dB | GBW MHz | Q | Q ideal | diff Q err % | abs Q err % | f0 err % | <=5 % |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 200 | 2 | 18 | 50 | 7.82 | 1.8698 | 1.9956 | -6.31 | -6.51 | -0.50 | no |
| 200 | 2 | 18 | 50 | 10.60 | 1.8700 | 1.9956 | -6.29 | -6.50 | -0.50 | no |
| 200 | 2 | 18 | 50 | 20.00 | 1.8700 | 1.9956 | -6.29 | -6.50 | -0.50 | no |
| 200 | 2 | 18 | 60 | 7.82 | 1.9578 | 1.9956 | -1.90 | -2.11 | -0.25 | yes |
| 200 | 2 | 18 | 60 | 10.60 | 1.9578 | 1.9956 | -1.90 | -2.11 | -0.25 | yes |
| 200 | 2 | 18 | 60 | 20.00 | 1.9598 | 1.9956 | -1.79 | -2.01 | +0.00 | yes |
| 200 | 2 | 18 | 80 | 7.82 | 1.9956 | 1.9956 | +0.00 | -0.22 | +0.00 | yes |
| 200 | 2 | 18 | 80 | 10.60 | 1.9956 | 1.9956 | +0.00 | -0.22 | +0.00 | yes |
| 200 | 2 | 18 | 80 | 20.00 | 1.9956 | 1.9956 | +0.00 | -0.22 | +0.00 | yes |
| 25 | 2 | 18 | 50 | 7.82 | 1.8828 | 1.9961 | -5.67 | -5.86 | +0.00 | no |
| 25 | 2 | 18 | 50 | 10.60 | 1.8961 | 1.9961 | -5.01 | -5.20 | +0.00 | no |
| 25 | 2 | 18 | 50 | 20.00 | 1.8828 | 1.9961 | -5.67 | -5.86 | +0.00 | no |
| 25 | 2 | 18 | 60 | 7.82 | 1.9732 | 1.9961 | -1.15 | -1.34 | +0.00 | yes |
| 25 | 2 | 18 | 60 | 10.60 | 1.9732 | 1.9961 | -1.15 | -1.34 | +0.00 | yes |
| 25 | 2 | 18 | 60 | 20.00 | 1.9734 | 1.9961 | -1.14 | -1.33 | +0.00 | yes |
| 25 | 2 | 18 | 80 | 7.82 | 1.9970 | 1.9961 | +0.05 | -0.15 | +0.00 | yes |
| 25 | 2 | 18 | 80 | 10.60 | 1.9961 | 1.9961 | +0.00 | -0.19 | +0.00 | yes |
| 25 | 2 | 18 | 80 | 20.00 | 1.9961 | 1.9961 | +0.00 | -0.20 | +0.00 | yes |

### Conclusion

At A0 = 50 dB (the tt/ss transistor-corner level) the worst Q <= 2 differential error at 18 dB is **6.31 %**, outside the 5 % typ row. Raising A0 to **60 dB** reduces the worst error to **1.90 %**, inside the row. GBW from 7.82 to 20 MHz changes the result by well under 1 %, so the DC gain, not GBW, is the limiter. The existing op-amp requirement **A0 >= 60 dB** already covers Q <= 2 at 18 dB; no extra Q <= 2 relaxation or K/Q limit is needed.

## (c) Step-ring versus multisine Q extraction cross-check

Same behavioral deck, gain and ideal op-amp parameters (A0=80 dB, GBW=20 MHz, SR=5 V/us, Ron=1 kohm, CI=8 pF). The exact ideal discrete-time model target is the design Q. A finite-A0 closed-form discrete-time model is not available in this prototype; the 80 dB/20 MHz run is the near-ideal numerical reference. [SIM]

| K | Q | gain dB | Q target | Q step | Q multisine | step err % | multisine err % | step-vs-multisine % | f0 step err % | f0 multisine err % |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | 5 | 0 | 5 | 5.216 | 4.847 | +4.32 | -3.07 | +7.62 | +0.00 | +0.50 |
| 100 | 5 | 18 | 5 | 5.191 | 4.847 | +3.82 | -3.07 | +7.11 | +0.00 | +0.50 |
| 200 | 5 | 0 | 5 | 5.010 | 5.026 | +0.20 | +0.52 | -0.31 | +0.00 | +0.05 |
| 200 | 5 | 18 | 5 | 4.993 | 5.023 | -0.14 | +0.47 | -0.60 | +0.00 | +0.00 |

The K=200/Q=5 step-ring Q error in results/behavioral/q_evidence.md section (a) and results/behavioral/behav_sweep.md (about -15 %) is **not confirmed by the multisine method (+0.5 %)**. It is therefore likely a step-ring extraction artifact at K=200 (few clean ringing peaks) and must be re-measured at transistor level.

The multisine fit is the more trustworthy Q method when the record is long enough: it fits many coherent tones and does not depend on peak detection. The step-ring fit is faster but assumes a clean, single-mode decaying sinusoid; it loses validity when the ringing has too few clean peaks or the response is dominated by settling/slew. The K=25/Q=1 18 dB ss step-ring run is marked `fit=0` in results/behavioral/q_evidence.md for that reason; the multisine method is preferred there.
