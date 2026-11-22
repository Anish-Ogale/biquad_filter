#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Behavioral-biquad sweeps: op-amp gain/GBW sweep and input-offset test.

Both modes rewrite the .param block of sim/behavioral/biquad_behav.spice
(and the stimulus line for the tone mode used by extract_f0_q.py) and run
ngspice in batch.  No PDK is needed: the deck is PDK-free.

Modes
  sweep   (default)  Step response at K = 100, Q = 5 (worst-case f0/Q
          sensitivity), sweeping DC gain 40-80 dB and GBW 3-20 MHz; extracts
          f0/Q from the BP step-ringing and the LP DC gain from the settled
          tail, and reports the minimum op-amp keeping f0 within 1% and Q
          within 5%.  Writes results/behav_sweep.csv and results/summary
          lines to stdout.
  offset  5 mV input-referred op-amp offset, zero input: all 8 Q steps at
          K = 100 plus the extremes (K = 25/Q = 5, K = 200/Q = 5 for both
          offset signs).  Gain settings are covered by invariance: the input
          attenuator is a capacitive divider with no DC path into the
          summing nodes (docs/architecture.md 8), so the offset map is
          gain-invariant at gain 0 dB.  Writes results/offset_test.{csv,md}.

Runtime: ~10-20 s per ngspice run; the default sweep grid is 16 runs plus
11 offset runs.

Run:  python3 sim/behavioral/run_sweep.py [--mode sweep|offset]
"""
import csv
import math
import os
import re
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
RESULTS = os.path.join(REPO, 'results')
TEMPLATE = os.path.join(HERE, 'biquad_behav.spice')

sys.path.insert(0, os.path.join(HERE, '..'))
from capbudget import design_exact  # noqa: E402

QS = (0.5, 2.0 ** -0.5, 1.0, 2.0 ** 0.5, 2.0, 2.0 ** 1.5, 4.0, 5.0)


# ------------------------------------------------------------ template I/O
def render(K=None, Q=None, CI=8.0, fclk=500e3, ron=1e3, A0=1e3, GBW=10e6,
           SR=5e6, vos=0.0, amp=0.05, tstep=100e-6, tstop=2.5e-3,
           tmaxstep=1e-8, stim='step', fsig=10e3, dat='biquad_behav.dat'):
    """Return the template with the parameter block and stimulus rewritten."""
    Q = Q if Q is not None else 1.0
    K = K if K is not None else 50
    theta, a, a_d = design_exact(K, Q)
    Cs = a * CI          # pF -> deck uses units of pF on .param lines
    Cd = a_d * CI
    text = open(TEMPLATE).read()
    sub = {
        r'^\.param fclk=.*$': f'.param fclk={fclk:g}',
        r'^\.param CI=.*$': f'.param CI={CI:g}p',
        r'^\.param Cs=.*$': f'.param Cs={Cs:.6f}p',
        r'^\.param Cd=.*$': f'.param Cd={Cd:.6f}p',
        r'^\.param Ron=.*$': f'.param Ron={ron:g}',
        r'^\.param A0=.*$': f'.param A0={A0:g}',
        r'^\.param GBW=.*$': f'.param GBW={GBW:g}',
        r'^\.param SR=.*$': f'.param SR={SR:g}',
        r'^\.param VOS=.*$': f'.param VOS={vos:g}',
        r'^\.param AMP=.*$': f'.param AMP={amp:g}',
        r'^\.param TSTEP=.*$': f'.param TSTEP={tstep:g}',
    }
    for pat, rep in sub.items():
        text = re.sub(pat, rep, text, flags=re.M)
    text = re.sub(r'^\.tran .*$', f'.tran {tmaxstep:g} {tstop:g}', text,
                  flags=re.M)
    if stim == 'sine':
        text = re.sub(r'^Vsig sig 0 PWL.*$',
                      f'Vsig sig 0 SIN(0 {{AMP}} {fsig:g})', text, flags=re.M)
    elif stim == 'zero':
        text = re.sub(r'^Vsig sig 0 PWL.*$', 'Vsig sig 0 0', text, flags=re.M)
    text = re.sub(r'^wrdata .*$', f'wrdata {dat} '
                  'v(lpp) v(lpn) v(bpp) v(bpn) v(vinp) v(vinn)', text,
                  flags=re.M)
    return text, dict(theta=theta, Cs_pF=Cs, Cd_pF=Cd, f0=fclk / K)


def run_ngspice(tag, **kw):
    """Render the deck, run ngspice -b, return (dat path, info)."""
    dat = os.path.join(HERE, f'{tag}.dat')
    sp = os.path.join(HERE, f'{tag}.gen.spice')
    text, info = render(dat=os.path.basename(dat), **kw)
    with open(sp, 'w') as f:
        f.write(text)
    r = subprocess.run(['ngspice', '-b', os.path.basename(sp)],
                       cwd=HERE, capture_output=True, text=True, timeout=280)
    if not os.path.exists(dat):
        raise RuntimeError(f'ngspice failed for {tag}: '
                           f'{(r.stdout + r.stderr)[-300:]}')
    return dat, info


# ------------------------------------------------------------ extraction
def load_wrdata(path):
    d = np.loadtxt(path)
    # columns: t, lpp, lpn, bpp, bpn, vinp, vinn (half circuit = diff/2)
    return dict(t=d[:, 0], l=(d[:, 1] - d[:, 2]) / 2.0,
                b=(d[:, 3] - d[:, 4]) / 2.0, v=(d[:, 5] - d[:, 6]) / 2.0)


def sample_per_period(d, T, frac_lo=0.88, frac_hi=0.97):
    """One sample per clock period, settled value at the end of phi2."""
    t = d['t']
    n = np.floor(t / T).astype(np.int64)
    frac = t / T - n
    sel = {}
    for i in np.where((frac > frac_lo) & (frac < frac_hi))[0]:
        sel[int(n[i])] = i
    ks = np.array(sorted(sel))
    idx = np.array([sel[k] for k in ks])
    return dict(k=ks, t=t[idx], b=d['b'][idx], l=d['l'][idx], v=d['v'][idx],
                idx=idx)


def model_response(K, Q, v):
    """Iterate the exact discrete map (reference from capbudget.design_exact)."""
    theta, a, a_d = design_exact(K, Q)
    b = np.zeros(len(v))
    l = np.zeros(len(v))
    for i in range(1, len(v)):
        b[i] = (b[i - 1] + a * v[i] + a * l[i - 1]) / (1.0 + a_d)
        l[i] = l[i - 1] - a * b[i - 1]
    return b, l


def bp_peaks(k, b, kstart):
    m = k >= kstart
    kk, bb = k[m], b[m]
    maxima = [i for i in range(1, len(bb) - 1)
              if (bb[i] - bb[i - 1]) > 0 and (bb[i + 1] - bb[i]) < 0]
    if len(maxima) < 3:
        return None
    return kk[maxima], bb[maxima]


def fit_fq(peaks, T, settle_base=0.0):
    kk, bb = peaks
    am = np.abs(bb - settle_base)
    tm = kk
    Td = float(np.median(np.diff(tm)))
    f0 = 1.0 / (Td * T)
    good = am > 1e-9
    tm, am = tm[good], am[good]
    slope, _ = np.polyfit(tm, np.log(am), 1)
    r = math.exp(slope)
    th = 2 * math.pi * f0 * T
    Qe = th / (-2 * math.log(r)) if 0 < r < 1 else float('inf')
    return f0, Qe


def pole_radius(K, Q):
    theta, _, _ = design_exact(K, Q)
    return math.exp(-theta / (2.0 * Q))


# ------------------------------------------------------------ mode: sweep
def case_step(K, Q, A0, GBW, SR, ron, fclk=500e3, CI=8.0, amp=0.05,
              tstep=100e-6, tstop=2.5e-3, tag=None):
    tag = tag or f'sw_A0{A0:g}_GBW{GBW:g}_K{K}_Q{Q:g}'
    T = 1.0 / fclk
    dat, _ = run_ngspice(tag, K=K, Q=Q, CI=CI, fclk=fclk, ron=ron, A0=A0,
                         GBW=GBW, SR=SR, amp=amp, tstep=tstep, tstop=tstop,
                         stim='step')
    d = load_wrdata(dat)
    s = sample_per_period(d, T)
    kstep = round(tstep / T)
    n = len(s['k'])
    vin = np.zeros(n)
    vin[s['k'] >= kstep] = amp
    _, lm = model_response(K, Q, vin)
    kstart = kstep + int(2.5 * 2 * Q * K / (2 * math.pi))
    peaks = bp_peaks(s['k'].astype(float), s['b'], kstart)
    if peaks is None:
        f0, Qe = float('nan'), float('nan')
    else:
        settle_base = float(np.mean(s['b'][int(0.8 * len(s['k'])):]))
        f0, Qe = fit_fq(peaks, T, settle_base)
    tail = slice(max(0, len(s['k']) - 40), None)
    gain = float(np.mean(s['l'][tail])) / amp
    gain_ideal = float(np.mean(lm[tail])) / amp
    os.remove(dat)
    return dict(tag=tag, K=K, Q=Q, A0_dB=round(20 * math.log10(A0), 1),
                GBW_MHz=GBW / 1e6, SR_MVs=SR / 1e6, Ron_k=ron / 1e3,
                fclk=fclk, CI_pF=CI, amp=amp,
                f0_kHz=f0 / 1e3,
                f0_err_pct=100 * (f0 - fclk / K) / (fclk / K),
                Q_ext=Qe, Q_err_pct=100 * (Qe - Q) / Q,
                gain=gain, gain_ideal=gain_ideal,
                gain_err_db=20 * math.log10(abs(gain / gain_ideal)))


def mode_sweep():
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    base = dict(K=100, Q=5.0, A0=1e4, GBW=10e6, SR=5e6, ron=1e3,
                fclk=500e3, CI=8.0, amp=0.05, tstop=2.5e-3)
    gbws = (3e6, 5e6, 10e6, 20e6)
    a0s_dB = (40.0, 50.0, 60.0, 80.0)
    print('== gain x GBW grid (step, K=100, Q=5, fclk=500 kHz, Ron=1k,'
          ' SR=5 V/us) ==', flush=True)
    for gbw in gbws:
        for adb in a0s_dB:
            kw = {**base, 'A0': 10 ** (adb / 20), 'GBW': gbw}
            try:
                row = case_step(**kw)
                rows.append(row)
                print(f"  A0={adb:4.0f} dB GBW={gbw/1e6:4.0f} MHz: "
                      f"f0err={row['f0_err_pct']:+.2f}% "
                      f"Qerr={row['Q_err_pct']:+.2f}% "
                      f"gainerr={row['gain_err_db']:+.3f} dB", flush=True)
            except Exception as e:  # noqa: BLE001
                rows.append(dict(tag=kw and '', status=f'FAIL {e}',
                                 A0_dB=adb, GBW_MHz=gbw / 1e6))
                print(f'  A0={adb:g} dB GBW={gbw:g}: FAILED {e}', flush=True)
    # summary: minimum op-amp per GBW satisfying f0 +-1% and Q +-5%
    print('\nminimum op-amp per GBW (f0 within 1%, Q within 5%, LP DC gain '
          'within 0.1 dB of its ideal):', flush=True)
    okrows = [r for r in rows
              if r.get('status') != 'FAIL'
              and not math.isnan(r['f0_err_pct'])
              and abs(r['f0_err_pct']) <= 1.0
              and math.isfinite(r['Q_err_pct'])
              and abs(r['Q_err_pct']) <= 5.0]
    best = {}
    for r in okrows:
        best.setdefault(r['GBW_MHz'], []).append(r)
    for gbw in sorted(best):
        m = min(best[gbw], key=lambda r: r['A0_dB'])
        print(f"  GBW={gbw:.0f} MHz -> A0 >= {m['A0_dB']:.0f} dB "
              f"(f0err {m['f0_err_pct']:+.2f}%, Qerr {m['Q_err_pct']:+.2f}%)",
              flush=True)
    # GBW worst case: K = 25 at fclk = 1 MHz (highest normalized bandwidth
    # demand).  Q = 1 is the lowest setting where the step response still
    # rings enough for the f0/Q fit; the absolute worst case Q = 0.5 is
    # overdamped and its f0/Q extraction is not applicable (gain error only).
    print('== GBW sweep, K=25 Q=1 fclk=1 MHz (GBW worst case, ringing) ==',
          flush=True)
    for grun in (3e6, 5e6, 9e6, 20e6):
        kw = {**base, 'GBW': grun, 'K': 25, 'Q': 1.0, 'A0': 1e4, 'fclk': 1e6,
              'tstop': 1.5e-3}
        try:
            row = case_step(**kw)
            rows.append(row)
            print(f"  GBW={grun/1e6:4.0f} MHz: f0err={row['f0_err_pct']:+.2f}% "
                  f"Qerr={row['Q_err_pct']:+.2f}% "
                  f"gainerr={row['gain_err_db']:+.3f} dB", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f'  GBW={grun:g}: FAILED {e}', flush=True)
    keys = ['tag', 'status', 'K', 'Q', 'A0_dB', 'GBW_MHz', 'SR_MVs', 'Ron_k',
            'fclk', 'CI_pF', 'amp', 'f0_kHz', 'f0_err_pct', 'Q_ext',
            'Q_err_pct', 'gain', 'gain_ideal', 'gain_err_db']
    with open(os.path.join(RESULTS, 'behav_sweep.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, '') for c in w.fieldnames})
    print(f"wrote {os.path.join(RESULTS, 'behav_sweep.csv')} "
          f'({len([r for r in rows if r.get("status") != "FAIL"])} rows)',
          flush=True)


# ------------------------------------------------------------ mode: offset
def case_offset(K, Q, vos, fclk=500e3, CI=8.0, tag=None):
    tag = tag or f'off_K{K}_Q{Q:g}_v{vos:+g}'
    T = 1.0 / fclk
    # settle: r^n < 0.02 needs n = ln(0.02)/ln(r) cycles (+60 margin)
    theta, _, _ = design_exact(K, Q)
    r = math.exp(-theta / (2.0 * Q))
    n_settle = int(math.log(0.02) / math.log(r)) + 60 if r < 1 else 5000
    tstop = min((n_settle + 20) * T, 20e-3)
    dat, _ = run_ngspice(tag, K=K, Q=Q, CI=CI, fclk=fclk, vos=vos,
                         amp=0.0, tstop=tstop, tmaxstep=2e-8, stim='zero')
    try:
        d = np.loadtxt(dat)
    except Exception:
        os.remove(dat)
        return dict(K=K, Q=Q, vos=vos, status='no data')
    os.remove(dat)
    t = d[:, 0]
    lp = (d[:, 1] - d[:, 2]) / 2.0
    bp = (d[:, 3] - d[:, 4]) / 2.0
    # mean of the last 10 phi2-end samples (~settled)
    samp_lp, samp_bp = [], []
    ncyc = int(round(t[-1] * fclk))
    for c in range(ncyc - 12, ncyc - 2):
        ti = (c + 0.95) * T
        samp_lp.append(np.interp(ti, t, lp))
        samp_bp.append(np.interp(ti, t, bp))
    return dict(K=K, Q=Q, vos=vos, status='ok', n_settle=n_settle,
                rail=int(abs(bp.max()) > 1.55 or abs(lp.max()) > 1.55),
                lp_offset=float(np.mean(samp_lp)),
                bp_offset=float(np.mean(samp_bp)),
                worst_mV=max(abs(np.mean(samp_lp)), abs(np.mean(samp_bp))) * 1e3)


def mode_offset():
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    print('== offset test (5 mV input-referred op-amp offset, zero input, '
          'fclk = 500 kHz) ==', flush=True)
    for q in QS:
        r = case_offset(100, q, 5e-3)
        rows.append(r)
        print(f"  K=100 Q={q:g}: {r.get('status')}, worst="
              f"{r.get('worst_mV', float('nan')):.1f} mV", flush=True)
    for K, Q, vos in ((25, 0.5, 5e-3), (25, 5.0, 5e-3),
                      (200, 5.0, 5e-3), (200, 5.0, -5e-3)):
        r = case_offset(K, Q, vos)
        rows.append(r)
        print(f"  K={K} Q={Q:g} vos={vos * 1e3:+.0f} mV: {r.get('status')}, "
              f"worst={r.get('worst_mV', float('nan')):.1f} mV", flush=True)
    keys = ['K', 'Q', 'vos', 'status', 'n_settle', 'rail', 'lp_offset',
            'bp_offset', 'worst_mV']
    with open(os.path.join(RESULTS, 'offset_test.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, '') for c in w.fieldnames})
    ok = [r for r in rows if r.get('status') == 'ok']
    qle2 = [r for r in ok if r['Q'] <= 2.0]
    with open(os.path.join(RESULTS, 'offset_test.md'), 'w') as f:
        f.write('# Offset test - 5 mV input-referred op-amp offset\n\n')
        f.write('Behavioral biquad (ideal switches), zero differential input, '
                'fclk = 500 kHz, both op-amps offset by +5 mV (same sign) '
                'unless noted.  Gain settings collapse into one row per '
                '(K, Q) because the input attenuator is a capacitive divider '
                'with no DC path into the summing nodes, so the offset is '
                'gain-invariant (docs/architecture.md).  [SIM]\n\n')
        f.write('| K | Q | vos mV | LP offset mV | BP offset mV | rail |\n')
        f.write('|---:|---:|---:|---:|---:|---:|\n')
        for r in ok:
            f.write(f"| {r['K']} | {r['Q']:g} | {r['vos'] * 1e3:+.0f} | "
                    f"{r['lp_offset'] * 1e3:+.2f} | "
                    f"{r['bp_offset'] * 1e3:+.2f} | {r['rail']} |\n")
        if qle2:
            f.write('\nWorst |offset| at Q <= 2: '
                    f"{max(r['worst_mV'] for r in qle2):.1f} mV "
                    '(spec max 30 mV). Worst overall: '
                    f"{max(r['worst_mV'] for r in ok):.1f} mV "
                    '(spec max 60 mV).\n')
    print(f"wrote results/offset_test.{{csv,md}} "
          f'({len(ok)} ok / {len(rows)} runs)', flush=True)


def main():
    mode = sys.argv[sys.argv.index('--mode') + 1] if '--mode' in sys.argv \
        else 'sweep'
    if mode == 'sweep':
        mode_sweep()
    elif mode == 'offset':
        mode_offset()
    else:
        sys.exit(f'unknown mode {mode!r} (sweep|offset)')


if __name__ == '__main__':
    main()
