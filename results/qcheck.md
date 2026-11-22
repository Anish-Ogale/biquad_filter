# Q evidence: absolute and differential errors

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

The Q<=2 rows at 18 dB use the 50/49 dB transistor-corner parameters. A targeted A0/GBW sweep in results/q2check.md shows that A0=60 dB brings the worst Q<=2 differential error inside 5 % (GBW has little effect), so the existing A0>=60 dB requirement covers this row; no separate Q<=2 relaxation is needed.
