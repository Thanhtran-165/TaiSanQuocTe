#!/usr/bin/env python3
"""
Refresh WGC "Latest World Official Gold Reserves" dataset.

Reads auth cookie from `.secrets/wgc_auth_cookie.txt` (or --cookie-file),
then runs `download_wgc_gold_reserves.py` in Playwright mode.

Usage:
  python scripts/wgc_refresh.py
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cookie-file", default=os.path.join(".secrets", "wgc_auth_cookie.txt"))
    ap.add_argument("--outdir", default="data_wgc")
    ap.add_argument("--python", default=sys.executable, help="Python interpreter to run downloader")
    args = ap.parse_args(argv)

    if not os.path.exists(args.cookie_file):
        print(f"Cookie file not found: {args.cookie_file}", file=sys.stderr)
        print("Run: python scripts/wgc_bootstrap_cookie.py", file=sys.stderr)
        return 2

    with open(args.cookie_file, "r", encoding="utf-8") as f:
        cookie_val = (f.read() or "").strip()
    if not cookie_val:
        print(f"Cookie file is empty: {args.cookie_file}", file=sys.stderr)
        return 2

    env = os.environ.copy()
    env["WGC_AUTH_COOKIE"] = cookie_val

    cmd = [
        args.python,
        "download_wgc_gold_reserves.py",
        "--mode",
        "playwright",
        "--outdir",
        args.outdir,
        "--no-parquet",
    ]
    proc = subprocess.run(cmd, env=env)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

