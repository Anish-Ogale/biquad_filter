# SPDX-License-Identifier: Apache-2.0
# Run the transistor-level two-stage op-amp (design/opamp/opamp_2stage.spice)
# at the 3 review corners, both testbenches:
#   tb_ac.spice   -> DC gain, GBW, phase margin, Idd
#   tb_step.spice -> integrator step settling + output noise
# Writes results/opamp_corners.md.
#
# Requires ngspice on PATH and PDK_ROOT (default ~/.volare). Each ngspice
# invocation spends ~10 s loading Sky130 models; total runtime ~2 min.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
RESULTS="$(cd "$HERE/../.." && pwd)/results"
PDK_ROOT="${PDK_ROOT:-$HOME/.volare}"
PDK="${PDK:-sky130A}"
LIB="$PDK_ROOT/$PDK/libs.tech/ngspice/sky130.lib.spice"

[ -f "$LIB" ] || { echo "ERROR: $LIB not found (set PDK_ROOT)" >&2; exit 1; }
command -v ngspice >/dev/null || { echo "ERROR: ngspice not on PATH" >&2; exit 1; }
mkdir -p "$RESULTS"

# corner name | lib section | temp C | VDDA
CORNERS='tt|tt|27.0|3.3
ss_110C|ss|110.0|2.97
ff_m40C|ff|-40.0|3.63'

gen_deck () { # $1 template  $2 corner-name  $3 sect  $4 temp  $5 vdda  $6 tbtype
  awk -v lib="$LIB" -v sect="$3" -v temp="$4" -v vdda="$5" \
      -v dat="$HERE/tb_$6_$2.dat" '
    { gsub(/__PDK_LIB__/, lib); gsub(/__CORNER__/, sect); gsub(/__TEMP__/, temp);
      gsub(/__VDDA__/, vdda); gsub(/__DAT__/, dat); print }' "$1" \
    > "$HERE/tb_$6_$2.gen.spice"
  if grep -q '__PDK_LIB__\|__CORNER__\|__TEMP__\|__VDDA__\|__DAT__' "$HERE/tb_$6_$2.gen.spice"; then
    echo "ERROR: leftover placeholder in tb_$6_$2.gen.spice" >&2; exit 1
  fi
}

run_tb () { # $1 corner-name  $2 tbtype
  (cd "$HERE" && timeout 280 ngspice -b "tb_$2_$1.gen.spice" > "tb_$2_$1.log" 2>&1)
}

parse_ac () { # $1 dat file -> "A0_dB GBW_MHz PM_deg"
python3 - "$1" <<'PY'
import sys, numpy as np
d = np.loadtxt(sys.argv[1])
f, gr, gi = d[:,0], d[:,1], d[:,2]
gdb = 20*np.log10(np.maximum(np.hypot(gr, gi), 1e-30))
gph = np.degrees(np.unwrap(np.arctan2(gi, gr)))
fgbw = pm = None
for i in range(len(f)-1):
    if gdb[i] >= 0.0 > gdb[i+1]:
        w = gdb[i]/(gdb[i]-gdb[i+1])
        fgbw = f[i] + w*(f[i+1]-f[i])
        pm = 180.0 + gph[i] + w*(gph[i+1]-gph[i])
        break
print(f"{gdb[0]:.1f} {fgbw/1e6 if fgbw else 0:.2f} {pm if fgbw else 0:.1f}")
PY
}

parse_step () { # $1 dat file -> "tau_ns t01pc_ns"
python3 - "$1" <<'PY'
import sys, numpy as np
d = np.loadtxt(sys.argv[1])
t, vod = d[:,0], d[:,1]
vend = vod[-100:].mean()
m = (t > 30e-9) & (t < 400e-9) & (np.abs(vod - vend) > 1e-4)
if m.sum() > 10:
    slope = np.polyfit(t[m], np.log(np.abs(vod[m]-vend)), 1)[0]
    tau = -1.0/slope
    print(f"{tau*1e9:.0f} {np.log(1000)*tau*1e9:.0f}")
else:
    print("na na")
PY
}

parse_log_value () { # $1 log file  $2 regex -> value or "na"
python3 - "$1" "$2" <<'PY'
import sys, re
txt = open(sys.argv[1]).read()
m = re.search(sys.argv[2], txt)
print(m.group(1) if m else "na")
PY
}

{
echo "# Two-stage op-amp, three-corner characterization (transistor-level)"
echo
echo "Testbenches: \`design/opamp/tb_ac.spice\` (open-loop AC, CL = 16 pF/side)"
echo "and \`design/opamp/tb_step.spice\` (resistive feedback gain -0.5, beta = 1/3,"
echo "200 mV diff step, CL = 5 pF/side). Bias: iref = 60 uA, Cc = 5 pF, Rz = 550."
echo "Corners per spec/corners.md; the prototype runs tt / ss@110C / ff@-40C only."
echo "[SIM]"
echo
echo "## tb_ac: gain / GBW / phase margin / supply current"
echo
echo "| corner | A0 dB | GBW MHz | PM deg | Idd uA |"
echo "|---|---:|---:|---:|---:|"
for line in $CORNERS; do
  IFS='|' read -r cname sect temp vdda <<< "$line"
  gen_deck "$HERE/tb_ac.spice"  "$cname" "$sect" "$temp" "$vdda" ac
  run_tb "$cname" ac
  dat="$HERE/tb_ac_${cname}.dat"
  if [ -f "$dat" ]; then
    read -r g0 gbw pm <<< "$(parse_ac "$dat")"
    idd=$(parse_log_value "$HERE/tb_ac_${cname}.log" "i\(vd\)[^0-9-]*([-0-9.eE+]+)")
    idd_uA=$(python3 -c "print(f'{float(\"$idd\")*1e6:.0f}')" 2>/dev/null || echo na)
    echo "| $cname | $g0 | $gbw | $pm | $idd_uA |"
  else
    echo "| $cname | FAIL | | | |"
  fi
  rm -f "$dat"
done
echo
echo "## tb_step: integrator settling and differential output noise"
echo
echo "| corner | tau ns | settle 0.1% ns | inoise uVrms |"
echo "|---|---:|---:|---:|"
for line in $CORNERS; do
  IFS='|' read -r cname sect temp vdda <<< "$line"
  gen_deck "$HERE/tb_step.spice" "$cname" "$sect" "$temp" "$vdda" step
  run_tb "$cname" step
  dat="$HERE/tb_step_${cname}.dat"
  inz=$(parse_log_value "$HERE/tb_step_${cname}.log" "inoise_total\s*=\s*([-0-9.eE+]+)")
  inz_uV=$(python3 -c "print(f'{float(\"$inz\")*1e6:.1f}')" 2>/dev/null || echo na)
  if [ -f "$dat" ]; then
    read -r tau t01 <<< "$(parse_step "$dat")"
    echo "| $cname | $tau | $t01 | $inz_uV |"
  else
    echo "| $cname | FAIL | | $inz_uV |"
  fi
  rm -f "$dat"
done
echo
echo "Targets: gain >= 60 dB, GBW >= 10 MHz (CL = 5 pF eff), PM >= 60 deg,"
echo "Idd <= 250 uA. Note: the shipped v3 netlist measures ~578 uA Idd at tt"
echo "and ~50 dB A0; see results/spec_check.md for the revised targets."
} > "$RESULTS/opamp_corners.md"

rm -f "$HERE"/tb_*_*.gen.spice
echo "done: results/opamp_corners.md"
