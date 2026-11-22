# Q <= 2 at 18 dB gain: A0 / GBW requirement check

Targeted follow-up to `results/qcheck.md`. Same behavioral deck, step-ring extraction and 18 dB input-branch gain as the Q check. Differential Q error is referenced to the same-case ideal op-amp baseline at **A0 = 80 dB, GBW = 20 MHz**, which cancels the extraction bias. Limit used: |Q_diff| <= 5 % for Q <= 2. [SIM]

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

## Conclusion

At A0 = 50 dB (the tt/ss transistor-corner level) the worst Q <= 2 differential error at 18 dB is **6.31 %**, outside the 5 % typ row. Raising A0 to **60 dB** reduces the worst error to **1.90 %**, inside the row. GBW from 7.82 to 20 MHz changes the result by well under 1 %, so the DC gain, not GBW, is the limiter. The existing op-amp requirement **A0 >= 60 dB** already covers Q <= 2 at 18 dB; no extra Q <= 2 relaxation or K/Q limit is needed.
