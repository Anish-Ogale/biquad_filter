# Behavioral op-amp requirement sweep

Step response. Q error is the **difference versus the same-case ideal op-amp baseline (A0=80 dB, GBW=20 MHz)**, so extraction bias cancels. Pass limits: |Q_diff| <= 5 % for Q<=2 and <= 15 % for Q>2; f0 within 1 % (K<=100) or 1.5 % (K=200). SR = 5 V/us, Ron = 1 kohm, CI = 8 pF. The grid runs both gain settings (G=1 and 7.94) for K=100/Q=5, K=25/Q=1 (fclk=1 MHz) and K=200/Q=5. [SIM]

## Minimum A0 (dB) at each GBW

| case | gain dB | 3 MHz | 5 MHz | 7.8 MHz | 10 MHz |
|---|---:|---:|---:|---:|---:|
| K100/Q5 | 0 | 45 | 45 | 45 | 45 |
| K100/Q5 | 18 | 50 | 50 | 50 | 50 |
| K25/Q1 | 0 | 45 | 40 | 40 | 40 |
| K25/Q1 | 18 | >80 | 50 | 50 | 50 |
| K200/Q5 | 0 | 45 | 45 | 45 | 45 |
| K200/Q5 | 18 | 60 | 60 | 60 | 60 |

`>80` means no A0 point in the tested grid met both the f0 and differential-Q limits at that GBW.

At K=200/Q=5 and A0=80 dB / GBW=10 MHz: absolute Q -14.8 %, differential Q -0.0 % at 0 dB; absolute Q -15.1 %, differential Q -0.0 % at 18 dB. These are inside the 15 % differential Q limit for Q>2; the absolute Q residual remains inside the max +/-20 % budget. The absolute K=200/Q=5 residual comes from the step-ring extractor; the multisine cross-check in results/behavioral/q_evidence.md section (c) gives +0.5 % and does not confirm it. Treat it as an extraction artifact pending transistor-level measurement.

**Op-amp requirement (all three cases, both gains, differential-Q limits): A0 >= 60 dB and GBW >= 5 MHz.**

## Transistor-level corners versus that requirement

| corner | A0 dB | GBW MHz | PM deg | vs requirement |
|---|---:|---:|---:|---|
| tt | 50.0 | 10.60 | 56.3 | FAIL |
| ss_110C | 49.0 | 7.82 | 52.1 | FAIL |
| ff_m40C | 50.5 | 13.94 | 61.6 | FAIL |

The transistor-level op-amp also has a separate 50 dB minimum A0 bar and an 80 dB gain target; see results/opamp/opamp_corners.md and results/spec_check.md.
