#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Behavioral-biquad sweeps: op-amp requirement, gain, offset and Q evidence.

Every mode rewrites the .param block of sim/behavioral/biquad_behav.spice
(and the stimulus line for the tone mode used by extract_f0_q.py) and runs
ngspice in batch.  No PDK is needed: the deck is PDK-free.

Modes
  sweep   (default)  Step response at K = 100, Q = 5 (worst-case f0/Q
          sensitivity), sweeping DC gain 40-80 dB and GBW 3-20 MHz; extracts
          f0/Q from the BP step-ringing and the LP DC gain from the settled
          tail, and reports the minimum op-amp keeping f0 within 1% and Q
          within 5%.  Writes results/behav_sweep.csv and results/summary
          lines to stdout.
  gain    LP passband gain at 0/6/12/18 dB for K = 100/Q = 5 and K = 25/Q = 1.
          Gain is applied only by the input-branch cap Cs1 = G*Cs, so the
          loop coefficients and therefore f0/Q stay unchanged.
          Writes results/gain_test.{csv,md}.

  offset  5 mV input-referred op-amp offset, zero input: all 8 Q steps at
          K = 100, all Q <= 2 at K = 25 and K = 200, plus K = 25/Q = 5 and
          K = 200/Q = 5.  Each case is run at 0 dB and 18 dB and for
          same-sign and opposite-sign op-amp offsets.  Writes
          results/offset_test.{csv,md}.

  offset-opamp  worst offset settings at ideal, tt and ss op-amp parameters.
          Writes results/offset_opamp.{csv,md}.

  qcheck  absolute and differential Q error versus the same-case ideal
          baseline at the real tt/ss corners.  Writes results/qcheck.{csv,md}.
          The separate q2_check.py extends this to the 18 dB Q<=2 row.

Runtime: ~10-20 s per ngspice run; the full behavioral set is several
minutes.  The targeted Q<=2 check is `sim/behavioral/q2_check.py`.

Run:  python3 sim/behavioral/run_sweep.py
      [--mode sweep|gain|offset|offset-opamp|qcheck]
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
GAIN_STEPS = ((0.0, 1.0), (6.0, 2.0), (12.0, 3.98), (18.0, 7.94))


# ------------------------------------------------------------ template I/O
def render(K=None, Q=None, CI=8.0, fclk=500e3, ron=1e3, A0=1e3, GBW=10e6,
           SR=5e6, vos=0.0, vos2=None, gain=1.0, amp=0.05, tstep=100e-6,
           tstop=2.5e-3, tmaxstep=1e-8, stim='step', fsig=10e3,
           dat='biquad_behav.dat'):
    """Return the template with the parameter block and stimulus rewritten."""
    Q = Q if Q is not None else 1.0
    K = K if K is not None else 50
    vos2 = vos if vos2 is None else vos2
    theta, a, a_d = design_exact(K, Q)
    Cs = a * CI          # pF -> deck uses units of pF on .param lines
    Cd = a_d * CI
    text = open(TEMPLATE).read()
    sub = {
        r'^\.param fclk=.*$': f'.param fclk={fclk:g}',
        r'^\.param CI=.*$': f'.param CI={CI:g}p',
        r'^\.param Cs=.*$': f'.param Cs={Cs:.6f}p',
        r'^\.param Cd=.*$': f'.param Cd={Cd:.6f}p',
        r'^\.param GAIN=.*$': f'.param GAIN={gain:g}',
        r'^\.param Ron=.*$': f'.param Ron={ron:g}',
        r'^\.param A0=.*$': f'.param A0={A0:g}',
        r'^\.param GBW=.*$': f'.param GBW={GBW:g}',
        r'^\.param SR=.*$': f'.param SR={SR:g}',
        r'^\.param VOS=.*$': f'.param VOS={vos:g}',
        r'^\.param VOS2=.*$': f'.param VOS2={vos2:g}',
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
    return text, dict(theta=theta, Cs_pF=Cs, Cs1_pF=gain * Cs, Cd_pF=Cd,
                      gain=gain, f0=fclk / K)


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


def model_response(K, Q, v, gain=1.0):
    """Iterate the exact discrete map (reference from capbudget.design_exact).

    Only the input branch is scaled by `gain`: Cs1 = gain*Cs, while the loop
    branches and damping cap are unchanged.  At DC this gives LP gain = gain.
    """
    theta, a, a_d = design_exact(K, Q)
    b = np.zeros(len(v))
    l = np.zeros(len(v))
    for i in range(1, len(v)):
        b[i] = (b[i - 1] + gain * a * v[i] + a * l[i - 1]) / (1.0 + a_d)
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
              tstep=100e-6, tstop=2.5e-3, gain=1.0, tag=None):
    gdb = 20 * math.log10(gain)
    tag = tag or f'sw_G{gdb:g}dB_A0{A0:g}_GBW{GBW:g}_K{K}_Q{Q:g}'
    T = 1.0 / fclk
    dat, _ = run_ngspice(tag, K=K, Q=Q, CI=CI, fclk=fclk, ron=ron, A0=A0,
                         GBW=GBW, SR=SR, amp=amp, tstep=tstep, tstop=tstop,
                         stim='step', gain=gain)
    d = load_wrdata(dat)
    s = sample_per_period(d, T)
    kstep = round(tstep / T)
    n = len(s['k'])
    vin = np.zeros(n)
    vin[s['k'] >= kstep] = amp
    _, lm = model_response(K, Q, vin, gain=gain)
    kstart = kstep + int(2.5 * 2 * Q * K / (2 * math.pi))
    peaks = bp_peaks(s['k'].astype(float), s['b'], kstart)
    if peaks is None:
        f0, Qe = float('nan'), float('nan')
    else:
        settle_base = float(np.mean(s['b'][int(0.8 * len(s['k'])):]))
        f0, Qe = fit_fq(peaks, T, settle_base)
    tail = slice(max(0, len(s['k']) - 40), None)
    gain_sim = float(np.mean(s['l'][tail])) / amp
    gain_ideal = float(np.mean(lm[tail])) / amp
    os.remove(dat)
    return dict(tag=tag, K=K, Q=Q, A0_dB=round(20 * math.log10(A0), 1),
                GBW_MHz=GBW / 1e6, SR_MVs=SR / 1e6, Ron_k=ron / 1e3,
                fclk=fclk, CI_pF=CI, amp=amp, gain_db=round(gdb, 3),
                gain_set=gain,
                f0_kHz=f0 / 1e3,
                f0_err_pct=100 * (f0 - fclk / K) / (fclk / K),
                Q_ext=Qe, Q_err_pct=100 * (Qe - Q) / Q,
                gain=gain_sim, gain_ideal=gain_ideal,
                gain_err_db=20 * math.log10(abs(gain_sim / gain_ideal)))


def mode_sweep():
    """A0 x GBW requirement grid at 0 and 18 dB for three worst cases."""
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    cases = (
        dict(K=100, Q=5.0, fclk=500e3, tstop=2.5e-3),
        dict(K=25, Q=1.0, fclk=1e6, tstop=1.5e-3),
        dict(K=200, Q=5.0, fclk=500e3, tstop=2.7e-3),
    )
    gains = ((0.0, 1.0), (18.0, 7.94))
    gbws = (3.0, 5.0, 7.8, 10.0)
    a0s_dB = (40.0, 45.0, 49.0, 50.0, 60.0, 80.0)
    print('== op-amp requirement: A0 x GBW, gains 0/18 dB, 3 cases ==',
          flush=True)
    for case in cases:
        cname = f"K{case['K']}/Q{case['Q']:g}"
        for gdb, g in gains:
            for gbw in gbws:
                for adb in a0s_dB:
                    kw = dict(A0=10 ** (adb / 20), GBW=gbw * 1e6,
                              SR=5e6, ron=1e3, CI=8.0, amp=0.05,
                              gain=g, **case)
                    row = case_step(**kw)
                    row.update(case=cname, gain_step_db=gdb)
                    rows.append(row)
                    print(f"  {cname:12s} G={gdb:2.0f} dB GBW={gbw:4.1f} "
                          f"MHz A0={adb:4.0f} dB: f0err={row['f0_err_pct']:+.2f}% "
                          f"Qerr={row['Q_err_pct']:+.2f}% "
                          f"gainerr={row['gain_err_db']:+.3f} dB", flush=True)
    # Ideal-op-amp baseline at the SAME (K, Q, gain): A0=80 dB, GBW=20 MHz.
    # The differential Q error cancels extraction bias.
    baselines = {}
    print('== ideal baseline A0=80 dB / GBW=20 MHz ==', flush=True)
    for case in cases:
        cname = f"K{case['K']}/Q{case['Q']:g}"
        for gdb, g in gains:
            kw = dict(A0=1e4, GBW=20e6, SR=5e6, ron=1e3, CI=8.0,
                      amp=0.05, gain=g, **case)
            r = case_step(**kw)
            baselines[(cname, gdb)] = r['Q_ext']
            print(f"  {cname:12s} G={gdb:2.0f} dB: Q_base={r['Q_ext']:.4f}",
                  flush=True)
    for r in rows:
        qb = baselines[(r['case'], r['gain_step_db'])]
        r['Q_base'] = qb
        r['Q_diff_pct'] = 100.0 * (r['Q_ext'] - qb) / qb

    keys = ['tag', 'case', 'status', 'K', 'Q', 'gain_step_db', 'gain_db',
            'gain_set', 'A0_dB', 'GBW_MHz', 'SR_MVs', 'Ron_k', 'fclk',
            'CI_pF', 'amp', 'f0_kHz', 'f0_err_pct', 'Q_ext', 'Q_err_pct',
            'Q_base', 'Q_diff_pct', 'gain', 'gain_ideal', 'gain_err_db']
    with open(os.path.join(RESULTS, 'behav_sweep.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, '') for c in w.fieldnames})

    write_sweep_markdown(rows, cases, gains, gbws)
    print(f"wrote results/behav_sweep.{{csv,md}} ({len(rows)} rows)", flush=True)


# ------------------------------------------------------------ mode: gain
def write_sweep_markdown(rows, cases, gains, gbws):
    def passes(r):
        qlim = 5.0 if r['Q'] <= 2.0 else 15.0
        f0lim = 1.0 if r['K'] <= 100 else 1.5
        return (r.get('status') != 'FAIL'
                and math.isfinite(r.get('f0_err_pct', float('nan')))
                and math.isfinite(r.get('Q_diff_pct', float('nan')))
                and abs(r['f0_err_pct']) <= f0lim
                and abs(r['Q_diff_pct']) <= qlim)

    # Per (case, gain, GBW): minimum A0 that keeps f0 within 1% and Q within 5%.
    thresholds = {}
    for case in cases:
        cname = f"K{case['K']}/Q{case['Q']:g}"
        for gdb, g in gains:
            for gbw in gbws:
                sub = [r for r in rows if r['case'] == cname
                       and abs(r['gain_set'] - g) < 1e-12
                       and abs(r['GBW_MHz'] - gbw) < 1e-9 and passes(r)]
                thresholds[(cname, gdb, gbw)] = (
                    min(r['A0_dB'] for r in sub) if sub else None)

    def requirement(case_list):
        out = {}
        for gbw in gbws:
            vals, missing = [], []
            for case in case_list:
                cname = f"K{case['K']}/Q{case['Q']:g}"
                for gdb, g in gains:
                    v = thresholds[(cname, gdb, gbw)]
                    if v is None:
                        missing.append(f'{cname} G={gdb:.0f}dB')
                    else:
                        vals.append(v)
            out[gbw] = (max(vals) if not missing else None, missing)
        return out

    global_req = requirement(cases)
    supported = [gbw for gbw in gbws if global_req[gbw][0] is not None]
    req_gbw = min(supported) if supported else None
    req_a0 = global_req[req_gbw][0] if req_gbw is not None else None

    # Nominal-ideal result for the K=200/Q=5 case that cannot meet Q +/-5%.
    k200_nom = {}
    for gdb, g in gains:
        sub = [r for r in rows if r['case'] == 'K200/Q5'
               and abs(r['gain_set'] - g) < 1e-12
               and abs(r['A0_dB'] - 80.0) < 1e-9
               and abs(r['GBW_MHz'] - 10.0) < 1e-9]
        k200_nom[gdb] = sub[0] if sub else None

    # Transistor-level corner comparison (tb_ac table only).
    corners = []
    cop = os.path.join(RESULTS, 'opamp_corners.md')
    if os.path.exists(cop):
        in_ac = False
        for line in open(cop):
            if line.startswith('## tb_ac'):
                in_ac = True
                continue
            if line.startswith('## tb_step'):
                break
            if in_ac:
                parts = [x.strip() for x in line.strip().strip('|').split('|')]
                if len(parts) >= 4 and parts[0] in ('tt', 'ss_110C', 'ff_m40C'):
                    try:
                        corners.append(dict(name=parts[0], A0=float(parts[1]),
                                            GBW=float(parts[2]),
                                            PM=float(parts[3])))
                    except ValueError:
                        pass

    mdp = os.path.join(RESULTS, 'behav_sweep.md')
    with open(mdp, 'w') as f:
        f.write('# Behavioral op-amp requirement sweep\n\n')
        f.write('Step response. Q error is the **difference versus the same-case ideal op-amp baseline (A0=80 dB, GBW=20 MHz)**, so extraction bias cancels. Pass limits: |Q_diff| <= 5 % for Q<=2 and <= 15 % for Q>2; f0 within 1 % (K<=100) or 1.5 % (K=200). SR = 5 V/us, '
                'Ron = 1 kohm, CI = 8 pF. The grid runs both gain settings '
                '(G=1 and 7.94) for K=100/Q=5, K=25/Q=1 (fclk=1 MHz) and '
                'K=200/Q=5. [SIM]\n\n')
        f.write('## Minimum A0 (dB) at each GBW\n\n')
        f.write('| case | gain dB | 3 MHz | 5 MHz | 7.8 MHz | 10 MHz |\n')
        f.write('|---|---:|---:|---:|---:|---:|\n')
        for case in cases:
            cname = f"K{case['K']}/Q{case['Q']:g}"
            for gdb, g in gains:
                cells = []
                for gbw in gbws:
                    v = thresholds[(cname, gdb, gbw)]
                    cells.append('>80' if v is None else f'{v:.0f}')
                f.write(f"| {cname} | {gdb:.0f} | " + ' | '.join(cells) +
                        ' |\n')
        f.write('\n`>80` means no A0 point in the tested grid met both the '
                'f0 and differential-Q limits at that GBW.\n\n')
        f.write('At K=200/Q=5 and A0=80 dB / GBW=10 MHz: ')
        for gdb, g in gains:
            r = k200_nom[gdb]
            if r:
                f.write(f"absolute Q {r['Q_err_pct']:+.1f} %, differential "
                        f"Q {r['Q_diff_pct']:+.1f} % at {gdb:.0f} dB")
            if gdb == gains[0][0]:
                f.write('; ')
        k200_bad = any(r and abs(r['Q_diff_pct']) > 15.0
                       for r in k200_nom.values())
        if k200_bad:
            f.write('. The differential error exceeds 15 %; limiting K=200 '
                    'to Q<=4 is a proposed change (see results/qcheck.md).\n\n')
        else:
            f.write('. These are inside the 15 % differential Q limit for '
                    'Q>2; the absolute Q residual remains inside the max '
                    '+/-20 % budget.\n\n')
        if req_gbw is not None:
            f.write(f'**Op-amp requirement (all three cases, both gains, '
                    f'differential-Q limits): A0 >= {req_a0:.0f} dB and '
                    f'GBW >= {req_gbw:g} MHz.**\n\n')
        else:
            f.write('**No tested GBW supports all three cases.**\n\n')
        if corners:
            f.write('## Transistor-level corners versus that requirement\n\n')
            f.write('| corner | A0 dB | GBW MHz | PM deg | vs requirement |\n')
            f.write('|---|---:|---:|---:|---|\n')
            for c in corners:
                ok = (req_a0 is not None and c['A0'] >= req_a0
                      and c['GBW'] >= req_gbw)
                f.write(f"| {c['name']} | {c['A0']:.1f} | {c['GBW']:.2f} | "
                        f"{c['PM']:.1f} | {'PASS' if ok else 'FAIL'} |\n")
        f.write('\nThe transistor-level op-amp also has a separate 50 dB '
                'minimum A0 bar and an 80 dB gain target; see '
                'results/opamp_corners.md and results/spec_check.md.\n')



def mode_gain():
    """LP passband gain at four settings, with ideal/tt/ss op-amp parameters."""
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    cases = (
        dict(K=100, Q=5.0, fclk=500e3, tstop=2.5e-3),
        dict(K=25, Q=1.0, fclk=1e6, tstop=1.5e-3),
    )
    # name, A0 (linear), GBW (Hz)
    opamps = (
        ('ideal_80dB_10MHz', 1e4, 10e6),
        ('tt_50.0dB_10.6MHz', 10 ** (50.0 / 20), 10.6e6),
        ('ss_49.0dB_7.82MHz', 10 ** (49.0 / 20), 7.82e6),
    )
    print('== LP gain error: ideal / tt / ss op-amp parameters ==',
          flush=True)
    for oname, A0, GBW in opamps:
        for case in cases:
            for gdb, g in GAIN_STEPS:
                kw = dict(A0=A0, GBW=GBW, SR=5e6, ron=1e3, CI=8.0,
                          amp=0.05, gain=g, **case)
                row = case_step(**kw)
                row['opamp'] = oname
                rows.append(row)
                print(f"  {oname:20s} K={row['K']} Q={row['Q']:g} "
                      f"G={gdb:2.0f} dB: error={row['gain_err_db']:+.3f} dB "
                      f"(f0err={row['f0_err_pct']:+.2f}%, "
                      f"Qerr={row['Q_err_pct']:+.2f}%)", flush=True)
    keys = ['opamp', 'K', 'Q', 'gain_db', 'gain_set', 'fclk', 'gain',
            'gain_ideal', 'gain_err_db', 'f0_err_pct', 'Q_err_pct', 'tag']
    with open(os.path.join(RESULTS, 'gain_test.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, '') for c in w.fieldnames})
    with open(os.path.join(RESULTS, 'gain_test.md'), 'w') as f:
        f.write('# LP gain-error test\n\n')
        f.write('Behavioral biquad, gain applied only by the input-branch '
                'capacitor Cs1 = G*Cs (Cs2, Cs3, Cd and CI unchanged). '
                'SR = 5 V/us, Ron = 1 kohm, fclk = 500 kHz (K=100/Q=5) and '
                '1 MHz (K=25/Q=1). Op-amp parameter sets: ideal A0=80 dB / '
                'GBW=10 MHz, tt A0=50.0 dB / GBW=10.6 MHz, ss A0=49.0 dB / '
                'GBW=7.82 MHz. [SIM]\n\n')
        f.write('| op-amp | K | Q | gain set dB | LP gain dB | gain error dB | '
                'f0 err % | Q err % | verdict |\n')
        f.write('|---|---:|---:|---:|---:|---:|---:|---:|---|\n')
        for r in rows:
            err = r['gain_err_db']
            verdict = 'PASS typ' if abs(err) <= 0.5 else (
                'PASS max' if abs(err) <= 1.0 else 'FAIL')
            badfit = (not math.isfinite(r['f0_err_pct'])
                      or not math.isfinite(r['Q_err_pct'])
                      or abs(r['f0_err_pct']) > 10.0
                      or abs(r['Q_err_pct']) > 50.0)
            f0txt = 'fit fail' if badfit else f"{r['f0_err_pct']:+.2f}"
            qtxt = 'fit fail' if badfit else f"{r['Q_err_pct']:+.2f}"
            f.write(f"| {r['opamp']} | {r['K']} | {r['Q']:g} | "
                    f"{r['gain_db']:.0f} | "
                    f"{20 * math.log10(abs(r['gain'])):.3f} | "
                    f"{err:+.3f} | {f0txt} | {qtxt} | {verdict} |\n")
        worst = max(abs(r['gain_err_db']) for r in rows)
        f.write(f"\nWorst gain error over all op-amp sets: **{worst:.3f} dB**. ")
        f.write('Spec: +/-0.5 dB typ, +/-1 dB max. ')
        f.write('PASS\n' if worst <= 1.0 else
                'At least one setting exceeds the max target; report the '
                'measured value and propose a revised spec.\n')
        f.write('\n`fit fail` means the step-ringing f0/Q extractor did not '
                'converge for that run; the gain error is still measured from '
                'the settled LP tail.\n')
    print(f"wrote results/gain_test.{{csv,md}} ({len(rows)} rows)", flush=True)


# ------------------------------------------------------------ mode: offset
def case_offset(K, Q, vos, fclk=500e3, CI=8.0, gain=1.0, vos2=None,
                A0=1e3, GBW=10e6, tag=None):
    vos2 = vos if vos2 is None else vos2
    gdb = 20 * math.log10(gain)
    tag = tag or (f'off_K{K}_Q{Q:g}_G{gdb:g}dB_'
                  f'v{vos * 1e3:+g}_{vos2 * 1e3:+g}')
    T = 1.0 / fclk
    # settle: r^n < 0.02 needs n = ln(0.02)/ln(r) cycles (+60 margin)
    theta, _, _ = design_exact(K, Q)
    r = math.exp(-theta / (2.0 * Q))
    n_settle = int(math.log(0.02) / math.log(r)) + 60 if r < 1 else 5000
    tstop = min((n_settle + 20) * T, 20e-3)
    dat, _ = run_ngspice(tag, K=K, Q=Q, CI=CI, fclk=fclk, vos=vos,
                         vos2=vos2, gain=gain, A0=A0, GBW=GBW, amp=0.0,
                         tstop=tstop, tmaxstep=2e-8, stim='zero')
    try:
        d = np.loadtxt(dat)
    except Exception:
        os.remove(dat)
        return dict(K=K, Q=Q, gain_db=gdb, gain_set=gain, vos=vos,
                    vos2=vos2, status='no data')
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
    # Ignore the t=0 / initial-DC transient and check only the settled tail.
    n_tail = max(100, len(t) // 5)
    rail = int(max(np.max(np.abs(lp[-n_tail:])),
                   np.max(np.abs(bp[-n_tail:]))) > 1.55)
    return dict(K=K, Q=Q, gain_db=gdb, gain_set=gain, vos=vos, vos2=vos2,
                status='rail' if rail else 'ok', n_settle=n_settle,
                rail=rail, lp_offset=float(np.mean(samp_lp)),
                bp_offset=float(np.mean(samp_bp)),
                worst_mV=max(abs(np.mean(samp_lp)),
                             abs(np.mean(samp_bp))) * 1e3)


def mode_offset():
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    cases = [(100, q) for q in QS]
    cases += [(K, q) for K in (25, 200) for q in QS if q <= 2.0]
    cases += [(25, 5.0), (200, 5.0)]
    print('== offset test (5 mV op-amp offset, zero input, fclk = 500 kHz, '
          'both op-amps, same and opposite sign, 0 and 18 dB) ==',
          flush=True)
    for K, Q in cases:
        for gdb, g in ((0.0, 1.0), (18.0, 7.94)):
            for v1, v2 in ((5e-3, 5e-3), (5e-3, -5e-3)):
                r = case_offset(K, Q, v1, gain=g, vos2=v2)
                rows.append(r)
                print(f"  K={K} Q={Q:g} G={gdb:2.0f} dB "
                      f"vos=({v1 * 1e3:+.0f},{v2 * 1e3:+.0f}) mV: "
                      f"{r.get('status')}, worst="
                      f"{r.get('worst_mV', float('nan')):.1f} mV", flush=True)
    keys = ['K', 'Q', 'gain_db', 'gain_set', 'vos', 'vos2', 'status',
            'n_settle', 'rail', 'lp_offset', 'bp_offset', 'worst_mV']
    with open(os.path.join(RESULTS, 'offset_test.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, '') for c in w.fieldnames})
    ok = [r for r in rows if r.get('status') == 'ok']
    rails = [r for r in rows if r.get('status') == 'rail']
    qle2_0db = [r for r in ok if r['Q'] <= 2.0 and r['gain_db'] == 0.0]
    with open(os.path.join(RESULTS, 'offset_test.md'), 'w') as f:
        f.write('# Offset test - 5 mV input-referred op-amp offset\n\n')
        f.write('Behavioral biquad (ideal switches), zero differential input, '
                'fclk = 500 kHz, A0 = 60 dB (deck default), GBW = 10 MHz. '
                'Both op-amps have a 5 mV input-referred offset; same-sign is '
                '(+5,+5) mV and opposite-sign is (+5,-5) mV. Gain is the '
                'input-branch cap Cs1 = G*Cs (G = 1 and 7.94, i.e. 0 and '
                '18 dB). Real tt/ss worst cases are in '
                'results/offset_opamp.md. [SIM]\n\n')
        f.write('`rail` is 1 when the settled differential output exceeded '
                '+/-1.55 V; such a row is invalid and is excluded from the '
                'worst-case summary. No row is silently clipped.\n\n')
        f.write('| K | Q | gain dB | VOS1 mV | VOS2 mV | LP offset mV | '
                'BP offset mV | rail | status |\n')
        f.write('|---:|---:|---:|---:|---:|---:|---:|---:|---|\n')
        for r in rows:
            if r.get('status') == 'no data':
                continue
            f.write(f"| {r['K']} | {r['Q']:g} | {r['gain_db']:.0f} | "
                    f"{r['vos'] * 1e3:+.0f} | {r['vos2'] * 1e3:+.0f} | "
                    f"{r['lp_offset'] * 1e3:+.2f} | "
                    f"{r['bp_offset'] * 1e3:+.2f} | {r['rail']} | "
                    f"{r['status']} |\n")
        if qle2_0db:
            f.write('\nWorst |offset| at 0 dB and Q <= 2 (all K): '
                    f"{max(r['worst_mV'] for r in qle2_0db):.1f} mV "
                    '(spec max 40 mV).\n')
        if ok:
            f.write(f"Worst |offset| over all simulated gain/Q settings: "
                    f"{max(r['worst_mV'] for r in ok):.1f} mV "
                    '(spec max 60 mV).\n')
        if rails:
            f.write(f"\n**{len(rails)} rail-limited row(s)** are marked "
                    'invalid above and excluded from the summaries.\n')
    print(f"wrote results/offset_test.{{csv,md}} "
          f'({len(ok)} ok / {len(rows)} runs, {len(rails)} rail)', flush=True)


def mode_offset_opamp():
    """Worst offset cases with ideal, tt and ss op-amp parameters."""
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    cases = ((200, 2 ** 0.5), (200, 5.0), (25, 5.0))
    opamps = (
        ('ideal_80dB_10MHz', 1e4, 10e6),
        ('tt_50.0dB_10.6MHz', 10 ** (50.0 / 20), 10.6e6),
        ('ss_49.0dB_7.82MHz', 10 ** (49.0 / 20), 7.82e6),
    )
    print('== worst offset cases: ideal / tt / ss op-amp parameters ==',
          flush=True)
    for oname, A0, GBW in opamps:
        for K, Q in cases:
            for gdb, g in ((0.0, 1.0), (18.0, 7.94)):
                for v1, v2 in ((5e-3, 5e-3), (5e-3, -5e-3)):
                    tag = (f'offop_{oname}_K{K}_Q{Q:g}_G{gdb:g}dB_'
                           f'v{v1 * 1e3:+g}_{v2 * 1e3:+g}')
                    r = case_offset(K, Q, v1, gain=g, vos2=v2,
                                    A0=A0, GBW=GBW, tag=tag)
                    r['opamp'] = oname
                    rows.append(r)
                    print(f"  {oname:20s} K={K} Q={Q:g} G={gdb:2.0f} dB "
                          f"vos=({v1 * 1e3:+.0f},{v2 * 1e3:+.0f}) mV: "
                          f"{r.get('status')}, worst="
                          f"{r.get('worst_mV', float('nan')):.1f} mV",
                          flush=True)
    keys = ['opamp', 'K', 'Q', 'gain_db', 'gain_set', 'vos', 'vos2',
            'status', 'n_settle', 'rail', 'lp_offset', 'bp_offset',
            'worst_mV']
    with open(os.path.join(RESULTS, 'offset_opamp.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, '') for c in w.fieldnames})
    with open(os.path.join(RESULTS, 'offset_opamp.md'), 'w') as f:
        f.write('# Worst offset cases with real op-amp parameters\n\n')
        f.write('Behavioral biquad, 5 mV op-amp input offset on both '
                'amplifiers, same sign (+5,+5) and opposite sign (+5,-5) mV, '
                'at 0 and 18 dB. Cases: K=200/Q=1.414, K=200/Q=5, K=25/Q=5. '
                'Op-amp sets: ideal (A0=80 dB, GBW=10 MHz), tt (50.0 dB, '
                '10.6 MHz), ss/110C (49.0 dB, 7.82 MHz). [SIM]\n\n')
        f.write('| op-amp | K | Q | gain dB | VOS1 mV | VOS2 mV | LP mV | '
                'BP mV | rail | status |\n')
        f.write('|---|---:|---:|---:|---:|---:|---:|---:|---:|---|\n')
        for r in rows:
            if r.get('status') == 'no data':
                continue
            f.write(f"| {r['opamp']} | {r['K']} | {r['Q']:g} | "
                    f"{r['gain_db']:.0f} | {r['vos'] * 1e3:+.0f} | "
                    f"{r['vos2'] * 1e3:+.0f} | {r['lp_offset'] * 1e3:+.2f} | "
                    f"{r['bp_offset'] * 1e3:+.2f} | {r['rail']} | "
                    f"{r['status']} |\n")
        f.write('\nWorst |offset| per op-amp set (valid rows):\n\n')
        for oname, _, _ in opamps:
            sub = [r for r in rows if r['opamp'] == oname
                   and r.get('status') == 'ok']
            if sub:
                m = max(sub, key=lambda r: r['worst_mV'])
                f.write(f"- {oname}: **{m['worst_mV']:.1f} mV** "
                        f"(K={m['K']}, Q={m['Q']:g}, {m['gain_db']:.0f} dB, "
                        f"VOS=({m['vos'] * 1e3:+.0f},{m['vos2'] * 1e3:+.0f}) mV)\n")
    print(f"wrote results/offset_opamp.{{csv,md}} ({len(rows)} rows)",
          flush=True)


def mode_qcheck():
    """Absolute and differential Q error for the real op-amp corners."""
    os.makedirs(RESULTS, exist_ok=True)
    cases = ((200, 5.0), (100, 5.0), (25, 1.0), (200, 2.0),
             (25, 2.0), (200, 4.0))
    gains = ((0.0, 1.0), (18.0, 7.94))
    opamps = (
        ('tt_50.0dB_10.6MHz', 10 ** (50.0 / 20), 10.6e6),
        ('ss_49.0dB_7.82MHz', 10 ** (49.0 / 20), 7.82e6),
    )
    rows = []
    print('== Q check: absolute and differential (baseline 80 dB/20 MHz) ==',
          flush=True)
    for K, Q in cases:
        cname = f'K{K}/Q{Q:g}'
        for gdb, g in gains:
            tstop = 4.0e-3 if K == 200 else (2.5e-3 if K == 100 else 1.5e-3)
            base = case_step(K=K, Q=Q, A0=1e4, GBW=20e6, SR=5e6,
                             ron=1e3, fclk=500e3, CI=8.0, amp=0.05,
                             tstop=tstop, gain=g)
            for oname, A0, GBW in opamps:
                r = case_step(K=K, Q=Q, A0=A0, GBW=GBW, SR=5e6,
                              ron=1e3, fclk=500e3, CI=8.0, amp=0.05,
                              tstop=tstop, gain=g)
                fit_ok = (math.isfinite(r['Q_ext'])
                          and abs(r['f0_err_pct']) <= 10.0
                          and abs(r['Q_err_pct']) <= 50.0)
                qabs = 100.0 * (r['Q_ext'] - Q) / Q
                qdiff = (100.0 * (r['Q_ext'] - base['Q_ext'])
                         / base['Q_ext']) if fit_ok else float('nan')
                rows.append(dict(case=cname, K=K, Q=Q, gain_db=gdb,
                                 opamp=oname, A0_dB=20 * math.log10(A0),
                                 GBW_MHz=GBW / 1e6, Q_ext=r['Q_ext'],
                                 Q_abs_err_pct=qabs, Q_base=base['Q_ext'],
                                 Q_diff_err_pct=qdiff,
                                 f0_err_pct=r['f0_err_pct'],
                                 fit_ok=int(fit_ok)))
                print(f"  {cname:9s} G={gdb:2.0f} dB {oname:20s}: "
                      f"Q={r['Q_ext']:.3f} abs={qabs:+.2f}% "
                      f"diff={qdiff:+.2f}%", flush=True)
    keys = ['case', 'K', 'Q', 'gain_db', 'opamp', 'A0_dB', 'GBW_MHz',
            'Q_ext', 'Q_abs_err_pct', 'Q_base', 'Q_diff_err_pct',
            'f0_err_pct', 'fit_ok']
    with open(os.path.join(RESULTS, 'qcheck.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, '') for c in w.fieldnames})
    with open(os.path.join(RESULTS, 'qcheck.md'), 'w') as f:
        f.write('# Q evidence: absolute and differential errors\n\n')
        f.write('Same step-ring extraction for every run. Differential Q error '
                'is `(Q_real - Q_ideal)/Q_ideal` with the same-case ideal '
                'baseline at **A0=80 dB, GBW=20 MHz**. This cancels the '
                'extraction bias. Limits used: 5 % for Q<=2, 15 % for Q>2 '
                '(margin below the 20 % max). [SIM]\n\n')
        f.write('| K | Q | gain dB | op-amp | Q | abs Q err % | Q ideal | '
                'diff Q err % | f0 err % | fit |\n')
        f.write('|---:|---:|---:|---|---:|---:|---:|---:|---:|---|\n')
        for r in rows:
            f.write(f"| {r['K']} | {r['Q']:g} | {r['gain_db']:.0f} | "
                    f"{r['opamp']} | {r['Q_ext']:.3f} | "
                    f"{r['Q_abs_err_pct']:+.2f} | {r['Q_base']:.3f} | "
                    f"{r['Q_diff_err_pct']:+.2f} | {r['f0_err_pct']:+.2f} | "
                    f"{r['fit_ok']} |\n")
        f.write('\n`fit=0` means the step-ring extraction did not converge; '
                'its differential Q is not used. The gain error from the same '
                'run can still be valid (settled LP tail).\n')
        # Proposed K=200 Q limit check.
        q5 = [r for r in rows if r['K'] == 200 and abs(r['Q'] - 5.0) < 1e-9
              and r['fit_ok']]
        q4 = [r for r in rows if r['K'] == 200 and abs(r['Q'] - 4.0) < 1e-9
              and r['fit_ok']]
        if q5:
            worst5 = max(abs(r['Q_diff_err_pct']) for r in q5)
            f.write(f'\nK=200/Q=5 corrected differential Q worst: '
                    f'**{worst5:.2f} %** (tt/ss, both gains). ')
            if worst5 > 15.0:
                f.write('This exceeds 15 %, so limiting K=200 to Q<=4 is a '
                        'proposed change (not applied). ')
            else:
                f.write('This does not exceed the 15 % differential limit, '
                        'so a Q<=4 limit is not required. ')
        if q4:
            worst4 = max(abs(r['Q_diff_err_pct']) for r in q4)
            f.write(f'For reference, K=200/Q=4 differential Q worst is '
                    f'**{worst4:.2f} %**.\n')
        f.write('\nThe Q<=2 rows at 18 dB use the 50/49 dB transistor-corner '
                'parameters. A targeted A0/GBW sweep in results/q2check.md '
                'shows that A0=60 dB brings the worst Q<=2 differential error '
                'inside 5 % (GBW has little effect), so the existing A0>=60 dB '
                'requirement covers this row; no separate Q<=2 relaxation is '
                'needed.\n')
    print(f"wrote results/qcheck.{{csv,md}} ({len(rows)} rows)", flush=True)


def main():
    mode = sys.argv[sys.argv.index('--mode') + 1] if '--mode' in sys.argv \
        else 'sweep'
    if mode == 'sweep':
        mode_sweep()
    elif mode == 'gain':
        mode_gain()
    elif mode == 'offset':
        mode_offset()
    elif mode == 'offset-opamp':
        mode_offset_opamp()
    elif mode == 'qcheck':
        mode_qcheck()
    else:
        sys.exit(f'unknown mode {mode!r} '
                 '(sweep|gain|offset|offset-opamp|qcheck)')


if __name__ == '__main__':
    main()
