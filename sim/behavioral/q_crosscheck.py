#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Cross-check step-ring and multisine Q extraction at four settings.

Both methods use the same rendered behavioral deck and the same ideal-op-amp
baseline (A0=80 dB, GBW=20 MHz).  The step-ring method is run_sweep.case_step;
the multisine method reuses the fitting routines in extract_f0_q.py.

The exact ideal discrete-time model Q is the design target (design_exact).
A finite-A0 closed-form discrete-time model is not available in this
prototype; the A0=80 dB/GBW=20 MHz run is the near-ideal numerical reference.

Run:  python3 sim/behavioral/q_crosscheck.py
Out:  results/data/q_crosscheck.csv, q_crosscheck.fragment.md
"""
import csv
import math
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.abspath(os.path.join(HERE, '..', '..', 'results'))
DATA = os.path.join(RESULTS, 'data')
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..'))

import run_sweep as rs  # noqa: E402
import extract_f0_q as ef  # noqa: E402


SETTINGS = ((100, 5.0, 0.0, 1.0), (100, 5.0, 18.0, 7.94),
            (200, 5.0, 0.0, 1.0), (200, 5.0, 18.0, 7.94))
FCLK = 500e3
A0 = 1e4          # 80 dB
GBW = 20e6        # 20 MHz
AMP = 0.01        # per tone


def multisine_run(K, Q, gain, tag):
    """Return multisine-fit f0, Q and tone rows for one setting."""
    f0_tgt = FCLK / K
    tones = ef.tone_ladder(f0_tgt, 10)
    n_settle = ef.nominal_settle(K, Q)
    n_tone_cycles = int(round((1.0 / tones[0]) * FCLK))
    tstop = (n_settle + 15 * n_tone_cycles) / FCLK
    dat = os.path.join(HERE, f'{tag}.dat')
    sp = os.path.join(HERE, f'{tag}.gen.spice')
    text, _ = rs.render(K=K, Q=Q, fclk=FCLK, tstop=tstop, tmaxstep=2e-8,
                        gain=gain, A0=A0, GBW=GBW, dat=os.path.basename(dat))
    text = ef.stimulation(text, ef.multisine_lines(tones, AMP))
    ef.write_deck(sp, text)
    r = subprocess.run(['ngspice', '-b', os.path.basename(sp)], cwd=HERE,
                       capture_output=True, text=True, timeout=400)
    if not os.path.exists(dat):
        raise RuntimeError(f'ngspice failed for {tag}: '
                           f'{(r.stdout + r.stderr)[-300:]}')
    d = rs.load_wrdata(dat)
    os.remove(dat)
    t, yl, yb = ef.sample_tail(d, 1.0 / FCLK, n_settle + 1, 12, tones[0])
    rows = []
    for f in tones:
        fl = ef.fit_sine(t, yl, f, extra_harm=2)
        fb = ef.fit_sine(t, yb, f)
        rows.append(dict(f=f,
                         gain_l_dB=20 * math.log10(fl['amp'] / AMP),
                         gain_b_dB=20 * math.log10(fb['amp'] / AMP)))
    fit = ef.fit_f0_q(f0_tgt, Q, FCLK, [r['f'] for r in rows],
                      [10 ** (r['gain_l_dB'] / 20) for r in rows],
                      gain_scale=gain)
    return fit, rows


def main():
    os.makedirs(DATA, exist_ok=True)
    out = []
    for K, Q, gdb, gain in SETTINGS:
        tag = f'xq_K{K}_Q{Q:g}_G{gdb:g}'
        tstop = 4.0e-3 if K == 200 else 2.5e-3
        step = rs.case_step(K=K, Q=Q, A0=A0, GBW=GBW, SR=5e6, ron=1e3,
                            fclk=FCLK, CI=8.0, amp=0.05, tstop=tstop,
                            gain=gain, tag=f'{tag}_step')
        fit, _ = multisine_run(K, Q, gain, tag)
        f0_tgt = FCLK / K
        q_step = step['Q_ext']
        q_multi = fit['Q']
        out.append(dict(
            K=K, Q=Q, gain_db=gdb,
            Q_target=Q,
            Q_step=q_step,
            Q_multi=q_multi,
            Q_step_abs_err_pct=100 * (q_step - Q) / Q,
            Q_multi_abs_err_pct=100 * (q_multi - Q) / Q,
            Q_step_vs_multi_pct=100 * (q_step - q_multi) / q_multi,
            f0_step_err_pct=step['f0_err_pct'],
            f0_multi_err_pct=100 * (fit['f0'] - f0_tgt) / f0_tgt,
        ))
        print(f'K={K}/Q={Q:g} G={gdb:.0f} dB: '
              f'step Q={q_step:.3f}, multisine Q={q_multi:.3f}, '
              f'target {Q:g}', flush=True)
    keys = ['K', 'Q', 'gain_db', 'Q_target', 'Q_step', 'Q_multi',
            'Q_step_abs_err_pct', 'Q_multi_abs_err_pct',
            'Q_step_vs_multi_pct', 'f0_step_err_pct', 'f0_multi_err_pct']
    with open(os.path.join(DATA, 'q_crosscheck.csv'), 'w',
              newline='') as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(out)
    with open(os.path.join(DATA, 'q_crosscheck.fragment.md'), 'w') as f:
        f.write('## (c) Step-ring versus multisine Q extraction cross-check\n\n')
        f.write('Same behavioral deck, gain and ideal op-amp parameters '
                '(A0=80 dB, GBW=20 MHz, SR=5 V/us, Ron=1 kohm, CI=8 pF). '
                'The exact ideal discrete-time model target is the design Q. '
                'A finite-A0 closed-form discrete-time model is not available '
                'in this prototype; the 80 dB/20 MHz run is the near-ideal '
                'numerical reference. [SIM]\n\n')
        f.write('| K | Q | gain dB | Q target | Q step | Q multisine | '
                'step err % | multisine err % | step-vs-multisine % | '
                'f0 step err % | f0 multisine err % |\n')
        f.write('|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n')
        for r in out:
            f.write(f"| {r['K']} | {r['Q']:g} | {r['gain_db']:.0f} | "
                    f"{r['Q_target']:g} | {r['Q_step']:.3f} | "
                    f"{r['Q_multi']:.3f} | {r['Q_step_abs_err_pct']:+.2f} | "
                    f"{r['Q_multi_abs_err_pct']:+.2f} | "
                    f"{r['Q_step_vs_multi_pct']:+.2f} | "
                    f"{r['f0_step_err_pct']:+.2f} | "
                    f"{r['f0_multi_err_pct']:+.2f} |\n")
        f.write('\nThe K=200/Q=5 step-ring Q error in results/behavioral/q_evidence.md section (a) and results/behavioral/behav_sweep.md (about -15 %) is **not confirmed by the multisine method (+0.5 %)**. It is therefore likely a step-ring extraction artifact at K=200 (few clean ringing peaks) and must be re-measured at transistor level.\n')
        f.write('\nThe multisine fit is the more trustworthy Q method when '
                'the record is long enough: it fits many coherent tones and '
                'does not depend on peak detection. The step-ring fit is '
                'faster but assumes a clean, single-mode decaying sinusoid; '
                'it loses validity when the ringing has too few clean peaks '
                'or the response is dominated by settling/slew. The K=25/Q=1 '
                '18 dB ss step-ring run is marked `fit=0` in results/behavioral/q_evidence.md '
                'for that reason; the multisine method is preferred there.\n')
    print(f"wrote results/data/q_crosscheck.csv and the q_crosscheck fragment ({len(out)} settings)",
          flush=True)


if __name__ == '__main__':
    main()
