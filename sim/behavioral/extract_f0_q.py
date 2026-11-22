#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Extract f0, Q and gain from transient sine-tone runs of the biquad.

ngspice has no periodic steady-state AC for switched-capacitor circuits, so
frequency response is measured from transients.  Two modes:

  multi (default)  One long transient run with a multisine stimulus (the
        Vsig source is rewritten to a chain of series SIN sources), then a
        per-tone least-squares fit y(t) = A cos(wt) + B sin(wt) + C over the
        settled tail of the record gives gain and phase per tone, and a 2-D
        grid fit of the exact z-domain transfer function gives f0 and Q.
        This is the prototype flow (results/behav_tones.csv).
  tones  The same, but one transient run per tone ("about 20 transient sine
        tones"); slower (one ngspice run per tone) but independent points.

The decks are rendered from sim/behavioral/biquad_behav.spice the same way
run_sweep.py does.  No PDK needed (PDK-free behavioral deck).

Runtime: multi mode ~1 min (one long run); tones mode ~10 s per tone.

Run:  python3 sim/behavioral/extract_f0_q.py [--mode multi|tones]
      [--K 100 --Q 5 --fclk 500e3 --ntones 10]
"""
import csv
import math
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, '..', '..', 'results')
sys.path.insert(0, os.path.join(HERE, '..'))
from capbudget import design_exact  # noqa: E402

import run_sweep as rs  # same directory: reuses render/run_ngspice/load_wrdata


def sample_tail(d, T, n_settle_cycles, n_tone_periods, f_tone):
    """Return (t, y) over the last n_tone_periods periods of the tone."""
    n_tone_cycles = int(round((1.0 / f_tone) / T))
    t_lo = (n_settle_cycles + 1) * T
    t_hi = t_lo + n_tone_periods * n_tone_cycles * T
    m = (d['t'] > t_lo) & (d['t'] < min(t_hi, d['t'][-1]))
    return d['t'][m], d['l'][m], d['b'][m]


def fit_sine(t, y, f, extra_harm=0):
    """LS fit y = sum_k [a_k cos(kwt) + b_k sin(kwt)] + c."""
    w = 2.0 * math.pi * f
    cols = [np.cos(w * t), np.sin(w * t), np.ones_like(t)]
    for h in range(2, extra_harm + 2):
        cols += [np.cos(h * w * t), np.sin(h * w * t)]
    A = np.column_stack(cols)
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    amp = math.hypot(coef[0], coef[1])
    ph = math.degrees(math.atan2(-coef[1], coef[0]))
    resid = y - A @ coef
    return dict(amp=amp, phase=ph, dc=coef[2],
                rms_resid=float(np.sqrt(np.mean(resid ** 2))))


def H_lp(theta, a, a_d, w, gain=1.0):
    """Exact LP transfer function of the discrete map at w (rad/sample)."""
    M = np.array([[1.0 / (1.0 + a_d), a / (1.0 + a_d)],
                  [-a, 1.0]])
    Bv = np.array([gain * a / (1.0 + a_d), 0.0])
    H = np.linalg.solve(np.array([[np.exp(1j * w) - M[0, 0], -M[0, 1]],
                                  [-M[1, 0], np.exp(1j * w) - M[1, 1]]]), Bv)
    return H[1]


def fit_f0_q(f0_guess, Q_guess, fclk, tones, gains, gain_scale=1.0):
    """Grid fit of (f0, Q) to the measured tone gains (linear magnitude)."""
    fs = np.array(tones)
    gv = np.array(gains)
    th0 = 2 * math.pi * f0_guess / fclk
    wv = 2 * math.pi * fs / fclk
    best = (1e99, None)
    for r in np.linspace(0.55, 0.9995, 1201):
        ths = np.linspace(th0 * 0.90, th0 * 1.10, 401)
        u = 2 * r * np.cos(ths) - 1.0
        ok = u > 0
        ths, u = ths[ok], u[ok]
        if len(ths) == 0:
            continue
        arg = r * r / u - 1.0
        ok2 = arg > 0
        ths, u = ths[ok2], u[ok2]
        a = np.sqrt(arg[ok2])
        ad = 1.0 / u - 1.0
        for th, aa, add in zip(ths, a, ad):
            hv = np.array([abs(H_lp(th, aa, add, w, gain_scale))
                              for w in wv])
            err = float(np.sum((hv - gv) ** 2))
            if err < best[0]:
                best = (err, (th, r, aa, add))
    err, (th, r, a, add) = best
    return dict(f0=th * fclk / (2 * math.pi), Q=th / (-2 * math.log(r)),
                sq_err=err, a=a, a_d=add)


def tone_ladder(f0, n):
    """Geometric, non-harmonically related ladder 0.2*f0 .. 1.3*f0."""
    return [f0 * 0.2 * (6.5 ** (i / (n - 1))) for i in range(n)]


def multisine_lines(tones, amp):
    """Series chain of SIN sources: sig = sum of tones (classic trick)."""
    lines = [f'Vms1 m1 0 SIN(0 {amp:g} {tones[0]:g})']
    for i, f in enumerate(tones[1:], start=2):
        lines.append(f'Vms{i} m{i} m{i - 1} SIN(0 {amp:g} {f:g})')
    lines.append(f'Bip vinp 0 V = VCM + V(m{i_last(len(tones))})')
    lines.append(f'Bin vinn 0 V = VCM - V(m{i_last(len(tones))})')
    return lines


def i_last(n):
    return n


def write_deck(sp, text):
    with open(sp, 'w') as f:
        f.write(text)


def nominal_settle(K, Q):
    """Cycles for the pole envelope to decay below 2% (+60 margin)."""
    theta, _, _ = design_exact(K, Q)
    r = math.exp(-theta / (2.0 * Q))
    return int(math.log(0.02) / math.log(r)) + 60 if r < 1 else 5000


def stimulation(text, lines):
    """Replace the Vsig/Bip/Bin stimulus block with `lines`."""
    out = []
    skipping = False
    for ln in text.split('\n'):
        if ln.startswith('Vsig sig 0'):
            out.extend(lines[:-2])
            skipping = True
            continue
        if skipping and (ln.startswith('Bip ') or ln.startswith('Bin ')):
            continue
        if skipping and not (ln.startswith('Bip ') or ln.startswith('Bin ')):
            skipping = False
        out.append(ln)
    # append the B sources from lines[-2:] right after the tone chain
    txt = '\n'.join(out)
    anchor = out[[i for i, l in enumerate(out)
                  if l.startswith('Vms')][-1]]
    idx = [i for i, l in enumerate(out) if l.startswith('Vms')][-1]
    out = out[:idx + 1] + lines[-2:] + out[idx + 1:]
    return '\n'.join(out)


def main():
    argv = sys.argv
    mode = 'multi'
    if '--mode' in argv:
        mode = argv[argv.index('--mode') + 1]
    K = int(argv[argv.index('--K') + 1]) if '--K' in argv else 100
    Q = float(argv[argv.index('--Q') + 1]) if '--Q' in argv else 5.0
    fclk = float(argv[argv.index('--fclk') + 1]) if '--fclk' in argv else 500e3
    ntones = int(argv[argv.index('--ntones') + 1]) if '--ntones' in argv else 10
    gain = float(argv[argv.index('--gain') + 1]) if '--gain' in argv else 1.0
    amp = 0.01  # per tone; 10 tones x 10 mV keeps the input well inside +-1 V

    f0_tgt = fclk / K
    tones = tone_ladder(f0_tgt, ntones)
    n_settle = nominal_settle(K, Q)
    rows = []
    print(f'tones: ' + ', '.join(f'{f:.0f}' for f in tones), flush=True)

    if mode == 'multi':
        # one run long enough for settling + 15 periods of the lowest tone
        n_tone_cycles = int(round((1.0 / tones[0]) * fclk))
        tstop = (n_settle + 15 * n_tone_cycles) / fclk
        dat = os.path.join(HERE, 'tone_multi.dat')
        sp = os.path.join(HERE, 'tone_multi.gen.spice')
        text, _ = rs.render(K=K, Q=Q, fclk=fclk, tstop=tstop,
                            tmaxstep=2e-8, dat='tone_multi.dat')
        text = stimulation(text, multisine_lines(tones, amp))
        write_deck(sp, text)
        r = subprocess.run(['ngspice', '-b', 'tone_multi.gen.spice'],
                           cwd=HERE, capture_output=True, text=True,
                           timeout=280)
        if not os.path.exists(dat):
            sys.exit(f'ngspice failed: {(r.stdout + r.stderr)[-300:]}')
        d = rs.load_wrdata(dat)
        os.remove(dat)
        t, yl, yb = sample_tail(d, 1.0 / fclk, n_settle + 1,
                                12, tones[0])
        for f in tones:
            fit_l = fit_sine(t, yl, f, extra_harm=2)
            fit_b = fit_sine(t, yb, f)
            rows.append(dict(f=f, gain_l_dB=20 * math.log10(fit_l['amp'] / amp),
                             ph_l=fit_l['phase'], resid_l=fit_l['rms_resid'],
                             gain_b_dB=20 * math.log10(fit_b['amp'] / amp),
                             ph_b=fit_b['phase'], resid_b=fit_b['rms_resid']))
            print(f"  {f:8.1f} Hz: LP {rows[-1]['gain_l_dB']:+.3f} dB "
                  f"BP {rows[-1]['gain_b_dB']:+.3f} dB "
                  f"(resid {rows[-1]['resid_l']:.2e} V)", flush=True)
    elif mode == 'tones':
        for f in tones:
            n_tone_cycles = int(round((1.0 / f) * fclk))
            tstop = (n_settle + 15 * n_tone_cycles) / fclk
            tag = f'tone_{K}_{Q:g}_{f:.0f}'
            try:
                dat, _ = rs.run_ngspice(tag, K=K, Q=Q, fclk=fclk,
                                        stim='sine', fsig=f, amp=amp,
                                        tstop=tstop, tmaxstep=2e-8)
            except RuntimeError as e:
                print(f'  {f:.0f} Hz: FAILED {e}', flush=True)
                continue
            d = rs.load_wrdata(dat)
            os.remove(dat)
            t, yl, yb = sample_tail(d, 1.0 / fclk, n_settle + 1,
                                    12, f)
            fit_l = fit_sine(t, yl, f, extra_harm=2)
            fit_b = fit_sine(t, yb, f)
            rows.append(dict(f=f, gain_l_dB=20 * math.log10(fit_l['amp'] / amp),
                             ph_l=fit_l['phase'], resid_l=fit_l['rms_resid'],
                             gain_b_dB=20 * math.log10(fit_b['amp'] / amp),
                             ph_b=fit_b['phase'], resid_b=fit_b['rms_resid']))
            print(f"  {f:8.1f} Hz: LP {rows[-1]['gain_l_dB']:+.3f} dB "
                  f"BP {rows[-1]['gain_b_dB']:+.3f} dB", flush=True)
    else:
        sys.exit(f'unknown mode {mode!r} (multi|tones)')

    if len(rows) >= 3:
        fit = fit_f0_q(f0_tgt, Q, fclk, [r['f'] for r in rows],
                       [10 ** (r['gain_l_dB'] / 20) for r in rows],
                       gain_scale=gain)
        print(f"\nLP fit: f0 = {fit['f0']:.1f} Hz (target {f0_tgt:.1f}, "
              f"{100 * (fit['f0'] - f0_tgt) / f0_tgt:+.2f}%), "
              f"Q = {fit['Q']:.3f} (target {Q:g}, "
              f"{100 * (fit['Q'] - Q) / Q:+.2f}%)", flush=True)
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, 'behav_tones.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, list(rows[0].keys()) if rows else ['f'])
        w.writeheader()
        w.writerows(rows)
    print(f"wrote results/behav_tones.csv ({len(rows)} tones)", flush=True)


if __name__ == '__main__':
    main()
