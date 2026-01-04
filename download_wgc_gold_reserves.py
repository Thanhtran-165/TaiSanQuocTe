#!/usr/bin/env python3
"""
Download and normalize "Latest World Official Gold Reserves" XLSX from World Gold Council (WGC).

Landing page:
  https://www.gold.org/goldhub/data/gold-reserves-by-country

Outputs (in --outdir):
  - wgc_gold_reserves_latest.csv
  - wgc_gold_reserves_latest.parquet (optional)

Requires:
  - requests
  - pandas
  - openpyxl (for reading xlsx)
  - (optional) pyarrow (for parquet)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Iterable, Optional
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests


LANDING_URL = "https://www.gold.org/goldhub/data/gold-reserves-by-country"
DEFAULT_OUTDIR = "./data_wgc"
AUTH_COOKIE_NAME = "wgcAuth_cookie"
AUTH_COOKIE_ENV = "WGC_AUTH_COOKIE"


log = logging.getLogger("wgc_downloader")


class DownloadBlockedError(RuntimeError):
    pass

class MissingDependencyError(RuntimeError):
    pass


class AnchorExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_a = False
        self._cur_href: Optional[str] = None
        self._cur_text_parts: list[str] = []
        self.anchors: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() != "a":
            return
        self._in_a = True
        self._cur_href = None
        self._cur_text_parts = []
        for k, v in attrs:
            if k.lower() == "href" and v:
                self._cur_href = v

    def handle_data(self, data: str) -> None:
        if not self._in_a:
            return
        if data:
            self._cur_text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a":
            return
        self._in_a = False
        href = (self._cur_href or "").strip()
        text = re.sub(r"\s+", " ", "".join(self._cur_text_parts)).strip()
        if href:
            self.anchors.append((href, text))
        self._cur_href = None
        self._cur_text_parts = []


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sleep_rl() -> None:
    time.sleep(0.2)


def _is_retryable_status(code: int) -> bool:
    return code in {429} or 500 <= code <= 599


def request_with_retries(
    session: requests.Session,
    method: str,
    url: str,
    *,
    headers: Optional[dict] = None,
    params: Optional[dict] = None,
    stream: bool = False,
    timeout: tuple[float, float] = (10.0, 30.0),
    max_retries: int = 3,
) -> requests.Response:
    last_err: Optional[BaseException] = None
    for attempt in range(1, max_retries + 1):
        _sleep_rl()
        try:
            resp = session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                stream=stream,
                timeout=timeout,
                allow_redirects=True,
            )
            if _is_retryable_status(resp.status_code):
                last_err = RuntimeError(f"HTTP {resp.status_code} for {url}")
                log.warning("Retryable HTTP error (%s): %s", resp.status_code, url)
                resp.close()
            elif resp.status_code in {401, 403}:
                resp.close()
                raise DownloadBlockedError(
                    f"Download blocked (HTTP {resp.status_code}). "
                    f"Try setting {AUTH_COOKIE_ENV} (a valid {AUTH_COOKIE_NAME} value) or download manually and use --local-xlsx."
                )
            else:
                # Non-retryable HTTP errors should fail fast (4xx).
                resp.raise_for_status()
                return resp
        except requests.RequestException as e:
            last_err = e
            log.warning("Request error (attempt %d/%d): %s", attempt, max_retries, e)

        if attempt < max_retries:
            backoff = 0.6 * (2 ** (attempt - 1))
            time.sleep(backoff)

    raise RuntimeError(f"Failed after {max_retries} attempts: {url}") from last_err


def fetch_html(session: requests.Session, url: str) -> str:
    log.info("Fetching landing page: %s", url)
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; WGCReservesBot/1.0; +https://example.invalid)",
        "Accept": "text/html,application/xhtml+xml",
    }
    resp = request_with_retries(session, "GET", url, headers=headers, timeout=(10.0, 30.0))
    _sleep_rl()
    resp.encoding = resp.encoding or "utf-8"
    return resp.text


def extract_download_url(landing_url: str, html: str) -> str:
    """
    Find download link via:
      A) Anchor-text strategy
      B) Regex fallback
    """
    parser = AnchorExtractor()
    parser.feed(html)

    def norm(s: str) -> str:
        return re.sub(r"\s+", " ", s).strip().lower()

    keywords = ["latest world official gold reserves", "world official gold reserves", "official gold reserves"]
    anchors = parser.anchors

    # Strategy A: anchor text contains both "download" and "xlsx" and WGC title.
    best_a = None
    for href, text in anchors:
        t = norm(text)
        if "download" in t and "xlsx" in t and any(k in t for k in keywords):
            best_a = href
            break
    if best_a:
        url = urljoin(landing_url, best_a)
        log.info("Found XLSX link via Strategy A: %s", url)
        return url

    # Strategy B: regex on hrefs; prioritize likely file links.
    hrefs = []
    href_re = re.compile(r"""href\s*=\s*['"]([^'"]+)['"]""", re.IGNORECASE)
    for m in href_re.finditer(html):
        hrefs.append(m.group(1))

    candidates = []
    for href in hrefs:
        h = href.strip()
        if not h:
            continue
        h_low = h.lower()
        if h_low.endswith(".xlsx") or ".xlsx?" in h_low or "/download/file/" in h_low:
            score = 0
            for kw in ["official", "gold", "reserve", "reserves", "holdings", "world_official", "world-official"]:
                if kw in h_low:
                    score += 1
            if h_low.endswith(".xlsx") or ".xlsx?" in h_low:
                score += 2
            if "/download/file/" in h_low:
                score += 1
            candidates.append((score, h))

    if not candidates:
        raise RuntimeError("Could not find XLSX download link on landing page.")

    candidates.sort(key=lambda x: x[0], reverse=True)
    url = urljoin(landing_url, candidates[0][1])
    log.info("Found XLSX link via Strategy B: %s", url)
    return url


@dataclass
class DownloadResult:
    final_url: str
    path: str
    size_bytes: int
    sha256: str


def _filename_from_response(resp: requests.Response, fallback_name: str) -> str:
    cd = resp.headers.get("Content-Disposition") or resp.headers.get("content-disposition") or ""
    m = re.search(r'filename\*=UTF-8\'\'([^;]+)', cd)
    if m:
        return os.path.basename(m.group(1))
    m = re.search(r'filename=\"?([^\";]+)\"?', cd)
    if m:
        return os.path.basename(m.group(1))
    return fallback_name


def _sanitize_filename(name: str) -> str:
    name = name.strip().replace("\\", "_").replace("/", "_")
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    if not name.lower().endswith(".xlsx"):
        name = f"{name}.xlsx"
    return name


def download_file(session: requests.Session, download_url: str, outdir: str) -> DownloadResult:
    log.info("Downloading XLSX...")
    os.makedirs(outdir, exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; WGCReservesBot/1.0; +https://example.invalid)",
        "Referer": LANDING_URL,
        "Accept": "*/*",
    }
    auth_cookie = os.environ.get(AUTH_COOKIE_ENV)
    if auth_cookie:
        headers["Cookie"] = f"{AUTH_COOKIE_NAME}={auth_cookie}"
    resp = request_with_retries(session, "GET", download_url, headers=headers, stream=True, timeout=(10.0, 60.0))
    final_url = resp.url

    # Determine filename
    parsed = urlparse(final_url)
    fallback = os.path.basename(parsed.path) or "wgc_gold_reserves_latest.xlsx"
    filename = _sanitize_filename(_filename_from_response(resp, fallback))
    out_path = os.path.join(outdir, filename)

    hasher = hashlib.sha256()
    size = 0

    # Validate by magic bytes: XLSX is a ZIP file, starts with b"PK"
    first_chunk = None
    try:
        for chunk in resp.iter_content(chunk_size=1024 * 64):
            if not chunk:
                continue
            if first_chunk is None:
                first_chunk = chunk
                sniff = chunk[:256].lstrip()
                ct = (resp.headers.get("Content-Type") or "").lower()
                if ct.startswith("text/html") or sniff.startswith(b"<!doctype") or sniff.startswith(b"<html") or sniff.startswith(b"<"):
                    raise DownloadBlockedError(
                        f"Download blocked (likely requires login). Try setting {AUTH_COOKIE_ENV} or use --local-xlsx."
                    )
                if not chunk.startswith(b"PK"):
                    raise RuntimeError("Downloaded content does not look like an XLSX (missing ZIP magic bytes 'PK').")
            with open(out_path, "ab") as f:
                f.write(chunk)
            hasher.update(chunk)
            size += len(chunk)
    finally:
        resp.close()

    if size <= 0:
        raise RuntimeError("Download completed but file is empty.")

    log.info("Downloaded to: %s", out_path)
    return DownloadResult(final_url=final_url, path=out_path, size_bytes=size, sha256=hasher.hexdigest())

def _looks_like_html(payload: bytes) -> bool:
    sniff = payload[:512].lstrip().lower()
    return sniff.startswith(b"<!doctype") or sniff.startswith(b"<html") or sniff.startswith(b"<head") or sniff.startswith(b"<")

def _ensure_xlsx_bytes(payload: bytes) -> None:
    if _looks_like_html(payload):
        raise DownloadBlockedError(
            f"Download blocked (likely requires login). Try setting {AUTH_COOKIE_ENV} or use --local-xlsx."
        )
    if not payload.startswith(b"PK"):
        raise RuntimeError("Downloaded content does not look like an XLSX (missing ZIP magic bytes 'PK').")

def _download_via_playwright(download_url: str, outdir: str, *, headless: bool = True) -> DownloadResult:
    """
    Browser-automation download using Playwright (headless Chromium).
    This is intended to bypass WAF/bot protection that blocks plain HTTP clients.
    """
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception as e:
        raise MissingDependencyError(
            "Missing dependency: playwright. Install with:\n"
            "  pip install playwright\n"
            "  playwright install chromium"
        ) from e

    os.makedirs(outdir, exist_ok=True)

    # Retry wrapper (3 attempts) because some runs may fail due to transient WAF/network.
    last_err: Optional[BaseException] = None
    for attempt in range(1, 4):
        _sleep_rl()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=headless)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    accept_downloads=True,
                )
                auth_cookie = os.environ.get(AUTH_COOKIE_ENV)
                if auth_cookie:
                    try:
                        context.add_cookies(
                            [
                                {
                                    "name": AUTH_COOKIE_NAME,
                                    "value": auth_cookie,
                                    "domain": "www.gold.org",
                                    "path": "/",
                                    "httpOnly": True,
                                    "secure": True,
                                    "sameSite": "Lax",
                                }
                            ]
                        )
                    except Exception:
                        pass
                page = context.new_page()
                page.goto(LANDING_URL, wait_until="domcontentloaded", timeout=60_000)
                # Light attempt to accept cookie banners if present.
                try:
                    for label in ["Accept", "I agree", "Agree", "Accept all", "OK"]:
                        btn = page.get_by_role("button", name=re.compile(rf"^{re.escape(label)}$", re.IGNORECASE))
                        if btn.count() > 0:
                            btn.first.click(timeout=1_500)
                            break
                except Exception:
                    pass

                # Prefer "real user" click download; some WAFs block direct file endpoints.
                download_obj = None
                try:
                    locator = page.get_by_role(
                        "link",
                        name=re.compile(r"download\\s+xlsx\\s+latest\\s+world\\s+official\\s+gold\\s+reserves", re.IGNORECASE),
                    )
                    if locator.count() > 0:
                        with page.expect_download(timeout=60_000) as dl:
                            locator.first.click()
                        download_obj = dl.value
                except Exception:
                    download_obj = None

                if download_obj is not None:
                    final_url = download_obj.url
                    suggested = _sanitize_filename(download_obj.suggested_filename or "wgc_gold_reserves_latest.xlsx")
                    out_path = os.path.join(outdir, suggested)
                    download_obj.save_as(out_path)
                    with open(out_path, "rb") as f:
                        payload = f.read(4096)
                    _ensure_xlsx_bytes(payload)
                    size = os.path.getsize(out_path)
                    with open(out_path, "rb") as f:
                        sha256 = hashlib.sha256(f.read()).hexdigest()
                    browser.close()
                    return DownloadResult(final_url=final_url, path=out_path, size_bytes=size, sha256=sha256)

                # Fallback: Use the browser's request context (shares cookies/session).
                headers = {"Referer": LANDING_URL, "Accept": "*/*"}
                resp = context.request.get(download_url, headers=headers, timeout=60_000)
                status = resp.status
                if status in {401, 403}:
                    raise DownloadBlockedError(
                        f"Download blocked (HTTP {status}). Try setting {AUTH_COOKIE_ENV} or use --local-xlsx."
                    )
                if _is_retryable_status(status):
                    raise RuntimeError(f"Retryable HTTP {status} for {download_url}")
                if status >= 400:
                    raise RuntimeError(f"HTTP {status} for {download_url}")

                payload = resp.body()
                _ensure_xlsx_bytes(payload)

                final_url = resp.url
                cd = resp.headers.get("content-disposition") or resp.headers.get("Content-Disposition") or ""
                parsed = urlparse(final_url)
                fallback = os.path.basename(parsed.path) or "wgc_gold_reserves_latest.xlsx"
                class _Hdr:
                    headers = {"Content-Disposition": cd}
                filename = _sanitize_filename(_filename_from_response(_Hdr(), fallback))  # type: ignore[arg-type]
                out_path = os.path.join(outdir, filename)
                with open(out_path, "wb") as f:
                    f.write(payload)
                sha256 = hashlib.sha256(payload).hexdigest()
                size = len(payload)
                browser.close()

                return DownloadResult(final_url=final_url, path=out_path, size_bytes=size, sha256=sha256)
        except Exception as e:
            last_err = e
            log.warning("Playwright download failed (attempt %d/3): %s", attempt, e)
            if attempt < 3:
                time.sleep(0.6 * (2 ** (attempt - 1)))

    raise RuntimeError("Playwright download failed after 3 attempts.") from last_err


def _normalize_columns(cols: Iterable[str]) -> list[str]:
    out = []
    for c in cols:
        s = str(c).strip().lower()
        s = s.replace("\n", " ")
        s = re.sub(r"\s+", " ", s)
        s = s.replace("%", " pct ")
        s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
        out.append(s)
    return out


def _clean_numeric_series(s: pd.Series) -> pd.Series:
    if s is None:
        return s
    if pd.api.types.is_numeric_dtype(s):
        return s
    x = s.astype(str).str.strip()
    x = x.str.replace(",", "", regex=False)
    x = x.str.replace("$", "", regex=False)
    x = x.str.replace("USD", "", case=False, regex=False)
    x = x.str.replace("%", "", regex=False)
    x = x.replace({"": None, "nan": None, "None": None})
    return pd.to_numeric(x, errors="coerce")


def _infer_holdings_as_of_from_preview(preview: pd.DataFrame) -> Optional[str]:
    try:
        text = " ".join(
            str(v)
            for v in preview.fillna("").astype(str).values.flatten().tolist()
            if v and str(v).strip()
        )
    except Exception:
        return None

    text = re.sub(r"\s+", " ", text)
    # Common patterns: "Holdings as of 31 Dec 2024", "As of: 2024-12-31"
    m = re.search(
        r"(?:holdings\s+as\s+of|as\s+of|as\s+at)\s*[:\-]?\s*([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}|\d{4})",
        text,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    return None


def _find_header_row(preview: pd.DataFrame) -> Optional[int]:
    # Find a row that likely contains headers: "country" and "tonnes" etc.
    keysets = [
        {"country", "tonnes"},
        {"country", "tonne"},
        {"country", "gold"},
        {"country", "holdings"},
    ]
    for i in range(min(30, len(preview))):
        row = preview.iloc[i].fillna("").astype(str).str.lower().tolist()
        row_text = " ".join(row)
        tokens = set(re.findall(r"[a-z]{3,}", row_text))
        for ks in keysets:
            if ks.issubset(tokens):
                return i
        if "country" in tokens and ("tonnes" in tokens or "tonne" in tokens or "holdings" in tokens):
            return i
    return None


def _parse_pdf_style_sheet(xl: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
    """
    Some WGC downloads appear as a single sheet named 'PDF' with two side-by-side tables:
      [rank, country, tonnes, % of reserves, holdings as of] + same repeated to the right.
    """
    raw = pd.read_excel(xl, sheet_name=sheet_name, header=None, engine="openpyxl")
    if raw is None or raw.empty:
        raise RuntimeError("Empty sheet")

    header_row = None
    tonnes_cols: list[int] = []

    for i in range(min(40, len(raw))):
        row = raw.iloc[i].fillna("").astype(str).str.strip().tolist()
        row_l = [str(x).lower() for x in row]
        joined = " ".join(row_l)
        if "tonnes" in joined and "holdings as of" in joined and ("% of reserves" in joined or "of reserves" in joined):
            header_row = i
            tonnes_cols = [j for j, v in enumerate(row_l) if v.strip() == "tonnes"]
            break

    if header_row is None or not tonnes_cols:
        raise RuntimeError("Could not detect PDF-style header row")

    blocks = []
    for tcol in tonnes_cols:
        blocks.append(
            {
                "rank": tcol - 2,
                "country": tcol - 1,
                "tonnes": tcol,
                "pct": tcol + 1,
                "asof": tcol + 2,
            }
        )

    rows: list[dict] = []
    for i in range(header_row + 1, len(raw)):
        for b in blocks:
            try:
                rank = raw.iat[i, b["rank"]] if 0 <= b["rank"] < raw.shape[1] else None
                country = raw.iat[i, b["country"]] if 0 <= b["country"] < raw.shape[1] else None
                tonnes = raw.iat[i, b["tonnes"]] if 0 <= b["tonnes"] < raw.shape[1] else None
                pct = raw.iat[i, b["pct"]] if 0 <= b["pct"] < raw.shape[1] else None
                asof = raw.iat[i, b["asof"]] if 0 <= b["asof"] < raw.shape[1] else None
            except Exception:
                continue

            if country is None:
                continue
            country_s = str(country).strip()
            if not country_s or country_s.lower() == "nan":
                continue

            # Rank is often numeric; use it as a guard to avoid footnotes/blank tails.
            rank_num = pd.to_numeric(pd.Series([rank]), errors="coerce").iloc[0]
            if pd.isna(rank_num):
                continue

            rows.append(
                {
                    "country_name": country_s,
                    "tonnes": tonnes,
                    "pct_of_reserves": pct,
                    "holdings_as_of": asof,
                }
            )

    out = pd.DataFrame(rows)
    if out.empty:
        raise RuntimeError("No rows parsed from PDF-style sheet")

    out["tonnes"] = _clean_numeric_series(out["tonnes"])
    out["pct_of_reserves"] = _clean_numeric_series(out["pct_of_reserves"])

    # Normalize percent: if values look like ratios (<= ~2), convert to percent.
    pct_med = out["pct_of_reserves"].dropna().median() if out["pct_of_reserves"].notna().any() else None
    if pct_med is not None and pct_med <= 2:
        out["pct_of_reserves"] = out["pct_of_reserves"] * 100.0

    # holdings_as_of normalization
    def norm_as_of(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        if isinstance(v, datetime):
            return v.date().isoformat()
        s = str(v).strip()
        if not s or s.lower() == "nan":
            return None
        try:
            dt = pd.to_datetime(s, errors="raise", utc=False)
            if pd.notna(dt):
                return dt.date().isoformat()
        except Exception:
            pass
        return s

    out["holdings_as_of"] = out["holdings_as_of"].map(norm_as_of)

    # This file variant does not include USD value; keep column for schema compatibility.
    out["value_usd"] = None
    out["source"] = "WGC"
    out["retrieved_at_utc"] = utc_now_iso()

    out = out[
        [
            "country_name",
            "tonnes",
            "pct_of_reserves",
            "value_usd",
            "holdings_as_of",
            "source",
            "retrieved_at_utc",
        ]
    ].reset_index(drop=True)

    return out


def parse_xlsx(xlsx_path: str) -> pd.DataFrame:
    log.info("Parsing XLSX: %s", xlsx_path)
    try:
        xl = pd.ExcelFile(xlsx_path, engine="openpyxl")
    except ImportError as e:
        raise RuntimeError("Missing dependency: openpyxl. Install with: pip install openpyxl") from e

    best_df: Optional[pd.DataFrame] = None
    best_score = -1
    best_as_of: Optional[str] = None

    for sheet in xl.sheet_names:
        # Special case: WGC "PDF" sheet layout (two side-by-side tables).
        if str(sheet).strip().lower() == "pdf":
            try:
                return _parse_pdf_style_sheet(xl, sheet)
            except Exception:
                pass

        try:
            preview = pd.read_excel(xl, sheet_name=sheet, header=None, nrows=30, engine="openpyxl")
        except Exception:
            continue

        header_row = _find_header_row(preview)
        as_of = _infer_holdings_as_of_from_preview(preview)

        try:
            if header_row is not None:
                df = pd.read_excel(xl, sheet_name=sheet, header=header_row, engine="openpyxl")
            else:
                df = pd.read_excel(xl, sheet_name=sheet, engine="openpyxl")
        except Exception:
            continue

        if df is None or df.empty:
            continue

        df.columns = _normalize_columns(df.columns)
        cols = set(df.columns)

        def has_any(*names: str) -> bool:
            return any(n in cols for n in names)

        # Score sheet by presence of key columns
        score = 0
        if has_any("country", "country_name", "economy", "economy_name"):
            score += 3
        if any("tonne" in c for c in cols):
            score += 3
        if any("pct" in c and "reserve" in c for c in cols) or any("percent" in c and "reserve" in c for c in cols):
            score += 1
        if any("usd" in c or ("value" in c and "usd" in c) for c in cols):
            score += 1

        if score > best_score:
            best_score = score
            best_df = df
            best_as_of = as_of

    if best_df is None or best_df.empty:
        raise RuntimeError("Could not find a usable sheet in the XLSX.")

    df = best_df.copy()
    cols = list(df.columns)

    def pick_col(predicates: list[re.Pattern]) -> Optional[str]:
        for c in cols:
            for p in predicates:
                if p.search(c):
                    return c
        return None

    country_col = pick_col([re.compile(r"^country(_name)?$"), re.compile(r"^economy(_name)?$")])
    tonnes_col = pick_col([re.compile(r"tonne"), re.compile(r"tonnes"), re.compile(r"holdings?_tonnes?")])
    pct_col = pick_col([re.compile(r"(pct|percent).*(reserve|reserves)"), re.compile(r"(reserve|reserves).*(pct|percent)")])
    value_col = pick_col([re.compile(r"value.*usd"), re.compile(r"usd"), re.compile(r"us_dollar"), re.compile(r"value")])
    asof_col = pick_col([re.compile(r"(holdings|data).*(as_of|date)"), re.compile(r"as_of"), re.compile(r"date")])

    if not country_col:
        # Sometimes it's unnamed first column
        country_col = cols[0] if cols else None

    out = pd.DataFrame()
    out["country_name"] = df[country_col] if country_col in df.columns else None
    out["tonnes"] = df[tonnes_col] if tonnes_col and tonnes_col in df.columns else None
    out["pct_of_reserves"] = df[pct_col] if pct_col and pct_col in df.columns else None
    out["value_usd"] = df[value_col] if value_col and value_col in df.columns else None

    if asof_col and asof_col in df.columns:
        out["holdings_as_of"] = df[asof_col]
    else:
        out["holdings_as_of"] = best_as_of

    out["country_name"] = out["country_name"].astype(str).str.strip()
    out = out[out["country_name"].notna() & (out["country_name"] != "")].copy()

    out["tonnes"] = _clean_numeric_series(out["tonnes"])
    out["pct_of_reserves"] = _clean_numeric_series(out["pct_of_reserves"])
    out["value_usd"] = _clean_numeric_series(out["value_usd"])

    # holdings_as_of normalization
    def norm_as_of(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        if isinstance(v, (datetime,)):
            return v.date().isoformat()
        s = str(v).strip()
        if not s or s.lower() == "nan":
            return None
        try:
            dt = pd.to_datetime(s, errors="raise", utc=False)
            if pd.notna(dt):
                return dt.date().isoformat()
        except Exception:
            pass
        return s

    out["holdings_as_of"] = out["holdings_as_of"].map(norm_as_of)

    out["source"] = "WGC"
    out["retrieved_at_utc"] = utc_now_iso()

    # Drop obvious totals/blank rows
    out = out[~out["country_name"].str.lower().str.contains(r"^total$", na=False)]

    # Ensure column order
    out = out[
        [
            "country_name",
            "tonnes",
            "pct_of_reserves",
            "value_usd",
            "holdings_as_of",
            "source",
            "retrieved_at_utc",
        ]
    ]

    return out.reset_index(drop=True)


def export_outputs(df: pd.DataFrame, outdir: str, *, write_parquet: bool = True) -> tuple[str, Optional[str]]:
    os.makedirs(outdir, exist_ok=True)
    csv_path = os.path.join(outdir, "wgc_gold_reserves_latest.csv")
    parquet_path = os.path.join(outdir, "wgc_gold_reserves_latest.parquet") if write_parquet else None

    log.info("Writing CSV: %s", csv_path)
    df.to_csv(csv_path, index=False, float_format="%.6f", quoting=csv.QUOTE_MINIMAL)

    if parquet_path:
        try:
            log.info("Writing Parquet: %s", parquet_path)
            df.to_parquet(parquet_path, index=False)
        except Exception as e:
            log.warning("Parquet skipped (install pyarrow or fastparquet). Error: %s", e)
            parquet_path = None

    return csv_path, parquet_path


def _print_top10(df: pd.DataFrame) -> None:
    if "tonnes" not in df.columns:
        return
    if df["tonnes"].isna().all():
        return
    top = df.sort_values("tonnes", ascending=False).head(10)
    log.info("Top 10 by tonnes:")
    for i, row in enumerate(top.itertuples(index=False), start=1):
        log.info("  %2d) %-30s %s", i, getattr(row, "country_name"), getattr(row, "tonnes"))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Download and parse WGC gold reserves XLSX.")
    ap.add_argument("--outdir", default=DEFAULT_OUTDIR, help=f"Output directory (default: {DEFAULT_OUTDIR})")
    ap.add_argument("--keep-raw", default=True, action=argparse.BooleanOptionalAction, help="Keep downloaded XLSX (default: true)")
    ap.add_argument("--local-xlsx", default=None, help="Use local XLSX path instead of downloading")
    ap.add_argument("--no-parquet", action="store_true", help="Disable parquet output")
    ap.add_argument(
        "--mode",
        choices=["requests", "playwright"],
        default="requests",
        help="Download mode: requests (default) or playwright (browser automation).",
    )
    ap.add_argument(
        "--headful",
        action="store_true",
        help="Run Playwright in headed mode (debug). Default is headless.",
    )
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    outdir = args.outdir
    os.makedirs(outdir, exist_ok=True)

    session = requests.Session()
    session.headers.update({"Accept-Language": "en-US,en;q=0.9"})

    xlsx_path: Optional[str] = None
    dl_info: Optional[DownloadResult] = None

    if args.local_xlsx:
        xlsx_path = args.local_xlsx
        if not os.path.exists(xlsx_path):
            log.error("Local XLSX not found: %s", xlsx_path)
            return 2
        log.info("Using local XLSX: %s", xlsx_path)
        try:
            log.info("File size: %s bytes", os.path.getsize(xlsx_path))
        except Exception:
            pass
    else:
        html = fetch_html(session, LANDING_URL)
        download_url = extract_download_url(LANDING_URL, html)
        if args.mode == "playwright":
            dl_info = _download_via_playwright(download_url, outdir, headless=not args.headful)
        else:
            dl_info = download_file(session, download_url, outdir)
        xlsx_path = dl_info.path

        log.info("Final download URL: %s", dl_info.final_url)
        log.info("File size: %s bytes", dl_info.size_bytes)
        log.info("SHA256: %s", dl_info.sha256)

        if not args.keep_raw:
            # We'll delete after parsing.
            pass

    df = parse_xlsx(xlsx_path)
    log.info("Parsed rows: %d", len(df))
    _print_top10(df)

    csv_path, parquet_path = export_outputs(df, outdir, write_parquet=not args.no_parquet)

    log.info("Wrote CSV: %s", csv_path)
    if parquet_path:
        log.info("Wrote Parquet: %s", parquet_path)

    if dl_info and (not args.keep_raw):
        try:
            os.remove(dl_info.path)
            log.info("Deleted raw XLSX (keep-raw disabled): %s", dl_info.path)
        except Exception as e:
            log.warning("Could not delete raw XLSX: %s", e)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except DownloadBlockedError as e:
        log.error(str(e))
        raise SystemExit(3)
