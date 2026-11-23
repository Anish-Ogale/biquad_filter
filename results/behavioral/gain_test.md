# LP gain-error test

Behavioral biquad, gain applied only by the input-branch capacitor Cs1 = G*Cs (Cs2, Cs3, Cd and CI unchanged). SR = 5 V/us, Ron = 1 kohm, fclk = 500 kHz (K=100/Q=5) and 1 MHz (K=25/Q=1). Op-amp parameter sets: ideal A0=80 dB / GBW=10 MHz, tt A0=50.0 dB / GBW=10.6 MHz, ss A0=49.0 dB / GBW=7.82 MHz. [SIM]

| op-amp | K | Q | gain set dB | LP gain dB | gain error dB | f0 err % | Q err % | verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| ideal_80dB_10MHz | 100 | 5 | 0 | -0.001 | -0.000 | +0.00 | +4.32 | PASS typ |
| ideal_80dB_10MHz | 100 | 5 | 6 | 6.020 | -0.000 | +0.00 | +4.19 | PASS typ |
| ideal_80dB_10MHz | 100 | 5 | 12 | 11.997 | -0.000 | +0.00 | +4.07 | PASS typ |
| ideal_80dB_10MHz | 100 | 5 | 18 | 17.996 | -0.000 | +0.00 | +3.82 | PASS typ |
| ideal_80dB_10MHz | 25 | 1 | 0 | -0.001 | -0.001 | +0.00 | -0.06 | PASS typ |
| ideal_80dB_10MHz | 25 | 1 | 6 | 6.019 | -0.001 | +0.00 | -0.06 | PASS typ |
| ideal_80dB_10MHz | 25 | 1 | 12 | 11.996 | -0.001 | +0.00 | -0.10 | PASS typ |
| ideal_80dB_10MHz | 25 | 1 | 18 | 17.985 | -0.012 | +0.00 | -0.06 | PASS typ |
| tt_50.0dB_10.6MHz | 100 | 5 | 0 | -0.007 | -0.007 | +0.00 | -0.84 | PASS typ |
| tt_50.0dB_10.6MHz | 100 | 5 | 6 | 6.013 | -0.007 | +0.00 | -2.35 | PASS typ |
| tt_50.0dB_10.6MHz | 100 | 5 | 12 | 11.990 | -0.007 | +0.00 | -5.12 | PASS typ |
| tt_50.0dB_10.6MHz | 100 | 5 | 18 | 17.989 | -0.007 | -0.99 | -11.17 | PASS typ |
| tt_50.0dB_10.6MHz | 25 | 1 | 0 | -0.036 | -0.036 | +0.00 | -1.62 | PASS typ |
| tt_50.0dB_10.6MHz | 25 | 1 | 6 | 5.984 | -0.036 | +0.00 | -1.82 | PASS typ |
| tt_50.0dB_10.6MHz | 25 | 1 | 12 | 11.961 | -0.037 | +0.00 | -2.66 | PASS typ |
| tt_50.0dB_10.6MHz | 25 | 1 | 18 | 17.951 | -0.046 | +0.00 | -2.96 | PASS typ |
| ss_49.0dB_7.82MHz | 100 | 5 | 0 | -0.008 | -0.007 | +0.00 | -1.38 | PASS typ |
| ss_49.0dB_7.82MHz | 100 | 5 | 6 | 6.012 | -0.008 | -0.50 | -3.41 | PASS typ |
| ss_49.0dB_7.82MHz | 100 | 5 | 12 | 11.989 | -0.008 | -0.50 | -6.44 | PASS typ |
| ss_49.0dB_7.82MHz | 100 | 5 | 18 | 17.988 | -0.008 | +0.00 | -11.89 | PASS typ |
| ss_49.0dB_7.82MHz | 25 | 1 | 0 | -0.041 | -0.041 | +0.00 | -1.86 | PASS typ |
| ss_49.0dB_7.82MHz | 25 | 1 | 6 | 5.980 | -0.041 | +0.00 | -2.14 | PASS typ |
| ss_49.0dB_7.82MHz | 25 | 1 | 12 | 11.956 | -0.042 | +0.00 | -2.97 | PASS typ |
| ss_49.0dB_7.82MHz | 25 | 1 | 18 | 17.936 | -0.060 | fit fail | fit fail | PASS typ |

Worst gain error over all op-amp sets: **0.060 dB**. Spec: +/-0.5 dB typ, +/-1 dB max. PASS

`fit fail` means the step-ringing f0/Q extractor did not converge for that run; the gain error is still measured from the settled LP tail.
