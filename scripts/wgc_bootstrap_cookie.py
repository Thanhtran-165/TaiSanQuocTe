#!/usr/bin/env python3
"""
Bootstrap WGC authentication cookie for automated downloads.

This script opens a real browser window (Playwright) and lets you log in manually.
After login, it extracts the `wgcAuth_cookie` value and saves it to a local secrets file.

Usage:
  python scripts/wgc_bootstrap_cookie.py

Then backend can read it from:
  .secrets/wgc_auth_cookie.txt

Notes:
  - This avoids storing username/password in code.
  - If WGC uses MFA/CAPTCHA, this approach still works because you complete it interactively once.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

LANDING_URL = "https://www.gold.org/goldhub/data/gold-reserves-by-country"
COOKIE_NAME = "wgcAuth_cookie"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(".secrets", "wgc_auth_cookie.txt"), help="Where to store cookie value")
    ap.add_argument("--timeout", type=int, default=300, help="Seconds to wait for login (default: 300)")
    args = ap.parse_args(argv)

    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        print("Missing dependency: playwright", file=sys.stderr)
        print("Install:\n  python -m pip install playwright\n  playwright install chromium", file=sys.stderr)
        return 2

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(LANDING_URL, wait_until="domcontentloaded", timeout=60_000)

        print("\n== WGC Cookie Bootstrap ==")
        print("1) In the opened browser window, log in to WGC if prompted.")
        print("2) Stay on the site until you're fully logged in.")
        print(f"3) This script will detect `{COOKIE_NAME}` and save it to: {args.out}\n")

        deadline = time.time() + args.timeout
        cookie_val = None
        while time.time() < deadline:
            cookies = context.cookies()
            for c in cookies:
                if c.get("name") == COOKIE_NAME and c.get("value"):
                    cookie_val = c["value"]
                    break
            if cookie_val:
                break
            time.sleep(1)

        if not cookie_val:
            print(f"Timeout: did not find cookie `{COOKIE_NAME}` within {args.timeout}s.", file=sys.stderr)
            browser.close()
            return 1

        with open(args.out, "w", encoding="utf-8") as f:
            f.write(cookie_val.strip() + "\n")

        print("Saved cookie successfully.")
        browser.close()
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

