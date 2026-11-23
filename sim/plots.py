#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Regenerate the committed result figures and their Markdown snapshot.

The committed PNGs in results/plots/ were originally produced ad hoc.  This
script makes them reproducible:

  - cap budget / f0 / Q figures use the exact z-domain table written by
    sim/capbudget.py (regenerated automatically if the CSV is missing);
  - the step-response figure runs the PDK-free behavioral deck;
  - the offset figure uses results/data/offset_test.csv from
    `run_sweep.py --mode offset` (skipped with a warning if absent);
  - the op-amp schematic is drawn from the committed netlist (no PDK);
  - the op-amp Bode figure runs the Sky130 AC testbench at the three review
    corners when the PDK is available (skipped otherwise).

Run:  python3 sim/plots.py [--skip-opamp]
Out:  results/plots/*.png, results/plots/README.md
"""
import argparse
import csv
import math
import os
import subprocess
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Polygon  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..'))
RESULTS = os.path.join(REPO, 'results')
PLOTS = os.path.join(RESULTS, 'plots')
DATA = os.path.join(RESULTS, 'data')
CAP_CSV = os.path.join(DATA, 'capbudget_table.csv')
OFFSET_CSV = os.path.join(DATA, 'offset_test.csv')
BEHAV = os.path.join(HERE, 'behavioral')
OPAMP = os.path.join(REPO, 'design', 'opamp')

sys.path.insert(0, HERE)
sys.path.insert(0, BEHAV)

KS = (25, 50, 100, 200)
COLORS = {25: '#1f77b4', 50: '#ff7f0e', 100: '#2ca02c',
          200: '#d62728'}
Q_LABELS = ('0.5', '0.71', '1', '1.41', '2', '2.83', '4', '5')


def load_cap_rows():
    """Read the cap table, generating it with sim/capbudget.py if needed."""
    if not os.path.exists(CAP_CSV):
        print('capbudget_table.csv missing; running sim/capbudget.py',
              flush=True)
        subprocess.run([sys.executable, os.path.join(HERE, 'capbudget.py')],
                       check=True)
    rows = []
    with open(CAP_CSV) as f:
        for r in csv.DictReader(f):
            if r.get('error'):
                continue
            rows.append(dict(
                K=int(r['K']), Q=float(r['Q']),
                f0_err=float(r['f0_quant_err_pct']),
                Q_err=float(r['Q_quant_err_pct']),
                total0=float(r['total_cap_pF']),
                total18=float(r['total_cap_pF_18dB']),
                area18=float(r['total_area_mm2_18dB']),
            ))
    return rows


def by_k(rows):
    out = {K: [] for K in KS}
    for r in rows:
        out[r['K']].append(r)
    for K in out:
        out[K].sort(key=lambda r: r['Q'])
    return out


def plot_capbudget(rows):
    grouped = by_k(rows)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
    for ax, key, ylab, spec, title in (
            (axes[0], 'total0', 'total cap (pF)', 120.0,
             '0 dB (G = 1)'),
            (axes[1], 'total18', 'total cap (pF)', 120.0,
             '18 dB (G = 7.94)'),
            (axes[2], 'area18', 'MiM area (mm$^2$)', 0.12,
             '18 dB MiM area')):
        for K in KS:
            q = [r['Q'] for r in grouped[K]]
            y = [r[key] for r in grouped[K]]
            ax.plot(q, y, 'o-', color=COLORS[K], label=f'K={K}')
        ax.axhline(spec, color='0.25', ls='--', lw=1.2)
        ax.set_xlabel('Q')
        ax.set_ylabel(ylab)
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        if key == 'area18':
            ax.set_ylim(0.0, 0.14)
        else:
            ax.set_ylim(0.0, 130.0)
    axes[0].legend(fontsize=8, ncol=2)
    max0 = max(r['total0'] for r in rows)
    max18 = max(r['total18'] for r in rows)
    maxa = max(r['area18'] for r in rows)
    fig.suptitle('Cap budget: %.1f pF max at 0 dB, %.1f pF max at 18 dB; '
                 'MiM area %.4f mm$^2$ (MiM only)' % (max0, max18, maxa))
    fig.tight_layout()
    path = os.path.join(PLOTS, 'fig_capbudget.png')
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path, dict(max0=max0, max18=max18, maxa=maxa)


def plot_f0_vs_fclk():
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    fclk = np.logspace(4, 6, 200)
    for K in KS:
        fmax = 500e3 if K == 25 else 1e6
        m = fclk <= fmax
        ax.loglog(fclk[m], fclk[m] / K, color=COLORS[K], label=f'K = {K}')
    ax.set_xlabel('fclk (Hz)')
    ax.set_ylabel('f0 = fclk/K (Hz)')
    ax.set_title('Clock-programmable f0 (fclk 10 kHz-1 MHz; '
                 'K=25 limited to 500 kHz)')
    ax.grid(True, which='both', alpha=0.3)
    ax.legend()
    fig.tight_layout()
    path = os.path.join(PLOTS, 'fig_f0_vs_fclk.png')
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path, {}


def plot_q_vs_setting(rows):
    grouped = by_k(rows)
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(11, 4.4))
    for K in KS:
        q = [r['Q'] for r in grouped[K]]
        ax0.plot(q, [r['f0_err'] for r in grouped[K]], 'o-',
                 color=COLORS[K], label=f'K={K}')
        ax1.plot(q, [r['Q_err'] for r in grouped[K]], 'o-',
                 color=COLORS[K], label=f'K={K}')
    ax0.axhline(1.0, color='tab:red', ls='--', lw=1.0)
    ax0.axhline(-1.0, color='tab:red', ls='--', lw=1.0)
    ax0.axhline(1.5, color='tab:orange', ls=':', lw=1.2)
    ax0.axhline(-1.5, color='tab:orange', ls=':', lw=1.2)
    ax0.text(0.55, 1.08, 'typ +/-1 % (K<=100)', color='tab:red', fontsize=8)
    ax0.text(0.55, 1.58, 'typ +/-1.5 % (K=200)', color='tab:orange',
             fontsize=8)
    ax0.set_xlabel('Q setting')
    ax0.set_ylabel('f0 quantization error (%)')
    ax0.set_title('f0 quantization error (CI=8 pF, 25 fF unit + trim)')
    ax0.grid(True, alpha=0.3)
    ax0.legend(fontsize=7, loc='lower left', ncol=2, framealpha=0.9)
    ax1.axhline(5.0, color='tab:red', ls='--', lw=1.0)
    ax1.axhline(-5.0, color='tab:red', ls='--', lw=1.0)
    ax1.text(0.55, 5.3, 'typ +/-5 %', color='tab:red', fontsize=8)
    ax1.set_xlabel('Q setting')
    ax1.set_ylabel('Q quantization error (%)')
    ax1.set_title('Q quantization error')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=8)
    fig.tight_layout()
    path = os.path.join(PLOTS, 'fig_q_vs_setting.png')
    fig.savefig(path, dpi=110)
    plt.close(fig)
    worst_f0 = max(rows, key=lambda r: abs(r['f0_err']))
    worst_q = max(rows, key=lambda r: abs(r['Q_err']))
    return path, dict(f0=worst_f0, q=worst_q)


def _run_step(K, Q, tstop, tag):
    import run_sweep as rs
    dat = os.path.join(BEHAV, f'{tag}.dat')
    rs.run_ngspice(tag, K=K, Q=Q, CI=8.0, fclk=500e3, ron=1e3, A0=1e4,
                   GBW=20e6, SR=5e6, amp=0.05, tstep=100e-6, tstop=tstop,
                   stim='step', gain=1.0)
    d = rs.load_wrdata(dat)
    os.remove(dat)
    s = rs.sample_per_period(d, 1.0 / 500e3)
    kstep = round(100e-6 * 500e3)
    vin = np.zeros(len(s['k']))
    vin[s['k'] >= kstep] = 0.05
    bm, lm = rs.model_response(K, Q, vin, gain=1.0)
    return s, bm, lm


def plot_step_response():
    settings = ((50.0, 1.0, 1.5e-3), (25.0, 0.5, 1.5e-3),
                (200.0, 5.0, 4.0e-3))
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))
    worst = 0.0
    for ax, (K, Q, tstop) in zip(axes, settings):
        tag = f'plot_step_K{K:g}_Q{Q:g}'.replace('.', 'p')
        s, bm, lm = _run_step(K, Q, tstop, tag)
        err_b = np.max(np.abs(s['b'] - bm)) / np.max(np.abs(bm))
        err_l = np.max(np.abs(s['l'] - lm)) / np.max(np.abs(lm))
        worst = max(worst, err_b, err_l)
        t_us = s['t'] * 1e6
        ax.plot(t_us, s['v'] * 1e3, color='0.75', lw=1.0, label='input')
        ax.plot(t_us, s['b'] * 1e3, 'b.', ms=2.5, label='BP [SIM]')
        ax.plot(t_us, bm * 1e3, 'k-', lw=1.0, label='BP analytical')
        ax.plot(t_us, s['l'] * 1e3, 'r.', ms=2.5, label='LP [SIM]')
        ax.plot(t_us, lm * 1e3, 'g-', lw=1.0, label='LP analytical')
        ax.set_title(f'K={K:g}, Q={Q:g}, f0={500e3 / K / 1e3:g} kHz')
        ax.set_xlabel('time (us)')
        ax.set_ylabel('differential output (mV)')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7, loc='upper center',
                  bbox_to_anchor=(0.5, -0.18), ncol=3, frameon=False)
    fig.suptitle('Behavioral SC biquad vs exact discrete map: '
                 '50 mV input step, sampled once per clock (A0=80 dB, '
                 'GBW=20 MHz)')
    fig.tight_layout(rect=(0.0, 0.08, 1.0, 1.0))
    path = os.path.join(PLOTS, 'fig_step_response.png')
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path, dict(worst_err_pct=100.0 * worst)


def plot_offset():
    if not os.path.exists(OFFSET_CSV):
        print('WARNING: results/data/offset_test.csv not found; '
              'keeping the committed offset figure (run '
              '`run_sweep.py --mode offset` first).', flush=True)
        return None, {}
    per = {}
    with open(OFFSET_CSV) as f:
        for r in csv.DictReader(f):
            if r.get('status') != 'ok' or int(r.get('rail') or 0) != 0:
                continue
            K = int(r['K'])
            Q = float(r['Q'])
            gdb = round(float(r['gain_db']))
            v = abs(float(r['worst_mV']))
            key = (K, Q, gdb)
            per[key] = max(per.get(key, 0.0), v)
    qs = [0.5, 2.0 ** -0.5, 1.0, 2.0 ** 0.5, 2.0, 2.0 ** 1.5, 4.0, 5.0]
    x = np.arange(len(qs))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)
    for ax, gdb, title in ((axes[0], 0, '0 dB'),
                           (axes[1], 18, '18 dB')):
        for K in KS:
            y = [per.get((K, q, gdb), np.nan) for q in qs]
            if not np.any(np.isfinite(y)):
                continue
            ax.plot(x, y, 's-', color=COLORS[K], ms=6, label=f'K={K}')
        ax.set_yscale('log')
        ax.set_xticks(x)
        ax.set_xticklabels(Q_LABELS, fontsize=8)
        ax.set_xlim(-0.4, len(qs) - 0.6)
        ax.set_xlabel('Q setting')
        ax.set_title(f'gain {title}')
        ax.grid(True, which='both', alpha=0.3)
        ax.axhline(60.0, color='0.2', ls=':', lw=1.3)
        ax.text(-0.2, 64.0, 'all gain/Q max 60 mV', fontsize=8,
                color='0.2')
        if gdb == 0:
            ax.plot([x[0], x[4]], [40.0, 40.0], color='0.2', ls='--',
                    lw=1.3)
            ax.text(-0.2, 42.0, '0 dB/Q<=2 max 40 mV', fontsize=8,
                    color='0.2')
        ax.legend(fontsize=8, loc='lower right')
    axes[0].set_ylabel('max |output offset| (mV), 5 mV op-amp VOS')
    fig.suptitle('Output offset from a 5 mV op-amp offset '
                 '(behavioral, A0=60 dB, settled, same/opposite signs)')
    fig.tight_layout()
    path = os.path.join(PLOTS, 'fig_offset_map.png')
    fig.savefig(path, dpi=110)
    plt.close(fig)
    worst0 = max((v for (K, q, g), v in per.items() if g == 0 and q <= 2.0),
                 default=float('nan'))
    worstall = max(per.values(), default=float('nan'))
    return path, dict(worst0=worst0, worstall=worstall)


def _find_pdk_lib():
    root = os.environ.get('PDK_ROOT', os.path.expanduser('~/.volare'))
    for cand in (os.path.join(root, 'libs.tech', 'ngspice',
                              'sky130.lib.spice'),
                 os.path.join(root, 'sky130A', 'libs.tech', 'ngspice',
                              'sky130.lib.spice')):
        if os.path.exists(cand):
            return cand
    return None


# ---------------------------------------------------------------------------
# Op-amp schematic.  Hand-drawn from design/opamp/opamp_2stage.spice so the
# README has a readable topology figure without requiring xschem or the PDK.

SCH_WIRE = '#1a1a1a'
SCH_DEV = '#124e78'
SCH_NET = '#a23b2a'
SCH_GRAY = '#6b7280'


def _sch_wire(ax, pts, lw=1.6, color=SCH_WIRE, ls='-', z=2):
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color, lw=lw,
            ls=ls, solid_capstyle='round', solid_joinstyle='round', zorder=z)


def _sch_dot(ax, x, y):
    ax.plot([x], [y], 'o', color=SCH_WIRE, ms=4.2, zorder=5)


def _sch_mosfet(ax, x, y, kind, source='bottom', mirror=False):
    """Vertical three-terminal MOSFET symbol centred at (x, y)."""
    ax.plot([x, x], [y - 0.50, y + 0.50], color=SCH_DEV, lw=2.6,
            zorder=3, solid_capstyle='round')
    gx = x + (0.17 if mirror else -0.17)
    ax.plot([gx, gx], [y - 0.38, y + 0.38], color=SCH_DEV, lw=2.6,
            zorder=3, solid_capstyle='round')
    ax.plot([x, x], [y + 0.50, y + 0.88], color=SCH_DEV, lw=1.8, zorder=3)
    ax.plot([x, x], [y - 0.50, y - 0.88], color=SCH_DEV, lw=1.8, zorder=3)
    if mirror:
        ax.plot([gx - 0.03, x + 0.92], [y, y], color=SCH_WIRE, lw=1.8,
                zorder=3)
    else:
        ax.plot([gx + 0.03, x - 0.92], [y, y], color=SCH_WIRE, lw=1.8,
                zorder=3)
    if kind == 'n':
        tri = [[x - 0.075, y - 0.69], [x + 0.075, y - 0.69],
               [x, y - 0.82]]
    elif source == 'top':
        tri = [[x - 0.075, y + 0.72], [x + 0.075, y + 0.72],
               [x, y + 0.59]]
    else:
        tri = [[x - 0.075, y - 0.72], [x + 0.075, y - 0.72],
               [x, y - 0.59]]
    ax.add_patch(Polygon(tri, closed=True, facecolor=SCH_DEV,
                         edgecolor=SCH_DEV, zorder=4))


def _sch_cap(ax, x, y, gap=0.34, width=0.52):
    for yy in (y + gap / 2, y - gap / 2):
        ax.plot([x - width / 2, x + width / 2], [yy, yy], color=SCH_DEV,
                lw=2.2, zorder=3, solid_capstyle='round')


def _sch_res(ax, x, y0, y1, amp=0.16, n=6):
    ys = [y0, y0 + (y1 - y0) * 0.10]
    step = (y1 - y0) * 0.80 / n
    xs = [x, x]
    for i in range(n):
        xs.append(x + (amp if i % 2 == 0 else -amp))
        ys.append(y0 + (y1 - y0) * 0.10 + step * (i + 0.5))
    xs.append(x)
    ys.append(y1)
    _sch_wire(ax, list(zip(xs, ys)), lw=1.8, color=SCH_DEV, z=3)


def _sch_label(ax, x, y, text, ha='center', va='center'):
    ax.text(x, y, text, color=SCH_NET, fontsize=12, fontweight='bold',
            ha=ha, va=va, zorder=7,
            bbox=dict(boxstyle='round,pad=0.12', fc='white', ec='none',
                      alpha=0.75))


def plot_opamp_schematic():
    fig, ax = plt.subplots(figsize=(15.5, 9.0))
    ax.set_xlim(0.8, 20.4)
    ax.set_ylim(-0.85, 11.9)
    ax.set_aspect('equal')
    ax.axis('off')

    ydd, yss = 11.0, 0.7
    _sch_wire(ax, [(1.6, ydd), (19.4, ydd)], lw=2.0, color=SCH_GRAY)
    _sch_wire(ax, [(1.6, yss), (19.4, yss)], lw=2.0, color=SCH_GRAY)
    ax.text(1.5, ydd, 'VDD (3.3 V)', ha='right', va='center',
            color=SCH_GRAY, fontsize=11)
    ax.text(1.5, yss, 'VSS', ha='right', va='center',
            color=SCH_GRAY, fontsize=11)

    # Stage 1: tail, PMOS input pair, NMOS mirror.
    mx0, my0 = 5.7, 9.35
    _sch_mosfet(ax, mx0, my0, 'p', source='top')
    _sch_wire(ax, [(mx0, my0 + 0.88), (mx0, ydd)])
    _sch_wire(ax, [(mx0, my0 - 0.88), (mx0, 8.15)])
    _sch_wire(ax, [(4.0, 8.15), (7.2, 8.15)])
    _sch_dot(ax, mx0, 8.15)
    _sch_label(ax, 3.95, 9.35, 'pbias', ha='right')
    ax.text(mx0 + 0.28, my0 + 0.42, 'M0', color=SCH_DEV, fontsize=11,
            fontweight='bold')
    ax.text(mx0 + 0.28, my0 + 0.10, '20/0.5, ×2', color=SCH_DEV,
            fontsize=8.5)

    for name, xx in (('M1', 4.0), ('M2', 7.2)):
        yy = 7.05
        _sch_mosfet(ax, xx, yy, 'p', source='top', mirror=(name == 'M2'))
        _sch_wire(ax, [(xx, yy + 0.88), (xx, 8.15)])
        _sch_wire(ax, [(xx, yy - 0.88), (xx, 5.9)])
        side = 1 if name == 'M1' else -1
        ha = 'left' if name == 'M1' else 'right'
        ax.text(xx + side * 0.28, yy + 0.42, name, color=SCH_DEV,
                fontsize=11, fontweight='bold', ha=ha)
        ax.text(xx + side * 0.28, yy + 0.10, '20/0.5', color=SCH_DEV,
                fontsize=8.5, ha=ha)
    _sch_wire(ax, [(3.08, 7.05), (2.25, 7.05)])
    _sch_label(ax, 2.12, 7.05, 'inp', ha='right')
    _sch_wire(ax, [(8.12, 7.05), (8.95, 7.05)])
    _sch_label(ax, 9.08, 7.05, 'inn', ha='left')

    for name, xx in (('M3', 4.0), ('M4', 7.2)):
        yy = 4.45
        _sch_mosfet(ax, xx, yy, 'n', mirror=(name == 'M4'))
        _sch_wire(ax, [(xx, yy - 0.88), (xx, yss)])
        _sch_wire(ax, [(xx, yy + 0.88), (xx, 5.9)])
        ax.text(xx - 0.28, yy + 0.40, name, color=SCH_DEV, fontsize=11,
                fontweight='bold', ha='right')
        ax.text(xx - 0.28, yy + 0.08, '5/0.5', color=SCH_DEV,
                fontsize=8.5, ha='right')

    _sch_dot(ax, 4.0, 5.9)
    _sch_dot(ax, 7.2, 5.9)
    _sch_wire(ax, [(4.0, 5.9), (4.55, 5.9)])
    _sch_label(ax, 4.62, 5.9, 'a', ha='left')
    _sch_wire(ax, [(7.2, 5.9), (7.75, 5.9)])
    _sch_label(ax, 7.82, 5.9, 'b', ha='left')
    # M3 is diode-connected; M4 gate is tied to node a (net label).
    _sch_wire(ax, [(3.08, 4.45), (2.78, 4.45), (2.78, 5.9), (4.0, 5.9)])
    _sch_wire(ax, [(8.12, 4.45), (8.72, 4.45)])
    _sch_label(ax, 8.85, 4.45, 'a', ha='left')

    # Stage 2: NMOS common source with PMOS load, mirrored left/right.
    for tag, xx, glab, gside, outlab, outx in (
            ('p', 11.8, 'a', 'left', 'outp', 14.4),
            ('n', 16.6, 'b', 'right', 'outn', 19.2)):
        y5, y6 = 4.15, 6.85
        _sch_mosfet(ax, xx, y5, 'n', mirror=(tag == 'n'))
        _sch_wire(ax, [(xx, y5 - 0.88), (xx, yss)])
        _sch_wire(ax, [(xx, y5 + 0.88), (xx, 5.45)])
        _sch_mosfet(ax, xx, y6, 'p', source='bottom', mirror=(tag == 'n'))
        _sch_wire(ax, [(xx, y6 + 0.88), (xx, ydd)])
        _sch_wire(ax, [(xx, y6 - 0.88), (xx, 5.45)])
        _sch_wire(ax, [(xx, 5.45), (outx, 5.45)])
        _sch_dot(ax, outx, 5.45)
        ax.add_patch(FancyArrowPatch((outx, 5.45), (outx + 0.38, 5.45),
                                     arrowstyle='-|>', mutation_scale=12,
                                     lw=1.4, color=SCH_WIRE, zorder=5))
        _sch_label(ax, outx + 0.48, 5.45, outlab, ha='left')
        n5 = 'M5p' if tag == 'p' else 'M5n'
        n6 = 'M6p' if tag == 'p' else 'M6n'
        side = 1 if gside == 'left' else -1
        ha = 'left' if gside == 'left' else 'right'
        ax.text(xx + side * 0.28, y5 + 0.35, n5, color=SCH_DEV,
                fontsize=11, fontweight='bold', ha=ha)
        ax.text(xx + side * 0.28, y5 + 0.03, '20/0.5', color=SCH_DEV,
                fontsize=8.5, ha=ha)
        ax.text(xx + side * 0.28, y6 + 0.35, n6, color=SCH_DEV,
                fontsize=11, fontweight='bold', ha=ha)
        ax.text(xx + side * 0.28, y6 + 0.03, '20/0.5, ×2', color=SCH_DEV,
                fontsize=8.5, ha=ha)
        if gside == 'left':
            _sch_wire(ax, [(xx - 0.92, y5), (xx - 1.30, y5)])
            _sch_label(ax, xx - 1.40, y5, glab, ha='right')
            _sch_wire(ax, [(xx - 0.92, y6), (xx - 1.30, y6)])
            _sch_label(ax, xx - 1.40, y6, 'cmfb', ha='right')
        else:
            _sch_wire(ax, [(xx + 0.92, y5), (xx + 1.30, y5)])
            _sch_label(ax, xx + 1.40, y5, glab, ha='left')
            _sch_wire(ax, [(xx + 0.92, y6), (xx + 1.30, y6)])
            _sch_label(ax, xx + 1.40, y6, 'cmfb', ha='left')

    # Miller compensation: series Cc + Rz from each first-stage output to
    # the corresponding second-stage output.
    for xx, net, cname, rname in ((14.4, 'a', 'Cc1', 'Rz1'),
                                  (19.2, 'b', 'Cc2', 'Rz2')):
        _sch_label(ax, xx, 9.55, net)
        _sch_wire(ax, [(xx, 9.55), (xx, 8.85)])
        _sch_cap(ax, xx, 8.55)
        _sch_wire(ax, [(xx, 8.38), (xx, 7.75)])
        _sch_res(ax, xx, 7.75, 6.45)
        _sch_wire(ax, [(xx, 6.45), (xx, 5.45)])
        ax.text(xx + 0.33, 8.55, cname, color=SCH_DEV, fontsize=9.5,
                fontweight='bold', ha='left')
        ax.text(xx + 0.33, 7.10, rname, color=SCH_DEV, fontsize=9.5,
                fontweight='bold', ha='left')

    ax.text(5.6, 11.55, 'Stage 1 — PMOS input pair + NMOS mirror',
            ha='center', va='center', color=SCH_GRAY, fontsize=11,
            fontweight='bold')
    ax.text(15.5, 11.55, 'Stage 2 — NMOS common source + PMOS load',
            ha='center', va='center', color=SCH_GRAY, fontsize=11,
            fontweight='bold')
    ax.text(16.8, 9.9, 'Miller compensation', ha='center', va='center',
            color=SCH_GRAY, fontsize=9.5, style='italic')
    ax.text(10.0, -0.20,
            'Cc = 5 pF, Rz = 550 Ω per side  ·  ideal CMFB drives the '
            'M6 gates  ·  all bulks tied to VDD/VSS',
            ha='center', va='center', color=SCH_GRAY, fontsize=9.5)
    ax.text(10.0, -0.62,
            'Sky130 5 V devices (L = 0.5 µm). Drawn from '
            'design/opamp/opamp_2stage.spice.',
            ha='center', va='center', color=SCH_GRAY, fontsize=9.5)

    fig.tight_layout(pad=0.2)
    path = os.path.join(PLOTS, 'fig_opamp_schematic.png')
    fig.savefig(path, dpi=220, facecolor='white', bbox_inches='tight',
                pad_inches=0.08)
    plt.close(fig)
    return path, {}


def plot_opamp():
    lib = _find_pdk_lib()
    if lib is None:
        print('WARNING: Sky130 ngspice library not found; '
              'keeping the committed op-amp Bode figure.', flush=True)
        return None, {}
    corners = (('tt', 'tt', 27.0, 3.3, '#1f77b4'),
               ('ss_110C', 'ss', 110.0, 2.97, '#d62728'),
               ('ff_m40C', 'ff', -40.0, 3.63, '#2ca02c'))
    template = open(os.path.join(OPAMP, 'tb_ac.spice')).read()
    fig, (axg, axp) = plt.subplots(1, 2, figsize=(13, 4.4))
    metrics = {}
    for cname, sect, temp, vdda, color in corners:
        dat = os.path.join(OPAMP, f'plot_ac_{cname}.dat')
        sp = os.path.join(OPAMP, f'plot_ac_{cname}.gen.spice')
        text = (template.replace('__PDK_LIB__', lib)
                .replace('__CORNER__', sect)
                .replace('__TEMP__', str(temp))
                .replace('__VDDA__', str(vdda))
                .replace('__DAT__', dat))
        with open(sp, 'w') as f:
            f.write(text)
        r = subprocess.run(['ngspice', '-b', os.path.basename(sp)],
                           cwd=OPAMP, capture_output=True, text=True,
                           timeout=280)
        os.remove(sp)
        if not os.path.exists(dat):
            print(f'WARNING: op-amp AC failed for {cname}: '
                  f'{(r.stdout + r.stderr)[-200:]}', flush=True)
            continue
        d = np.loadtxt(dat)
        os.remove(dat)
        f = d[:, 0]
        gdb = 20 * np.log10(np.maximum(np.hypot(d[:, 1], d[:, 2]), 1e-30))
        ph = np.degrees(np.unwrap(np.arctan2(d[:, 2], d[:, 1])))
        fgbw = pm = None
        for i in range(len(f) - 1):
            if gdb[i] >= 0.0 > gdb[i + 1]:
                w = gdb[i] / (gdb[i] - gdb[i + 1])
                fgbw = f[i] + w * (f[i + 1] - f[i])
                pm = 180.0 + ph[i] + w * (ph[i + 1] - ph[i])
                break
        label = (f'{cname} {temp:.0f} C {vdda:.2f} V '
                 f'({gdb[0]:.1f} dB, {fgbw / 1e6:.2f} MHz)')
        axg.semilogx(f, gdb, color=color, label=label)
        axp.semilogx(f, ph, color=color, label=label)
        metrics[cname] = dict(A0=gdb[0], GBW=fgbw / 1e6, PM=pm)
    for ax, ylab, title in ((axg, 'differential gain (dB)', 'A0 / GBW'),
                            (axp, 'phase (deg)', 'phase')):
        ax.set_xlabel('Hz')
        ax.set_ylabel(ylab)
        ax.set_title(title)
        ax.grid(True, which='both', alpha=0.3)
        ax.legend(fontsize=7)
    axg.set_ylim(-70, 60)
    fig.suptitle('Two-stage op-amp, CL=16 pF/side, Cc=5 pF, Rz=550 ohm')
    fig.tight_layout()
    path = os.path.join(PLOTS, 'fig_opamp_bode_tt_ss_ff.png')
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path, metrics


def write_snapshot(generated, skipped):
    path = os.path.join(PLOTS, 'README.md')
    with open(path, 'w') as f:
        f.write('# Figure snapshots\n\n')
        f.write('Generated by `python3 sim/plots.py` (`make plots`). '
                'These PNGs are the committed visual evidence; the raw CSV '
                'and simulator data are regenerated by the make targets and '
                'are not committed.\n\n')
        f.write('| Figure | What it shows | Source |\n')
        f.write('|---|---|---|\n')
        f.write('| `fig_capbudget.png` | Total MiM capacitance at 0 and '
                '18 dB and MiM area at 18 dB for all 32 (K,Q) settings. '
                'Dashed lines are the 120 pF target and 0.12 mm2 area spec. '
                'Counts both halves and all branches; switches, op-amps, '
                'bias and routing are excluded. | `sim/capbudget.py` '
                '(exact z-domain) |\n')
        f.write('| `fig_f0_vs_fclk.png` | Programmable f0 = fclk/K versus '
                'clock frequency; K=25 is limited to fclk <= 500 kHz. | '
                'architecture definition |\n')
        f.write('| `fig_q_vs_setting.png` | f0 and Q quantization error of '
                'the unit-cap-plus-trim design versus Q setting. The f0 '
                'panel marks the adopted +/-1 % (K<=100) and +/-1.5 % '
                '(K=200) typ limits; the Q panel marks +/-5 %. | '
                '`sim/capbudget.py` (exact z-domain) |\n')
        f.write('| `fig_step_response.png` | Sampled LP/BP step response '
                'of the behavioral SC biquad against the exact discrete map '
                'for K=50/Q=1, K=25/Q=0.5 and K=200/Q=5 (ideal switches, '
                'A0=80 dB, GBW=20 MHz). | `sim/behavioral/biquad_behav.spice` '
                '+ `run_sweep.py` |\n')
        f.write('| `fig_offset_map.png` | Worst settled output offset '
                'versus Q for each K at 0 and 18 dB, with 5 mV op-amp input '
                'offset and both same-sign and opposite-sign combinations. '
                'Spec lines: 40 mV for 0 dB/Q<=2 and 60 mV for all gain/Q. | '
                '`run_sweep.py --mode offset` |\n')
        f.write('| `fig_opamp_schematic.png` | Two-stage fully differential '
                'op-amp topology with device sizes, Miller Cc/Rz networks and '
                'the ideal CMFB gate drive. Drawn from the committed netlist; '
                'all bulks tie to VDD/VSS. | '
                '`design/opamp/opamp_2stage.spice` |\n')
        f.write('| `fig_opamp_bode_tt_ss_ff.png` | Transistor-level op-amp '
                'differential gain and phase at tt/27 C/3.3 V, ss/110 C/'
                '2.97 V and ff/-40 C/3.63 V (CL=16 pF/side). Legend gives '
                'A0 and GBW from each run. | `design/opamp/tb_ac.spice` '
                '(Sky130 PDK) |\n')
        f.write('\n## Figures\n\n')
        for name, caption in (
                ('fig_capbudget.png',
                 'Cap budget at 0/18 dB and MiM area at 18 dB.'),
                ('fig_f0_vs_fclk.png',
                 'Programmable f0 = fclk/K versus clock frequency.'),
                ('fig_q_vs_setting.png',
                 'f0 and Q quantization error against the adopted typ limits.'),
                ('fig_step_response.png',
                 'Behavioral step response versus the exact discrete map.'),
                ('fig_offset_map.png',
                 'Worst output offset versus Q at 0 and 18 dB.'),
                ('fig_opamp_schematic.png',
                 'Two-stage fully differential op-amp topology.'),
                ('fig_opamp_bode_tt_ss_ff.png',
                 'Transistor-level op-amp gain and phase at three corners.')):
            f.write(f'### {caption}\n\n![{caption}]({name})\n\n')
        f.write('## Snapshot values from this run\n\n')
        for name, text in generated:
            f.write(f'- **{name}**: {text}\n')
        if skipped:
            f.write('\nNot regenerated this run:\n\n')
            for name, why in skipped:
                f.write(f'- **{name}**: {why}\n')
        f.write('\nRe-run with `make cap behav plots` for the full set. '
                '`make plots` alone regenerates the analytical figures, the '
                'schematic and the PDK-free step figure; the offset figure '
                'needs the generated offset CSV and the Bode figure needs '
                'the Sky130 PDK.\n')
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--skip-opamp', action='store_true',
                    help='do not re-run the Sky130 AC testbench')
    args = ap.parse_args()
    os.makedirs(PLOTS, exist_ok=True)
    generated = []
    skipped = []

    path, _ = plot_opamp_schematic()
    generated.append(('op-amp schematic',
                      'two-stage fully differential topology drawn from '
                      'design/opamp/opamp_2stage.spice.'))
    print('wrote', path, flush=True)

    cap_rows = load_cap_rows()
    path, info = plot_capbudget(cap_rows)
    generated.append(('cap budget', '%.1f pF max at 0 dB, %.1f pF max at '
                      '18 dB, %.4f mm2 MiM area at 18 dB.'
                      % (info['max0'], info['max18'], info['maxa'])))
    print('wrote', path, flush=True)
    path, _ = plot_f0_vs_fclk()
    print('wrote', path, flush=True)
    path, info = plot_q_vs_setting(cap_rows)
    generated.append(('quantization',
                      'worst f0 %+.2f %% at K=%d/Q=%g, worst Q %+.2f %% '
                      'at K=%d/Q=%g.'
                      % (info['f0']['f0_err'], info['f0']['K'],
                         info['f0']['Q'], info['q']['Q_err'],
                         info['q']['K'], info['q']['Q'])))
    print('wrote', path, flush=True)
    path, info = plot_step_response()
    generated.append(('step response', 'three settings compared with the '
                      'exact discrete map; worst sampled point differs by '
                      '%.2f %% of that output peak.' % info['worst_err_pct']))
    print('wrote', path, flush=True)
    path, info = plot_offset()
    if path:
        generated.append(('offset', 'worst %.1f mV at 0 dB/Q<=2, %.1f mV '
                          'over all gain/Q.' % (info['worst0'],
                                                info['worstall'])))
        print('wrote', path, flush=True)
    else:
        skipped.append(('offset', 'results/data/offset_test.csv is absent'))
    if args.skip_opamp:
        skipped.append(('op-amp Bode', 'requested by --skip-opamp'))
    else:
        path, metrics = plot_opamp()
        if path:
            generated.append(('op-amp Bode', '; '.join(
                f'{c}: {m["A0"]:.1f} dB / {m["GBW"]:.2f} MHz'
                for c, m in metrics.items()) + '.'))
            print('wrote', path, flush=True)
        else:
            skipped.append(('op-amp Bode', 'Sky130 PDK not found or AC run '
                            'failed'))
    snap = write_snapshot(generated, skipped)
    print('wrote', snap, flush=True)


if __name__ == '__main__':
    main()
