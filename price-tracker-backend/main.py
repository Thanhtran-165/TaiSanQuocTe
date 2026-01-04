"""
Price Tracker FastAPI Backend
REST API for Gold and Silver price tracking
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Optional
import sys
import os
import sqlite3
import csv
import io
import requests
import subprocess
import re
import time

# Add ui directory to path to import data_fetcher
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
ui_dir = os.path.join(parent_dir, 'ui')
sys.path.insert(0, ui_dir)

from data_fetcher import PriceDataFetcher

# Initialize FastAPI app
app = FastAPI(
    title="Price Tracker API",
    description="Gold and Silver price tracking API for Vietnam and International markets",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",  # Added for current session
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize data fetcher
fetcher = PriceDataFetcher()

HISTORY_DB_PATH = os.path.join(ui_dir, "price_history.db")
RESERVES_CSV_PATH = os.path.join(parent_dir, "Du_tru", "reserves_gold_by_country_year.csv")
WGC_OUTDIR = os.path.join(parent_dir, "data_wgc")
WGC_CSV_PATH = os.path.join(WGC_OUTDIR, "wgc_gold_reserves_latest.csv")
WGC_COOKIE_FILE_DEFAULT = os.path.join(parent_dir, ".secrets", "wgc_auth_cookie.txt")

_TOKEN_CACHE: Optional[dict] = None
_TOKEN_LAST_FETCH: Optional[datetime] = None
_RESERVES_CACHE: Optional[dict] = None
_WGC_CACHE: Optional[dict] = None
_WGC_CACHE_MTIME: Optional[float] = None
_GOLD_SPOT_CACHE: Optional[dict] = None
_GOLD_SPOT_LAST_FETCH: Optional[datetime] = None


def _connect_history_db() -> sqlite3.Connection:
    conn = sqlite3.connect(HISTORY_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    _ensure_price_snapshots_columns(conn)
    return conn


def _rows_to_dicts(rows):
    return [dict(r) for r in rows]

def _ensure_price_snapshots_columns(conn: sqlite3.Connection) -> None:
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(price_snapshots)").fetchall()}
        expected = [
            ("paxg_usd_oz", "REAL"),
            ("paxg_source", "TEXT"),
            ("xaut_usd_oz", "REAL"),
            ("xaut_source", "TEXT"),
        ]
        for name, sql_type in expected:
            if name not in cols:
                conn.execute(f"ALTER TABLE price_snapshots ADD COLUMN {name} {sql_type}")
        conn.commit()
    except Exception:
        return

def _to_float(value):
    try:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        s = str(value).strip()
        # Handle common formatted numbers like "2,823,000"
        s = s.replace(",", "")
        return float(s)
    except Exception:
        return None

def _load_reserves_dataset() -> dict:
    """
    Load World Bank reserves dataset (gold inferred + non-gold) from CSV and cache in memory.

    Returns:
      {
        "global_min_year": int,
        "global_max_year": int,
        "countries": {
           "US": {
              "iso2": "US",
              "country_name": "United States",
              "min_year": 1960,
              "max_year": 2024,
              "series": [{"year": 1960, "total_reserves_usd": ..., "non_gold_reserves_usd": ..., "gold_value_usd_inferred": ..., "quality_flag": "OK"}, ...]
           },
           ...
        }
      }
    """
    global _RESERVES_CACHE
    if _RESERVES_CACHE is not None:
        return _RESERVES_CACHE

    countries: dict[str, dict] = {}
    global_min_year: Optional[int] = None
    global_max_year: Optional[int] = None

    if not os.path.exists(RESERVES_CSV_PATH):
        _RESERVES_CACHE = {"global_min_year": None, "global_max_year": None, "countries": {}}
        return _RESERVES_CACHE

    with open(RESERVES_CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            iso2 = (row.get("iso2") or "").strip().upper()
            name = (row.get("country_name") or "").strip()
            year_raw = row.get("year")
            try:
                year = int(year_raw) if year_raw is not None else None
            except Exception:
                year = None
            if not iso2 or year is None:
                continue

            total_usd = _to_float(row.get("total_reserves_usd"))
            non_gold_usd = _to_float(row.get("non_gold_reserves_usd"))
            gold_usd = _to_float(row.get("gold_value_usd_inferred"))
            qf = (row.get("quality_flag") or "").strip() or None

            global_min_year = year if global_min_year is None else min(global_min_year, year)
            global_max_year = year if global_max_year is None else max(global_max_year, year)

            entry = countries.get(iso2)
            if entry is None:
                entry = {
                    "iso2": iso2,
                    "country_name": name or iso2,
                    "min_year": year,
                    "max_year": year,
                    "series": [],
                }
                countries[iso2] = entry

            entry["min_year"] = min(entry["min_year"], year)
            entry["max_year"] = max(entry["max_year"], year)
            entry["series"].append(
                {
                    "year": year,
                    "total_reserves_usd": total_usd,
                    "non_gold_reserves_usd": non_gold_usd,
                    "gold_value_usd_inferred": gold_usd,
                    "quality_flag": qf,
                }
            )

    for iso2, entry in countries.items():
        entry["series"].sort(key=lambda r: r["year"])

    _RESERVES_CACHE = {
        "global_min_year": global_min_year,
        "global_max_year": global_max_year,
        "countries": countries,
    }
    return _RESERVES_CACHE

def _reserves_kind_value(row: dict, kind: str) -> Optional[float]:
    if kind == "gold":
        return row.get("gold_value_usd_inferred")
    if kind == "non_gold":
        return row.get("non_gold_reserves_usd")
    if kind == "total":
        return row.get("total_reserves_usd")
    return None

def _norm_country_name(name: str) -> str:
    s = (name or "").lower().strip()
    s = s.replace("&", " and ")
    s = re.sub(r"[\(\)\[\]\.,'’]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # Some common normalizations
    s = s.replace("russian federation", "russia")
    s = s.replace("republic of korea", "korea")
    s = s.replace("korea, rep", "korea")
    s = s.replace("iran, islamic rep", "iran")
    s = s.replace("venezuela, rb", "venezuela")
    s = s.replace("egypt, arab rep", "egypt")
    s = s.replace("slovak republic", "slovakia")
    s = s.replace("turkiye", "turkey")
    return s

def _country_token_set(name: str) -> set[str]:
    s = _norm_country_name(name)
    tokens = {t for t in s.split(" ") if t and t not in {"the", "of", "and", "rep", "republic"}}
    return tokens

def _build_wdi_country_index() -> list[tuple[str, str, set[str]]]:
    ds = _load_reserves_dataset()
    out: list[tuple[str, str, set[str]]] = []
    for iso2, entry in (ds.get("countries") or {}).items():
        cname = entry.get("country_name") or iso2
        out.append((iso2, cname, _country_token_set(cname)))
    return out

def _map_country_to_iso2(name: str) -> Optional[str]:
    ds = _load_reserves_dataset()
    countries = ds.get("countries") or {}
    if not countries:
        return None

    target_norm = _norm_country_name(name)
    for iso2, entry in countries.items():
        if _norm_country_name(entry.get("country_name") or "") == target_norm:
            return iso2

    target_tokens = _country_token_set(name)
    if not target_tokens:
        return None

    best_iso2 = None
    best_score = 0.0
    for iso2, cname, tokens in _build_wdi_country_index():
        if not tokens:
            continue
        inter = len(tokens & target_tokens)
        union = len(tokens | target_tokens)
        score = (inter / union) if union else 0.0
        if score > best_score:
            best_score = score
            best_iso2 = iso2

    return best_iso2 if best_score >= 0.6 else None

def _load_wgc_latest() -> dict:
    """
    Load latest WGC gold reserves snapshot from CSV.
    Returns cached result when possible.
    """
    global _WGC_CACHE, _WGC_CACHE_MTIME

    if not os.path.exists(WGC_CSV_PATH):
        _WGC_CACHE = {"meta": None, "rows": []}
        _WGC_CACHE_MTIME = None
        return _WGC_CACHE

    try:
        mtime = os.path.getmtime(WGC_CSV_PATH)
    except Exception:
        mtime = None

    if _WGC_CACHE is not None and _WGC_CACHE_MTIME is not None and mtime is not None and abs(_WGC_CACHE_MTIME - mtime) < 1e-6:
        return _WGC_CACHE

    rows: list[dict] = []
    retrieved_at_utc = None
    holdings_as_of_max: Optional[str] = None
    with open(WGC_CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            country = (r.get("country_name") or "").strip()
            if not country:
                continue
            tonnes = _to_float(r.get("tonnes"))
            pct = _to_float(r.get("pct_of_reserves"))
            value = _to_float(r.get("value_usd"))
            retrieved_at_utc = retrieved_at_utc or (r.get("retrieved_at_utc") or None)
            row_asof = (r.get("holdings_as_of") or "").strip() or None
            if row_asof:
                if holdings_as_of_max is None or row_asof > holdings_as_of_max:
                    holdings_as_of_max = row_asof
            iso2 = _map_country_to_iso2(country)
            rows.append(
                {
                    "country_name": country,
                    "iso2": iso2,
                    "tonnes": tonnes,
                    "pct_of_reserves": pct,
                    "value_usd": value,
                    "holdings_as_of": r.get("holdings_as_of") or None,
                    "source": "WGC",
                    "retrieved_at_utc": r.get("retrieved_at_utc") or None,
                }
            )

    _WGC_CACHE = {"meta": {"holdings_as_of": holdings_as_of_max, "retrieved_at_utc": retrieved_at_utc}, "rows": rows}
    _WGC_CACHE_MTIME = mtime
    return _WGC_CACHE

def _get_wgc_auth_cookie() -> Optional[str]:
    val = os.environ.get("WGC_AUTH_COOKIE")
    if val:
        return val.strip() or None
    path = os.environ.get("WGC_AUTH_COOKIE_FILE") or WGC_COOKIE_FILE_DEFAULT
    try:
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                v = (f.read() or "").strip()
                return v or None
    except Exception:
        return None
    return None

def _refresh_wgc_dataset() -> dict:
    """
    Refresh WGC dataset by running the downloader script using Playwright mode.
    """
    global _WGC_CACHE, _WGC_CACHE_MTIME
    os.makedirs(WGC_OUTDIR, exist_ok=True)
    script_path = os.path.join(parent_dir, "download_wgc_gold_reserves.py")
    if not os.path.exists(script_path):
        raise RuntimeError("Downloader script not found: download_wgc_gold_reserves.py")

    python_bin = os.environ.get("WGC_PYTHON") or sys.executable
    cookie = _get_wgc_auth_cookie()
    if not cookie:
        raise RuntimeError("Missing WGC auth cookie. Set env `WGC_AUTH_COOKIE` or put it in `.secrets/wgc_auth_cookie.txt`.")
    cmd = [
        python_bin,
        script_path,
        "--mode",
        "playwright",
        "--outdir",
        WGC_OUTDIR,
        "--no-parquet",
    ]
    env = os.environ.copy()
    env["WGC_AUTH_COOKIE"] = cookie
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if proc.returncode != 0:
        raise RuntimeError(f"WGC refresh failed (code={proc.returncode}).\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")

    _WGC_CACHE = None
    _WGC_CACHE_MTIME = None
    return _load_wgc_latest()

def _ensure_wgc_dataset(max_age_hours: int = 24 * 14) -> dict:
    """
    Ensure we have a reasonably fresh WGC snapshot (default: 14 days).
    If missing or stale, attempt a refresh using Playwright.
    """
    if not os.path.exists(WGC_CSV_PATH):
        return _refresh_wgc_dataset()
    try:
        mtime = os.path.getmtime(WGC_CSV_PATH)
        age_hours = (time.time() - mtime) / 3600.0
        if age_hours > max_age_hours:
            return _refresh_wgc_dataset()
    except Exception:
        pass
    return _load_wgc_latest()

def _get_gold_spot_usd_oz() -> Optional[dict]:
    """
    Get current international gold price in USD/oz with a short in-process cache.
    Uses the existing fetcher (international prices only).
    """
    global _GOLD_SPOT_CACHE, _GOLD_SPOT_LAST_FETCH
    now = datetime.now()
    try:
        if _GOLD_SPOT_LAST_FETCH and _GOLD_SPOT_CACHE and (now - _GOLD_SPOT_LAST_FETCH).total_seconds() < 300:
            return dict(_GOLD_SPOT_CACHE)
    except Exception:
        pass

    try:
        intl = fetcher.fetch_international_prices() or {}
        gold = intl.get("gold") if isinstance(intl, dict) else None
        if not isinstance(gold, dict):
            return None
        price = gold.get("price")
        if not isinstance(price, (int, float)) or price <= 0:
            return None
        out = {
            "price_usd_oz": float(price),
            "source": gold.get("source") or None,
            "retrieved_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        }
        _GOLD_SPOT_CACHE = out
        _GOLD_SPOT_LAST_FETCH = now
        return dict(out)
    except Exception:
        return None

def _tonnes_to_troy_oz(tonnes: float) -> float:
    # 1 metric tonne = 1,000,000 g; 1 troy oz = 31.1034768 g
    return tonnes * (1_000_000.0 / 31.1034768)

def _maybe_override_vn_prices_with_sell(data: dict) -> dict:
    """
    Ensure UI shows VN *sell* prices (giá bán) and spreads are computed using those.
    This is a compatibility layer in case the underlying fetcher still uses buy prices.
    """
    if not isinstance(data, dict):
        return data

    # Extract current values
    usd_vnd = data.get("usd_vnd")
    intl_gold = data.get("intl_gold") or {}
    intl_silver = data.get("intl_silver") or {}
    intl_gold_price = intl_gold.get("price") if isinstance(intl_gold, dict) else None
    intl_silver_price = intl_silver.get("price") if isinstance(intl_silver, dict) else None

    # 1) SJC sell price from `sjc_gold_all`
    sjc_sell = None
    sjc_all = data.get("sjc_gold_all")
    if isinstance(sjc_all, list):
        for item in sjc_all:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "")
            if "SJC" not in name.upper():
                continue
            sjc_sell = _to_float(item.get("sell_price") or item.get("sell"))
            if sjc_sell is not None:
                break

    if sjc_sell is not None:
        sjc_gold = data.get("sjc_gold") or {}
        if isinstance(sjc_gold, dict):
            sjc_gold["price"] = sjc_sell
            sjc_gold["unit"] = "VND/lượng"
            data["sjc_gold"] = sjc_gold

    # 2) PhuQuy silver sell price from `phuquy_silver_all.prices`
    pq_sell = None
    pq_unit = "VND/lượng"
    pq_all = data.get("phuquy_silver_all") or {}
    prices = pq_all.get("prices") if isinstance(pq_all, dict) else None
    if isinstance(prices, list):
        def _norm(s: str) -> str:
            return "".join(ch for ch in s.upper() if ch.isalnum() or ch.isspace()).strip()

        target = _norm("BẠC MIẾNG PHÚ QUÝ 999 1 LƯỢNG")
        best = None
        for item in prices:
            if not isinstance(item, dict):
                continue
            name = item.get("type") or item.get("product") or ""
            n = _norm(str(name))
            if target in n:
                best = item
                break
        if best is None and prices:
            best = prices[0] if isinstance(prices[0], dict) else None

        if isinstance(best, dict):
            raw_unit = str(best.get("unit") or "")
            pq_sell = _to_float(best.get("sell_price") or best.get("sell"))
            # Convert VND/kg -> VND/lượng if needed
            if pq_sell is not None and "KG" in raw_unit.upper():
                kg_to_luong = 1000.0 / 37.5
                pq_sell = pq_sell / kg_to_luong
            pq_unit = "VND/lượng"

    if pq_sell is not None:
        pq = data.get("phuquy_silver") or {}
        if isinstance(pq, dict):
            pq["price"] = pq_sell
            pq["unit"] = pq_unit
            data["phuquy_silver"] = pq

    # 3) Recompute spreads using sell prices (if possible)
    luong_to_oz = 37.5 / 31.1035
    recomputed_gold_spread = None
    recomputed_silver_spread = None
    if isinstance(usd_vnd, (int, float)) and isinstance(intl_gold_price, (int, float)) and isinstance(sjc_sell, (int, float)):
        intl_per_luong = intl_gold_price * usd_vnd * luong_to_oz
        spread_vnd = sjc_sell - intl_per_luong
        spread_percent = (spread_vnd / intl_per_luong) * 100 if intl_per_luong else None
        recomputed_gold_spread = {
            "spread_vnd": round(spread_vnd, 2),
            "spread_percent": round(spread_percent, 2) if spread_percent is not None else None,
            "intl_in_vnd": round(intl_gold_price * usd_vnd, 2),
            "intl_per_luong": round(intl_per_luong, 2),
        }
        data["gold_spread"] = recomputed_gold_spread

    if isinstance(usd_vnd, (int, float)) and isinstance(intl_silver_price, (int, float)) and isinstance(pq_sell, (int, float)):
        intl_per_luong = intl_silver_price * usd_vnd * luong_to_oz
        spread_vnd = pq_sell - intl_per_luong
        spread_percent = (spread_vnd / intl_per_luong) * 100 if intl_per_luong else None
        recomputed_silver_spread = {
            "spread_vnd": round(spread_vnd, 2),
            "spread_percent": round(spread_percent, 2) if spread_percent is not None else None,
            "intl_in_vnd": round(intl_silver_price * usd_vnd, 2),
            "intl_per_luong": round(intl_per_luong, 2),
            "unit": "VND/lượng",
        }
        data["silver_spread"] = recomputed_silver_spread

    if sjc_sell is not None or pq_sell is not None:
        _persist_vn_sell_to_latest_snapshot(sjc_sell, pq_sell, recomputed_gold_spread, recomputed_silver_spread)

    return data

def _fetch_tokenized_gold_today() -> dict:
    """
    Fetch tokenized gold prices (PAXG, XAUT) in USD/oz.
    Uses CryptoCompare, with a short in-process cache.
    """
    global _TOKEN_CACHE, _TOKEN_LAST_FETCH
    now = datetime.now()
    try:
        if _TOKEN_LAST_FETCH and _TOKEN_CACHE and (now - _TOKEN_LAST_FETCH).total_seconds() < 300:
            return dict(_TOKEN_CACHE)
    except Exception:
        pass

    url = "https://min-api.cryptocompare.com/data/pricemultifull"
    params = {"fsyms": "PAXG,XAUT", "tsyms": "USD"}
    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        payload = resp.json()
        raw = (payload.get("RAW") or {})

        def _one(sym: str):
            usd = ((raw.get(sym) or {}).get("USD") or {})
            price = usd.get("PRICE")
            change = usd.get("CHANGE24HOUR")
            change_pct = usd.get("CHANGEPCT24HOUR")
            if not isinstance(price, (int, float)):
                return None
            return {
                "price": round(float(price), 2),
                "change": round(float(change), 2) if isinstance(change, (int, float)) else None,
                "change_percent": round(float(change_pct), 2) if isinstance(change_pct, (int, float)) else None,
                "unit": "USD/oz",
                "source": "CryptoCompare",
            }

        out = {"paxg": _one("PAXG"), "xaut": _one("XAUT")}
        _TOKEN_CACHE = out
        _TOKEN_LAST_FETCH = now
        return out
    except Exception:
        return {"paxg": None, "xaut": None}

def _read_latest_tokenized_from_db() -> dict:
    try:
        conn = _connect_history_db()
        try:
            row = conn.execute(
                """
                SELECT paxg_usd_oz, paxg_source, xaut_usd_oz, xaut_source
                FROM price_snapshots
                WHERE paxg_usd_oz IS NOT NULL OR xaut_usd_oz IS NOT NULL
                ORDER BY ts DESC
                LIMIT 1
                """
            ).fetchone()
            if not row:
                return {"paxg": None, "xaut": None}
            paxg = row["paxg_usd_oz"]
            xaut = row["xaut_usd_oz"]
            return {
                "paxg": {
                    "price": float(paxg) if paxg is not None else None,
                    "change": None,
                    "change_percent": None,
                    "unit": "USD/oz",
                    "source": row["paxg_source"] or "CryptoCompare",
                }
                if paxg is not None
                else None,
                "xaut": {
                    "price": float(xaut) if xaut is not None else None,
                    "change": None,
                    "change_percent": None,
                    "unit": "USD/oz",
                    "source": row["xaut_source"] or "CryptoCompare",
                }
                if xaut is not None
                else None,
            }
        finally:
            conn.close()
    except Exception:
        return {"paxg": None, "xaut": None}

def _persist_tokenized_to_latest_snapshot(tokens: dict) -> None:
    paxg = (tokens or {}).get("paxg") or {}
    xaut = (tokens or {}).get("xaut") or {}
    try:
        conn = _connect_history_db()
        try:
            latest = conn.execute("SELECT ts FROM price_snapshots ORDER BY ts DESC LIMIT 1").fetchone()
            if not latest:
                return
            ts = latest["ts"]
            conn.execute(
                """
                UPDATE price_snapshots
                SET
                  paxg_usd_oz = COALESCE(?, paxg_usd_oz),
                  paxg_source = COALESCE(?, paxg_source),
                  xaut_usd_oz = COALESCE(?, xaut_usd_oz),
                  xaut_source = COALESCE(?, xaut_source)
                WHERE ts = ?
                """,
                (
                    paxg.get("price") if isinstance(paxg, dict) else None,
                    paxg.get("source") if isinstance(paxg, dict) else None,
                    xaut.get("price") if isinstance(xaut, dict) else None,
                    xaut.get("source") if isinstance(xaut, dict) else None,
                    ts,
                ),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        return

def _persist_vn_sell_to_latest_snapshot(
    sjc_sell: Optional[float],
    phuquy_sell: Optional[float],
    gold_spread: Optional[dict],
    silver_spread: Optional[dict],
) -> None:
    """
    Persist sell-based VN prices/spreads to the latest snapshot row so History matches Today.
    """
    try:
        conn = _connect_history_db()
        try:
            latest = conn.execute("SELECT ts FROM price_snapshots ORDER BY ts DESC LIMIT 1").fetchone()
            if not latest:
                return
            ts = latest["ts"]

            gold_spread = gold_spread or {}
            silver_spread = silver_spread or {}

            conn.execute(
                """
                UPDATE price_snapshots
                SET
                  sjc_vnd_luong = COALESCE(?, sjc_vnd_luong),
                  phuquy_silver_vnd = COALESCE(?, phuquy_silver_vnd),
                  phuquy_silver_unit = COALESCE(?, phuquy_silver_unit),
                  gold_spread_vnd = COALESCE(?, gold_spread_vnd),
                  gold_spread_percent = COALESCE(?, gold_spread_percent),
                  gold_intl_vnd_per_luong = COALESCE(?, gold_intl_vnd_per_luong),
                  silver_spread_vnd = COALESCE(?, silver_spread_vnd),
                  silver_spread_percent = COALESCE(?, silver_spread_percent),
                  silver_intl_vnd_per_unit = COALESCE(?, silver_intl_vnd_per_unit),
                  silver_spread_unit = COALESCE(?, silver_spread_unit)
                WHERE ts = ?
                """,
                (
                    sjc_sell,
                    phuquy_sell,
                    "VND/lượng" if phuquy_sell is not None else None,
                    gold_spread.get("spread_vnd"),
                    gold_spread.get("spread_percent"),
                    gold_spread.get("intl_per_luong"),
                    silver_spread.get("spread_vnd"),
                    silver_spread.get("spread_percent"),
                    silver_spread.get("intl_per_luong"),
                    "VND/lượng" if phuquy_sell is not None else None,
                    ts,
                ),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        return


def _normalize_phuquy_to_luong(row: dict) -> dict:
    # Convert VND/kg -> VND/lượng for consistent display
    unit = (row.get("unit") or "").strip().lower()
    buy = _to_float(row.get("buy_price"))
    sell = _to_float(row.get("sell_price"))
    kg_to_luong = 1000.0 / 37.5  # 26.666666...
    if "kg" in unit:
        if buy is not None:
            row["buy_price"] = buy / kg_to_luong
        if sell is not None:
            row["sell_price"] = sell / kg_to_luong
    row["unit"] = "VND/lượng"
    return row

def _normalize_stooq_today_payload(data: dict) -> dict:
    """
    Normalize Stooq SI.F values to USD/oz (Stooq commonly returns SI.F in cents).
    Also recompute silver spread to keep UI consistent.
    """
    try:
        intl_silver = (data or {}).get("intl_silver") or {}
        if not isinstance(intl_silver, dict):
            return data
        src = str(intl_silver.get("source") or "")
        price = intl_silver.get("price")
        if "STOOQ" not in src.upper() or not isinstance(price, (int, float)) or price <= 1000:
            return data

        scale = 0.01
        for k in ["price", "change", "high", "low"]:
            v = intl_silver.get(k)
            if isinstance(v, (int, float)):
                intl_silver[k] = round(v * scale, 2)
        data["intl_silver"] = intl_silver

        usd_vnd = (data or {}).get("usd_vnd")
        phuquy = (data or {}).get("phuquy_silver") or {}
        phuquy_price = phuquy.get("price")
        if isinstance(usd_vnd, (int, float)) and isinstance(phuquy_price, (int, float)):
            intl_price = intl_silver.get("price")
            if isinstance(intl_price, (int, float)) and intl_price > 0:
                luong_to_oz = 37.5 / 31.1035
                intl_per_luong = intl_price * usd_vnd * luong_to_oz
                spread_vnd = phuquy_price - intl_per_luong
                spread_percent = (spread_vnd / intl_per_luong) * 100 if intl_per_luong else None
                silver_spread = (data or {}).get("silver_spread") or {}
                silver_spread.update(
                    {
                        "spread_vnd": round(spread_vnd, 2),
                        "spread_percent": round(spread_percent, 2) if spread_percent is not None else None,
                        "intl_in_vnd": round(intl_price * usd_vnd, 2),
                        "intl_per_luong": round(intl_per_luong, 2),
                        "unit": "VND/lượng",
                    }
                )
                data["silver_spread"] = silver_spread
    except Exception:
        return data
    return data

def _ensure_meta_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )


def _get_meta(conn: sqlite3.Connection, key: str) -> Optional[str]:
    _ensure_meta_table(conn)
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


def _set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    _ensure_meta_table(conn)
    conn.execute("INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)", (key, value))


def _fetch_stooq_daily_close(symbol: str, days: int = 730) -> list[tuple[str, float]]:
    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    reader = csv.DictReader(io.StringIO(resp.text))
    rows: list[tuple[str, float]] = []
    for r in reader:
        d = (r.get("Date") or "").strip()
        c = (r.get("Close") or "").strip()
        if not d or not c:
            continue
        try:
            rows.append((d, float(c)))
        except Exception:
            continue
    if len(rows) > days:
        rows = rows[-days:]
    return rows


def _ensure_intl_history_backfill(days: int = 730) -> None:
    """
    Backfill 2y of XAU/XAG daily closes into `price_snapshots` (ts=YYYY-MM-DDT00:00:00).
    This allows charts/ratio to work immediately, then daily updates append new points.
    """
    conn = _connect_history_db()
    try:
        key = "intl_stooq_backfill_v1"
        if _get_meta(conn, key) == "1":
            return

        # If we already have enough daily points for both metals, skip.
        existing = conn.execute(
            """
            SELECT
              SUM(CASE WHEN intl_gold_usd_oz IS NOT NULL THEN 1 ELSE 0 END) AS gold_n,
              SUM(CASE WHEN intl_silver_usd_oz IS NOT NULL THEN 1 ELSE 0 END) AS silver_n
            FROM (
              SELECT substr(ts, 1, 10) AS day,
                     MAX(intl_gold_usd_oz) AS intl_gold_usd_oz,
                     MAX(intl_silver_usd_oz) AS intl_silver_usd_oz
              FROM price_snapshots
              GROUP BY day
            )
            """
        ).fetchone()
        if existing and existing[0] and existing[1] and existing[0] >= days and existing[1] >= days:
            _set_meta(conn, key, "1")
            conn.commit()
            return

        gold = _fetch_stooq_daily_close("xauusd", days=days)
        silver = _fetch_stooq_daily_close("xagusd", days=days)
        gold_by_day = {d: p for d, p in gold}
        silver_by_day = {d: p for d, p in silver}
        days_union = sorted(set(gold_by_day.keys()) | set(silver_by_day.keys()))

        created_at = datetime.now().isoformat()
        rows = []
        for day in days_union:
            ts = f"{day}T00:00:00"
            rows.append(
                (
                    ts,
                    created_at,
                    gold_by_day.get(day),
                    "stooq",
                    silver_by_day.get(day),
                    "stooq",
                )
            )

        conn.executemany(
            """
            INSERT OR IGNORE INTO price_snapshots
              (ts, created_at, intl_gold_usd_oz, intl_gold_source, intl_silver_usd_oz, intl_silver_source)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        _set_meta(conn, key, "1")
        conn.commit()
    finally:
        conn.close()

def _fetch_cryptocompare_histoday(fsym: str, days: int = 730) -> list[tuple[str, float]]:
    url = "https://min-api.cryptocompare.com/data/v2/histoday"
    params = {"fsym": fsym, "tsym": "USD", "limit": days}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("Response") != "Success":
        raise RuntimeError(payload.get("Message") or "cryptocompare histoday failed")
    out: list[tuple[str, float]] = []
    for row in (payload.get("Data") or {}).get("Data") or []:
        ts = row.get("time")
        close = row.get("close")
        if ts is None or close is None:
            continue
        try:
            day = datetime.fromtimestamp(int(ts), tz=None).date().isoformat()
            out.append((day, float(close)))
        except Exception:
            continue
    if len(out) > days + 1:
        out = out[-(days + 1) :]
    return out


def _ensure_tokenized_gold_backfill(days: int = 730) -> None:
    conn = _connect_history_db()
    try:
        key = "token_gold_backfill_v1"
        if _get_meta(conn, key) == "1":
            return

        paxg = _fetch_cryptocompare_histoday("PAXG", days=days)
        xaut = _fetch_cryptocompare_histoday("XAUT", days=days)
        paxg_by_day = {d: p for d, p in paxg}
        xaut_by_day = {d: p for d, p in xaut}
        days_union = sorted(set(paxg_by_day.keys()) | set(xaut_by_day.keys()))

        created_at = datetime.now().isoformat()
        rows = []
        for day in days_union:
            ts = f"{day}T00:00:00"
            rows.append(
                (
                    ts,
                    created_at,
                    paxg_by_day.get(day),
                    "CryptoCompare",
                    xaut_by_day.get(day),
                    "CryptoCompare",
                )
            )

        conn.executemany(
            """
            INSERT INTO price_snapshots
              (ts, created_at, paxg_usd_oz, paxg_source, xaut_usd_oz, xaut_source)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(ts) DO UPDATE SET
              paxg_usd_oz = COALESCE(excluded.paxg_usd_oz, paxg_usd_oz),
              paxg_source = COALESCE(excluded.paxg_source, paxg_source),
              xaut_usd_oz = COALESCE(excluded.xaut_usd_oz, xaut_usd_oz),
              xaut_source = COALESCE(excluded.xaut_source, xaut_source)
            """,
            rows,
        )
        _set_meta(conn, key, "1")
        conn.commit()
    finally:
        conn.close()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Price Tracker API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/prices/today")
async def get_today_prices():
    """
    Get today's prices for all metals
    Returns SJC gold, Phu Quy silver, and international prices
    """
    try:
        # Ensure we have intl history available for charts/ratio.
        try:
            _ensure_intl_history_backfill(days=730)
            _ensure_tokenized_gold_backfill(days=730)
        except Exception:
            pass
        data = fetcher.get_formatted_data()
        # Back-compat: if the scraper/fetcher doesn't provide tokenized assets yet,
        # inject PAXG/XAUT from CryptoCompare (or DB fallback) so UI cards never show N/A.
        if not isinstance(data, dict):
            data = {}

        tokens = _fetch_tokenized_gold_today()
        if not (tokens.get("paxg") or tokens.get("xaut")):
            tokens = _read_latest_tokenized_from_db()

        if isinstance(tokens.get("paxg"), dict) and (not isinstance(data.get("paxg"), dict) or data.get("paxg") is None):
            data["paxg"] = tokens["paxg"]
        if isinstance(tokens.get("xaut"), dict) and (not isinstance(data.get("xaut"), dict) or data.get("xaut") is None):
            data["xaut"] = tokens["xaut"]

        # Persist to the latest snapshot row if the underlying fetcher didn't.
        if tokens.get("paxg") or tokens.get("xaut"):
            _persist_tokenized_to_latest_snapshot(tokens)

        # Ensure VN prices use sell price and recompute spreads.
        data = _maybe_override_vn_prices_with_sell(data)

        data = _normalize_stooq_today_payload(data)
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reserves/top")
async def get_reserves_top(
    kind: str = Query(default="gold", description="gold | non_gold | total"),
    year: Optional[int] = Query(default=None, description="Year (defaults to latest available)"),
    limit: int = Query(default=20, ge=1, le=200),
):
    """
    Top N reserves holders for a given year.
    - kind=gold: inferred gold reserves value (USD)
    - kind=non_gold: reserves minus gold (USD)
    - kind=total: total reserves incl. gold (USD)
    """
    ds = _load_reserves_dataset()
    countries = ds.get("countries") or {}
    max_year = ds.get("global_max_year")
    min_year = ds.get("global_min_year")

    if max_year is None or min_year is None or not countries:
        raise HTTPException(status_code=404, detail="Reserves dataset not found")

    kind_norm = (kind or "").strip().lower()
    if kind_norm not in {"gold", "non_gold", "total"}:
        raise HTTPException(status_code=400, detail="Invalid kind (use: gold | non_gold | total)")

    target_year = year if isinstance(year, int) else max_year
    if target_year < min_year or target_year > max_year:
        raise HTTPException(status_code=400, detail=f"Year out of range ({min_year}..{max_year})")

    rows: list[dict] = []
    for iso2, entry in countries.items():
        series = entry.get("series") or []
        # Find exact year point
        value = None
        for r in series:
            if r.get("year") == target_year:
                value = _reserves_kind_value(r, kind_norm)
                break
        if value is None:
            continue
        rows.append(
            {
                "iso2": iso2,
                "country_name": entry.get("country_name") or iso2,
                "value_usd": float(value),
                "data_end_year": entry.get("max_year"),
            }
        )

    rows.sort(key=lambda r: r["value_usd"], reverse=True)
    rows = rows[:limit]
    for i, r in enumerate(rows, start=1):
        r["rank"] = i

    return {
        "success": True,
        "kind": kind_norm,
        "year": target_year,
        "global_end_year": max_year,
        "count": len(rows),
        "data": rows,
    }


@app.get("/api/reserves/country")
async def get_reserves_country(
    iso2: str = Query(..., min_length=2, max_length=3, description="Country ISO2 code, e.g. US"),
):
    """
    Full time series for a country (gold inferred + non-gold + total).
    Adds a note if data ends before global end year.
    """
    ds = _load_reserves_dataset()
    countries = ds.get("countries") or {}
    max_year = ds.get("global_max_year")
    min_year = ds.get("global_min_year")

    if max_year is None or min_year is None or not countries:
        raise HTTPException(status_code=404, detail="Reserves dataset not found")

    code = (iso2 or "").strip().upper()
    entry = countries.get(code)
    if not entry:
        raise HTTPException(status_code=404, detail="Country not found")

    end_year = entry.get("max_year")
    note = None
    if isinstance(end_year, int) and isinstance(max_year, int) and end_year < max_year:
        note = f"Dữ liệu dừng tại năm {end_year}."

    return {
        "success": True,
        "global_year_range": {"start": min_year, "end": max_year},
        "country": {
            "iso2": entry.get("iso2"),
            "country_name": entry.get("country_name"),
            "year_range": {"start": entry.get("min_year"), "end": entry.get("max_year")},
            "note": note,
        },
        "data": entry.get("series") or [],
        "count": len(entry.get("series") or []),
    }

@app.get("/api/reserves/wgc/status")
async def get_wgc_status():
    """Return status of the latest WGC snapshot file."""
    exists = os.path.exists(WGC_CSV_PATH)
    meta = None
    if exists:
        try:
            meta = _load_wgc_latest().get("meta")
        except Exception:
            meta = None
    return {
        "success": True,
        "exists": exists,
        "path": WGC_CSV_PATH,
        "meta": meta,
    }


@app.post("/api/reserves/wgc/refresh")
async def refresh_wgc():
    """Force refresh of WGC snapshot via Playwright downloader."""
    if not _get_wgc_auth_cookie() and not os.path.exists(WGC_CSV_PATH):
        raise HTTPException(
            status_code=503,
            detail="WGC download requires authentication. Set env `WGC_AUTH_COOKIE` (wgcAuth_cookie) or save it to `.secrets/wgc_auth_cookie.txt`.",
        )
    try:
        data = _refresh_wgc_dataset()
        return {"success": True, "meta": data.get("meta"), "count": len(data.get("rows") or [])}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/reserves/wgc/top")
async def get_wgc_top(
    limit: int = Query(default=20, ge=1, le=200),
    sort: str = Query(default="tonnes", description="tonnes | value_usd"),
):
    """
    Return top N countries by WGC latest snapshot.
    """
    if not os.path.exists(WGC_CSV_PATH) and not _get_wgc_auth_cookie():
        raise HTTPException(
            status_code=503,
            detail="WGC dataset not available. Save auth cookie to `.secrets/wgc_auth_cookie.txt` (or env `WGC_AUTH_COOKIE`) then call POST /api/reserves/wgc/refresh.",
        )

    try:
        ds = _ensure_wgc_dataset()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    meta = ds.get("meta") or {}
    rows = list(ds.get("rows") or [])
    sort_key = (sort or "").strip().lower()
    if sort_key not in {"tonnes", "value_usd"}:
        raise HTTPException(status_code=400, detail="Invalid sort (use: tonnes | value_usd)")

    gold_spot = _get_gold_spot_usd_oz()
    valuation_note = None
    if gold_spot:
        valuation_note = f"Value (USD) = tonnes × troy_oz_per_tonne × spot_price_usd_oz (spot from {gold_spot.get('source') or 'unknown'})"
        for r in rows:
            tonnes = r.get("tonnes")
            if r.get("value_usd") is None and isinstance(tonnes, (int, float)) and tonnes > 0:
                try:
                    r["value_usd"] = round(_tonnes_to_troy_oz(float(tonnes)) * float(gold_spot["price_usd_oz"]), 2)
                except Exception:
                    pass
    meta_out = dict(meta)
    meta_out["valuation"] = {
        "spot_price_usd_oz": gold_spot.get("price_usd_oz") if gold_spot else None,
        "spot_source": gold_spot.get("source") if gold_spot else None,
        "spot_retrieved_at": gold_spot.get("retrieved_at") if gold_spot else None,
        "note": valuation_note,
    }

    def key_fn(r: dict):
        v = r.get(sort_key)
        return v if isinstance(v, (int, float)) else -1.0

    rows.sort(key=key_fn, reverse=True)
    rows = rows[:limit]
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
    return {"success": True, "meta": meta_out, "sort": sort_key, "count": len(rows), "data": rows}


@app.get("/api/prices/history")
async def get_price_history(
    days: int = Query(default=7, ge=1, le=730, description="Number of days to fetch")
):
    """
    Get price history for the specified number of days
    """
    try:
        if days >= 365:
            try:
                _ensure_intl_history_backfill(days=730)
                _ensure_tokenized_gold_backfill(days=730)
            except Exception:
                pass
        # Prefer DB query (no pandas dependency), 1 point/day.
        conn = _connect_history_db()
        try:
            from datetime import timedelta

            cutoff = (datetime.now() - timedelta(days=days)).replace(second=0, microsecond=0).isoformat()
            rows = conn.execute(
                """
                WITH per_day AS (
                    SELECT substr(ts, 1, 10) AS day, MAX(ts) AS ts
                    FROM price_snapshots
                    WHERE ts >= ?
                    GROUP BY day
                ),
                token_day AS (
                    SELECT
                      substr(ts, 1, 10) AS day,
                      MAX(paxg_usd_oz) AS paxg_usd_oz,
                      MAX(paxg_source) AS paxg_source,
                      MAX(xaut_usd_oz) AS xaut_usd_oz,
                      MAX(xaut_source) AS xaut_source
                    FROM price_snapshots
                    WHERE ts >= ?
                    GROUP BY day
                )
                SELECT
                  ps.ts,
                  ps.created_at,
                  ps.usd_vnd,
                  ps.sjc_vnd_luong,
                  ps.phuquy_silver_vnd,
                  ps.phuquy_silver_unit,
                  ps.intl_gold_usd_oz,
                  ps.intl_gold_source,
                  ps.intl_silver_usd_oz,
                  ps.intl_silver_source,
                  ps.gold_spread_vnd,
                  ps.gold_spread_percent,
                  ps.gold_intl_vnd_per_luong,
                  ps.silver_spread_vnd,
                  ps.silver_spread_percent,
                  ps.silver_intl_vnd_per_unit,
                  ps.silver_spread_unit,
                  COALESCE(ps.paxg_usd_oz, td.paxg_usd_oz) AS paxg_usd_oz,
                  COALESCE(ps.paxg_source, td.paxg_source) AS paxg_source,
                  COALESCE(ps.xaut_usd_oz, td.xaut_usd_oz) AS xaut_usd_oz,
                  COALESCE(ps.xaut_source, td.xaut_source) AS xaut_source
                FROM price_snapshots ps
                JOIN per_day pd ON ps.ts = pd.ts
                LEFT JOIN token_day td ON td.day = pd.day
                ORDER BY ps.ts ASC
                """,
                (cutoff, cutoff),
            ).fetchall()
            data = _rows_to_dicts(rows)
        finally:
            conn.close()

        # Normalize legacy snapshots where silver was stored as VND/kg.
        kg_to_luong = 1000.0 / 37.5
        for r in data:
            unit = (r.get("phuquy_silver_unit") or "").strip().lower()
            if "kg" in unit and r.get("phuquy_silver_vnd") is not None:
                try:
                    r["phuquy_silver_vnd"] = float(r["phuquy_silver_vnd"]) / kg_to_luong
                except Exception:
                    pass
                r["phuquy_silver_unit"] = "VND/lượng"
            spread_unit = (r.get("silver_spread_unit") or "").strip().lower()
            if "kg" in spread_unit and r.get("silver_spread_vnd") is not None:
                try:
                    r["silver_spread_vnd"] = float(r["silver_spread_vnd"]) / kg_to_luong
                except Exception:
                    pass
                r["silver_spread_unit"] = "VND/lượng"

        if not data:
            return {
                "success": True,
                "data": [],
                "message": "No history data available"
            }

        return {
            "success": True,
            "data": data,
            "count": len(data),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prices/sjc-items")
async def get_sjc_items():
    """Get latest SJC items with detailed prices"""
    try:
        # Warm-up: ensure DB has per-item rows by fetching today's snapshot once.
        try:
            fetcher.get_formatted_data()
        except Exception:
            pass

        conn = _connect_history_db()
        try:
            from datetime import timedelta

            cutoff = (datetime.now() - timedelta(days=30)).replace(second=0, microsecond=0).isoformat()
            rows = conn.execute(
                """
                WITH latest AS (
                    SELECT
                        name,
                        COALESCE(branch, '') AS branch_key,
                        MAX(ts) AS ts
                    FROM sjc_items
                    WHERE ts >= ?
                    GROUP BY name, branch_key
                )
                SELECT s.*
                FROM sjc_items s
                JOIN latest l
                  ON s.name = l.name
                 AND COALESCE(s.branch, '') = l.branch_key
                 AND s.ts = l.ts
                ORDER BY s.name, s.branch
                """,
                (cutoff,),
            ).fetchall()
            data = _rows_to_dicts(rows)
        finally:
            conn.close()

        if data:
            return {"success": True, "data": data, "count": len(data), "source": "db"}

        # Last resort: return live scraped data (not DB-backed).
        sjc_data = fetcher.fetch_sjc_gold()
        rows = []
        for item in (sjc_data or []):
            name = item.get("name")
            buy = fetcher._to_float(item.get("buy_price") or item.get("buy"))
            sell = fetcher._to_float(item.get("sell_price") or item.get("sell"))
            if name and (buy is not None or sell is not None):
                rows.append(
                    {
                        "ts": datetime.now().isoformat(),
                        "name": name,
                        "branch": item.get("branch"),
                        "buy_price": buy,
                        "sell_price": sell,
                        "date": item.get("date"),
                    }
                )
        if rows:
            return {"success": True, "data": rows, "count": len(rows), "source": "live"}

        return {"success": True, "data": [], "message": "No SJC items available"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prices/sjc-item-history")
async def get_sjc_item_history(
    name: str = Query(..., description="Product name"),
    branch: Optional[str] = Query(None, description="Branch name"),
    days: int = Query(default=365, ge=1, le=365)
):
    """Get history for a specific SJC item"""
    try:
        conn = _connect_history_db()
        try:
            from datetime import timedelta

            cutoff = (datetime.now() - timedelta(days=days)).replace(second=0, microsecond=0).isoformat()
            if branch:
                rows = conn.execute(
                    """
                    SELECT ts, name, branch, buy_price, sell_price
                    FROM sjc_items
                    WHERE ts >= ? AND name = ? AND branch = ?
                    ORDER BY ts ASC
                    """,
                    (cutoff, name, branch),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT ts, name, branch, buy_price, sell_price
                    FROM sjc_items
                    WHERE ts >= ? AND name = ?
                    ORDER BY ts ASC
                    """,
                    (cutoff, name),
                ).fetchall()
            data = _rows_to_dicts(rows)
        finally:
            conn.close()

        if not data:
            return {
                "success": True,
                "data": [],
                "message": "No history available for this item"
            }

        return {
            "success": True,
            "data": data,
            "count": len(data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prices/phuquy-items")
async def get_phuquy_items():
    """Get latest Phu Quy silver items"""
    try:
        # Warm-up: ensure DB has per-item rows by fetching today's snapshot once.
        try:
            fetcher.get_formatted_data()
        except Exception:
            pass

        conn = _connect_history_db()
        try:
            from datetime import timedelta

            cutoff = (datetime.now() - timedelta(days=30)).replace(second=0, microsecond=0).isoformat()
            rows = conn.execute(
                """
                WITH latest AS (
                    SELECT product, MAX(ts) AS ts
                    FROM phuquy_items
                    WHERE ts >= ?
                    GROUP BY product
                )
                SELECT p.*
                FROM phuquy_items p
                JOIN latest l
                  ON p.product = l.product
                 AND p.ts = l.ts
                ORDER BY p.product
                """,
                (cutoff,),
            ).fetchall()
            data = _rows_to_dicts(rows)
        finally:
            conn.close()

        if data:
            data = [_normalize_phuquy_to_luong(d) for d in data]
            return {"success": True, "data": data, "count": len(data), "source": "db"}

        # Last resort: return live scraped data (not DB-backed).
        pq = fetcher.fetch_phuquy_silver() or {}
        rows = []
        for item in (pq.get("prices") or []):
            product = (item.get("product") or item.get("type") or "").strip()
            unit = item.get("unit")
            buy = fetcher._to_float(item.get("buy_price") or item.get("buy"))
            sell = fetcher._to_float(item.get("sell_price") or item.get("sell"))
            if product and (buy is not None or sell is not None):
                rows.append(
                    {
                        "ts": datetime.now().isoformat(),
                        "product": product,
                        "unit": unit,
                        "buy_price": buy,
                        "sell_price": sell,
                    }
                )
        if rows:
            rows = [_normalize_phuquy_to_luong(d) for d in rows]
            return {"success": True, "data": rows, "count": len(rows), "source": "live"}

        return {"success": True, "data": [], "message": "No Phu Quy items available"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prices/phuquy-item-history")
async def get_phuquy_item_history(
    product: str = Query(..., description="Product name"),
    days: int = Query(default=365, ge=1, le=730)
):
    """Get history for a specific Phu Quy item"""
    try:
        conn = _connect_history_db()
        try:
            from datetime import timedelta

            cutoff = (datetime.now() - timedelta(days=days)).replace(second=0, microsecond=0).isoformat()
            rows = conn.execute(
                """
                SELECT ts, product, unit, buy_price, sell_price
                FROM phuquy_items
                WHERE ts >= ? AND product = ?
                ORDER BY ts ASC
                """,
                (cutoff, product),
            ).fetchall()
            data = _rows_to_dicts(rows)
        finally:
            conn.close()

        if not data:
            return {
                "success": True,
                "data": [],
                "message": "No history available for this product"
            }

        data = [_normalize_phuquy_to_luong(d) for d in data]
        return {
            "success": True,
            "data": data,
            "count": len(data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
