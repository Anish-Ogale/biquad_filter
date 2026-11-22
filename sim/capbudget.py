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
  - total MiM capacitance and area at 0 dB and 18 dB
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
GAIN_STEPS = ((0.0, 1.0), (6.0, 2.0), (12.0, 3.98), (18.0, 7.94))
UNIT_F = 25.0          # fF, smallest matchable MiM unit (layout decision)
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


def ktc_output_noise_uV(cs1_fF, cs_fF, cd_fF, ci_fF):
    """Simplified sampled kT/C output-noise estimate [EST].

    Counts both differential halves: 2xCs1, 4xCs (Cs2/Cs3), 2xCd and 4xCI.
    Switched-cap charge noise sqrt(kT*C) referred to the integrator output is
    divided by CI; integrator-cap reset noise is sqrt(kT/CI). Contributions
    are added in power. No 1/f, op-amp or clock-feedthrough term is included.
    """
    kt = KT_C
    ci = ci_fF * 1e-15
    cs1 = cs1_fF * 1e-15
    cs = cs_fF * 1e-15
    cd = cd_fF * 1e-15
    power = 4.0 * kt / ci + 2.0 * kt * (cs1 + 2.0 * cs + cd) / (ci * ci)
    return math.sqrt(power) / 1e-6


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
            # Cap count for BOTH differential halves and all branches:
            #   Cs1 = G*Cs (2 caps) + Cs2/Cs3 = Cs (4 caps)
            #   + Cd (2 caps) + CI1/CI2 (4 caps).
            cs1 = {g: quantize(G * Cs_t, args.unit) for g, G in GAIN_STEPS}
            total_by_gain = {
                g: 2 * cs1[g] + 4 * Cs_t + 2 * Cd_t + 4 * CI_F
                for g, _ in GAIN_STEPS}
            area_by_gain = {
                g: (2 * mim_area(cs1[g]) + 4 * mim_area(Cs_t)
                    + 2 * mim_area(Cd_t) + 4 * mim_area(CI_F)) / 1e6
                for g, _ in GAIN_STEPS}
            total0 = total_by_gain[0.0]
            total18 = total_by_gain[18.0]
            area0 = area_by_gain[0.0]
            area18 = area_by_gain[18.0]
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
            if total18 > 120e3:
                flags.append('total>120pF@18dB')
            if area18 > 0.12:
                flags.append('area>0.12mm2@18dB')
            # band-peak BP gain from the exact state matrix |H_BP(e^{jw})|
            Mm = np.array([[1.0/(1.0+a_d), a/(1.0+a_d)], [-a, 1.0]])
            n_band = max(64, K)  # cover f0 +-2%
            ws = 2*np.pi/K * np.linspace(0.98, 1.02, n_band)
            def bp_peak(gain):
                Bv = np.array([gain * a/(1.0+a_d), 0.0])
                return max(abs(np.linalg.solve(
                    np.exp(1j*w)*np.eye(2)-Mm, Bv)[0]) for w in ws)
            gb0 = bp_peak(1.0)
            gb18 = bp_peak(7.94)
            ktc_uV_0dB = ktc_output_noise_uV(Cs_t, Cs_t, Cd_t, CI_F)
            ktc_uV_18dB = ktc_output_noise_uV(cs1[18.0], Cs_t, Cd_t, CI_F)
            rows.append(dict(
                CI_pF=CI_F / 1e3, K=K, Q=QNAME(Q),
                Cs_pF=Cs_F / 1e3, Cd_pF=Cd_F / 1e3,
                Cs_q_pF=Cs_t / 1e3, Cd_q_pF=Cd_t / 1e3,
                Cs1_18dB_pF=cs1[18.0] / 1e3,
                n_Cs=int(round(Cs_t / args.unit)), n_Cd=int(round(Cd_t / args.unit)) if Cd_t else 0,
                a=a, a_d=a_d,
                f0_ideal_Hz=1e6 / K, f0_quant_err_pct=f0_err,
                Q_quant_err_pct=Q_err,
                sigma_mim_pct=2.8 / math.sqrt(mim_area(min(Cs_t, CI_F) if Cs_t else 1.0)),
                ktc_uVrms=ktc_uV_0dB,
                ktc_uVrms_0dB=ktc_uV_0dB,
                ktc_uVrms_18dB=ktc_uV_18dB,
                bp_peak_gain_0dB=20 * math.log10(gb0),
                bp_peak_gain_18dB=20 * math.log10(gb18),
                total_cap_pF=total0 / 1e3,
                total_cap_pF_18dB=total18 / 1e3,
                total_area_mm2=area0,
                total_area_mm2_18dB=area18,
                q_par_err_pct=0.0,
                flags=';'.join(flags)))
    # CSV
    cols = ['CI_pF', 'K', 'Q', 'Cs_pF', 'Cd_pF', 'Cs_q_pF', 'Cd_q_pF',
            'Cs1_18dB_pF', 'n_Cs', 'n_Cd', 'a', 'a_d', 'f0_ideal_Hz',
            'f0_quant_err_pct', 'Q_quant_err_pct', 'sigma_mim_pct',
            'ktc_uVrms', 'ktc_uVrms_0dB', 'ktc_uVrms_18dB',
            'bp_peak_gain_0dB', 'bp_peak_gain_18dB',
            'total_cap_pF', 'total_cap_pF_18dB', 'total_area_mm2',
            'total_area_mm2_18dB', 'flags']
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
        f.write('Gain is the input-branch cap Cs1 = G*Cs; Cs2, Cs3, Cd and CI '
                'are unchanged. The 18 dB column uses G = 7.94. Totals and '
                'areas count both differential halves and all branches: '
                '2xCs1 + 4xCs (Cs2/Cs3) + 2xCd + 4xCI.\n\n')
        f.write('Flags: `Cd<100fF:trim-sensitive` damping cap needs the 3-bit trim '
                'to be exercised; `Cd<unit:UNMATCHABLE` cannot be built from whole '
                'units; `total>120pF@18dB` exceeds the 120 pF target; '
                '`area>0.12mm2@18dB` exceeds the area spec.\n\n')
        for K in KS:
            fmax = 500e3 if K == 25 else 1e6
            f.write('## K = %d (fclk up to %.0f kHz -> f0 up to %.1f kHz; row f0 err is vs fclk/K)\n\n' % (K, fmax / 1e3, fmax / K / 1e3))
            f.write('| Q | Cs pF | Cd pF |(Cs q)| (Cd q)| n_Cs | n_Cd | f0 err % | Q err % | Cs1@18 pF | tot@0 pF | tot@18 pF | area@18 mm² | flags |\n')
            f.write('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|\n')
            for r in rows:
                if r.get('K') != K:
                    continue
                if 'error' in r:
                    f.write('| %s | — | — | — | — | — | — | — | — | — | — | — | — | %s |\n'
                            % (QNAME(r['Q']), r['error']))
                    continue
                f.write('| %s | %.4f | %.4f | %.4f | %.4f | %d | %d | %+.2f | %+.2f | %.2f | %.1f | %.1f | %.4f | %s |\n'
                        % (r['Q'], r['Cs_pF'], r['Cd_pF'], r['Cs_q_pF'], r['Cd_q_pF'],
                           r['n_Cs'], r['n_Cd'], r['f0_quant_err_pct'],
                           r['Q_quant_err_pct'], r['Cs1_18dB_pF'],
                           r['total_cap_pF'], r['total_cap_pF_18dB'],
                           r['total_area_mm2_18dB'], r['flags'] or ''))
        max_tot0 = max(r.get('total_cap_pF', 0) for r in rows)
        max_tot18 = max(r.get('total_cap_pF_18dB', 0) for r in rows)
        max_area0 = max(r.get('total_area_mm2', 0) for r in rows)
        max_area18 = max(r.get('total_area_mm2_18dB', 0) for r in rows)
        f.write('\nAt 0 dB: max total %.1f pF, max MiM area %.4f mm².\n'
                % (max_tot0, max_area0))
        f.write('At 18 dB: max total %.1f pF (<=120 pF target: %s), '
                'max MiM area %.4f mm² (0.12 mm² spec: %s).\n'
                % (max_tot18, 'within' if max_tot18 <= 120 else 'EXCEEDS',
                   max_area18, 'within' if max_area18 <= 0.12 else 'EXCEEDS'))
        rn0 = max(rows, key=lambda r: r.get('ktc_uVrms_0dB', 0))
        rn18 = max(rows, key=lambda r: r.get('ktc_uVrms_18dB', 0))
        f.write('\nkT/C output-noise estimate [EST]: max **%.1f µVrms** at 0 dB '
                '(K=%s, Q=%s) and **%.1f µVrms** at 18 dB (K=%s, Q=%s). '
                'Method: sampled kT/C of both halves of Cs1/Cs2/Cs3/Cd/CI, '
                'power-summed; excludes 1/f, op-amp and clock-feedthrough '
                'noise.\n'
                % (rn0['ktc_uVrms_0dB'], rn0['K'], rn0['Q'],
                   rn18['ktc_uVrms_18dB'], rn18['K'], rn18['Q']))
    print('wrote', csvp, 'and', mdp)


if __name__ == '__main__':
    main()
