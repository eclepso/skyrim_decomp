#!/usr/bin/env python3
"""CI entry for pushes: the full repository check, then the site build from the same data.

The check is tools/check.py's own scan and validation (check.run), so nothing it fails on is
dropped. The site is built from the data that validation returned instead of validating a
second time, and its slow Git-history trend is computed in a separate process while the
validation runs.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import build_site
import check
from check import ROOT


def main():
    with tempfile.TemporaryDirectory() as tmp:
        rows = os.path.join(tmp, 'trend-rows.json')
        trend = subprocess.Popen([sys.executable, str(Path(__file__).with_name('build_model_trend.py')),
                                  '--rows-out', rows], cwd=ROOT)
        try:
            count, _ = check.run(then=lambda data: build_after(data, trend, rows))
        except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
            print(f'FAIL: {exc}', file=sys.stderr)
            return 1
        finally:
            if trend.poll() is None:
                trend.kill()
            trend.wait()
    print(f'PASS: metadata and {count} tracked files. No Skyrim byte comparison performed.')
    return 0


def build_after(data, trend, rows):
    if trend.wait() != 0:
        raise ValueError('trend history failed')
    build_site.build(data, rows)


if __name__ == '__main__':
    raise SystemExit(main())
