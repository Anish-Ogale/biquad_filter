#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Capacitor budget for the clock-programmable SC biquad — every (K, Q) setting.

Exact z-domain design (docs/architecture.md section 2):

    theta = 2*pi/K,  r = exp(-theta/(2*Q)),  u = 2*r*cos(theta) - 1
    Cd/CI = a_d = 1/u - 1,   Cs/CI = a = sqrt(r*r/u - 1)

Outputs, for each K in {25,50,100,200} and Q in the 8 sqrt2-spaced steps
(0.5 ... 5.0), at each CI in a small sweep (4/6/8 pF):

  - Cs, Cd (ideal), quantized to a 25 fF unit cap (only unit multiples are
    layout-real; 3-bit trim is assumed on top: +-3 units)
  - f0 and Q of the QUANTIZED design (state-matrix poles), and with trim
  - MiM (cap_mim_m3_2) square side and area: C = 2.0 w^2 + 0.76 w  [fF, um]
  - total MiM area; attenuator caps for the 2-bit gain
  - FLAGS: damping cap too small to match (the K=200/Q=5 known issue),
    quantized f0/Q exceeding typ spec, u<=0 (no solution)

Run:   python3 sim/capbudget.py [--ci 8e-12]
Out:   results/capbudget_table.csv, results/capbudget_table.md
"""
import argparse, csv, math, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


KS = (25, 50, 100, 200)
QS = (0.5, 2.0**-0.5, 1.0, 2.0**0.5, 2.0, 2.0**1.5, 4.0, 5.0)   # sqrt2-spaced
GAINS_DB = (0, 6, 12, 18)
UNIT_F = 25.0          # fF, smallest matchable MiM unit (layout decision)
ATT_TOTAL_F = 16000.0  # fF, input attenuator total (constant load -> f0 const)
MIM_AREA_F = 2.0       # fF/um^2
MIM_PERIM_F = 0.19     # fF/um per side
KT_C = 1.38e-23 * 300.0

def design_exact(K, Q):
    """Exact (a, a_d) for the two-delay topology (see docs/architecture.md)."""
    theta = 2.0 * math.pi / K
    r = math.exp(-theta / (2.0 * Q))
    u = 2.0 * r * math.cos(theta) - 1.0
    if u <= 0.0:
        raise ValueError(f"no solution: K={K} Q={Q} gives u={u:.4f}")
    a_d = 1.0 / u - 1.0
    arg = r * r / u - 1.0
    if arg <= 0.0:
        raise ValueError(f"no solution: K={K} Q={Q} gives a^2={arg:.4f}")
    a = math.sqrt(arg)
    return theta, a, a_d


def state_matrix(a, a_d):
    return np.array([[1.0 / (1.0 + a_d), a / (1.0 + a_d)],
                     [-a, 1.0]])


def poles_from_matrix(M):
    return np.linalg.eigvals(M)


QNAME = lambda q: ('%.4g' % q)


def mim_side(cf):
    """Square MiM side (um) for C (fF) with 2.0 fF/um^2 + 0.19 fF/um perimeter."""
    w = 10.0
    for _ in range(200):
        c = MIM_AREA_F * w * w + MIM_PERIM_F * 4.0 * w
        w += (cf - c) / (2.0 * MIM_AREA_F * w + 4.0 * MIM_PERIM_F)
    return w


def mim_area(cf):
    return mim_side(cf) ** 2


def z_response(a, a_d, K):
    """Return (f0, Q) of z-plane poles for ratio (a, a_d), f0 = fclk/K base."""
    M = state_matrix(a, a_d)
    p = poles_from_matrix(M)
    r = float(abs(p[0]))
    ang = math.atan2(float(abs(p[0].imag)), float(p[0].real))
    f0 = ang / (2.0 * math.pi)
    # Q from pole radius at angle theta: r = exp(-theta/(2Q))
    Q = -ang / (2.0 * math.log(r)) if r > 0 and r < 1 else float('inf')
    if r >= 1.0:
        Q = float('inf')
    return f0, Q


def quantize(x, unit=UNIT_F):
    return max(unit, round(x / unit) * unit)


def evaluate(K, Q, CI_F, c_cs, c_cd):
    a = c_cs / CI_F
    a_d = c_cd / CI_F
    try:
        fz, qz = z_response(a, a_d, K)
    except ValueError:
        return None
    return fz, qz


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ci', type=float, default=8e-12, help='integrator cap (F)')
    ap.add_argument('--unit', type=float, default=UNIT_F, help='unit cap fF')
    ap.add_argument('--out', default=os.path.join(HERE, '..', 'results'))
    args = ap.parse_args()
    CI_F = args.ci * 1e15  # fF
    os.makedirs(args.out, exist_ok=True)
    rows = []
    for K in KS:
        for Q in QS:
            try:
                _, a, a_d = design_exact(K, Q)
            except ValueError:
                rows.append(dict(K=K, Q=Q, error='u<=0 (no solution)'))
                continue
            Cs_F = a * CI_F
            Cd_F = max(a_d * CI_F, 0.0)
            Cs_q = quantize(Cs_F, args.unit)
            Cd_q = quantize(Cd_F, args.unit) if Cd_F > 0 else 0.0
            res = evaluate(K, Q, CI_F, Cs_q, Cd_q)
            f0q, Qq = res if res else (float('nan'), float('nan'))
            # trim: coarse +-3 units + fine 1/8-unit (4-bit fractional trim
            # array), minimizing combined f0/Q error
            best = (f0q, Qq, Cs_q, Cd_q)
            cost = lambda r: abs(r[1] - Q) / Q + abs(r[0] - 1.0 / K) * K
            n0 = int(round(Cs_q / args.unit))
            d0 = int(round(Cd_q / args.unit))
            fine = args.unit / 8.0
            for dn in range(-3, 4):
                for dm in range(-4, 5):
                    for dd in range(-3, 4):
                        for dm2 in range(-4, 5):
                            nC = (n0 + dn) * args.unit + dm * fine
                            nD = (d0 + dd) * args.unit + dm2 * fine
                            if nC <= 0 or nD <= 0:
                                continue
                            r = evaluate(K, Q, CI_F, nC, nD)
                            if r and cost(r) < cost(best):
                                best = (r[0], r[1], nC, nD)
            f0t, Qt, Cs_t, Cd_t = best
            f0_err = (f0t - 1.0 / K) / (1.0 / K) * 100.0
            Q_err = (Qt - Q) / Q * 100.0
            area = mim_area(Cs_t) * 2 + mim_area(Cd_t) * 2 + mim_area(CI_F) * 2
            # input attenuator caps (constant total load)
            att = {}
            for g in GAINS_DB:
                ctop = ATT_TOTAL_F * 10 ** (-g / 20.0)
                att[g] = (ctop, ATT_TOTAL_F - ctop)
            att_max = max(v[0] + v[1] for v in att.values())
            total_C = area and (2 * Cs_t + 2 * Cd_t + 2 * CI_F + att_max)
            flags = []
            if Cd_F < 100.0:
                flags.append('Cd<100fF:trim-sensitive')
            if Cd_q < args.unit and Cd_F > 0:
                flags.append('Cd<unit:UNMATCHABLE')
            if abs(f0_err) > 1.0:
                flags.append('f0_err>1%typ')
            if abs(Q_err) > (5.0 if Q <= 2.0 else 15.0):
                flags.append('Q_err>typ')
            if a_d <= 0:
                flags.append('a_d<=0')
            # band-peak BP gain from the exact state matrix |H_BP(e^{jw})|
            Mm = np.array([[1.0/(1.0+a_d), a/(1.0+a_d)], [-a, 1.0]])
            n_band = max(64, K)  # cover f0 +-2%
            ws = 2*np.pi/K * np.linspace(0.98, 1.02, n_band)
            Bv = np.array([a/(1.0+a_d), 0.0])
            gb = max(abs(np.linalg.solve(np.exp(1j*w)*np.eye(2)-Mm, Bv)[0])
                     for w in ws)
            ktc_uV = math.sqrt(KT_C * CI_F * 1e-15) / 1e-6
            rows.append(dict(
                CI_pF=CI_F / 1e3, K=K, Q=QNAME(Q),
                Cs_pF=Cs_F / 1e3, Cd_pF=Cd_F / 1e3,
                Cs_q_pF=Cs_t / 1e3, Cd_q_pF=Cd_t / 1e3,
                n_Cs=int(round(Cs_t / args.unit)), n_Cd=int(round(Cd_t / args.unit)) if Cd_t else 0,
                a=a, a_d=a_d,
                f0_ideal_Hz=1e6 / K, f0_quant_err_pct=f0_err,
                Q_quant_err_pct=Q_err,
                sigma_mim_pct=2.8 / math.sqrt(mim_area(min(Cs_t, CI_F) if Cs_t else 1.0)),
                ktc_uVrms=ktc_uV,
                bp_peak_gain_dB=20 * math.log10(gb),
                total_cap_pF=total_C / 1e3,
                total_area_mm2=2 * (mim_area(Cs_t) + mim_area(Cd_t) + mim_area(CI_F) + mim_area(ATT_TOTAL_F)) / 1e6,
                q_par_err_pct=0.0,
                flags=';'.join(flags)))
    # CSV
    cols = ['CI_pF', 'K', 'Q', 'Cs_pF', 'Cd_pF', 'Cs_q_pF', 'Cd_q_pF', 'n_Cs',
            'n_Cd', 'a', 'a_d', 'f0_ideal_Hz', 'f0_quant_err_pct',
            'Q_quant_err_pct', 'sigma_mim_pct', 'ktc_uVrms', 'bp_peak_gain_dB',
            'total_cap_pF', 'total_area_mm2', 'flags']
    csvp = os.path.join(args.out, 'capbudget_table.csv')
    with open(csvp, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols + ['error'])
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, '') for c in cols + ['error']})
    # Markdown: one table per K
    mdp = os.path.join(args.out, 'capbudget_table.md')
    with open(mdp, 'w') as f:
        f.write('# Capacitor budget (exact z-domain, CI = %.0f pF, unit = %.0f fF)\n\n'
                % (CI_F / 1e3, args.unit))
        f.write('Flags: `Cd<100fF:trim-sensitive` damping cap needs the 3-bit trim '
                'to be exercised; `Cd<unit:UNMATCHABLE` cannot be built from whole units.\n\n')
        for K in KS:
            fmax = 500e3 if K == 25 else 1e6
            f.write('## K = %d (fclk up to %.0f kHz -> f0 up to %.1f kHz; row f0 err is vs fclk/K)\n\n' % (K, fmax / 1e3, fmax / K / 1e3))
            f.write('| Q | Cs pF | Cd pF |(Cs q)| (Cd q)| n_Cs | n_Cd | f0 err %% | Q err %% | total pF | flags |\n')
            f.write('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|\n')
            for r in rows:
                if r.get('K') != K:
                    continue
                if 'error' in r:
                    f.write('| %s | — | — | — | — | — | — | — | — | — | %s |\n'
                            % (QNAME(r['Q']), r['error']))
                    continue
                f.write('| %s | %.4f | %.4f | %.4f | %.4f | %d | %d | %+.2f | %+.2f | %.1f | %s |\n'
                        % (r['Q'], r['Cs_pF'], r['Cd_pF'], r['Cs_q_pF'], r['Cd_q_pF'],
                           r['n_Cs'], r['n_Cd'], r['f0_quant_err_pct'],
                           r['Q_quant_err_pct'], r['total_cap_pF'], r['flags'] or ''))
        f.write('\nTotal MiM area (max over settings): %.4f mm²\n'
                % max(r.get('total_area_mm2', 0) for r in rows))
    print('wrote', csvp, 'and', mdp)


if __name__ == '__main__':
    main()
