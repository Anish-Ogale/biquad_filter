#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Assemble the three Q-evidence sections into one committed Markdown file.

The individual experiments write CSV data plus a Markdown fragment under
results/data/:

  qcheck.fragment.md       real-corner differential Q error
  q2check.fragment.md      Q<=2 at 18 dB A0/GBW sweep
  q_crosscheck.fragment.md step-ring versus multisine method check

This script concatenates them, in that order, into
results/behavioral/q_evidence.md.  If a fragment is missing it leaves the
existing committed file untouched and prints a warning.

Run:  python3 sim/behavioral/q_evidence.py
Out:  results/behavioral/q_evidence.md
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.abspath(os.path.join(HERE, '..', '..', 'results'))
BEHAVIORAL = os.path.join(RESULTS, 'behavioral')
DATA = os.path.join(RESULTS, 'data')
PARTS = ('qcheck.fragment.md', 'q2check.fragment.md',
         'q_crosscheck.fragment.md')


def main():
    paths = [os.path.join(DATA, name) for name in PARTS]
    missing = [p for p in paths if not os.path.exists(p)]
    out = os.path.join(BEHAVIORAL, 'q_evidence.md')
    if missing:
        print('WARNING: missing Q fragment(s): '
              + ', '.join(os.path.basename(p) for p in missing)
              + '; keeping existing ' + out, flush=True)
        return
    os.makedirs(BEHAVIORAL, exist_ok=True)
    with open(out, 'w') as f:
        f.write('# Q evidence\n\n')
        for i, path in enumerate(paths):
            if i:
                f.write('\n')
            f.write(open(path).read().rstrip() + '\n')
    print(f'wrote {out}', flush=True)


if __name__ == '__main__':
    main()
