"""
Data Fetcher for Price Tracker UI
Fetches data from all 3 modules and calculates spreads
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional
import importlib
import inspect
import re
import unicodedata
import json
import time
import requests

# Get the parent directory of ui (Word Asset folder)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Add parent directories to path
vn_gold_path = os.path.join(parent_dir, 'vn_gold_tracker')
silver_path = os.path.join(parent_dir, 'silver_scraper')
intl_path = os.path.join(parent_dir, 'international_metals')

def _prepend_sys_path(path: str) -> None:
    if not path:
        return
    norm = os.path.normpath(path)
    sys.path[:] = [p for p in sys.path if os.path.normpath(p) != norm]
    sys.path.insert(0, path)

# Ensure local modules shadow any site-packages installs.
_prepend_sys_path(parent_dir)
_prepend_sys_path(vn_gold_path)
_prepend_sys_path(silver_path)
_prepend_sys_path(intl_path)

try:
    from vn_gold_tracker.gold_data_pg import GoldDataPG
except ImportError:
    GoldDataPG = None
    print("Warning: vn_gold_tracker not found")

try:
    from silver_scraper.src.silver_scraper import SilverPriceScraper
except ImportError:
    SilverPriceScraper = None
    print("Warning: silver_scraper not found")

try:
    # Streamlit can keep modules cached across reruns; if an older pip-installed
    # `international_metals_pkg` was imported first, force reload from local repo.
    existing = sys.modules.get("international_metals_pkg")
    if existing is not None:
        mod_file = getattr(existing, "__file__", "") or ""
        if os.path.normpath(intl_path) not in os.path.normpath(mod_file):
            for name in ["international_metals_pkg.core", "international_metals_pkg"]:
                sys.modules.pop(name, None)

    from international_metals_pkg import PreciousMetalsPrice as _PreciousMetalsPrice
    PreciousMetalsPrice = _PreciousMetalsPrice
except Exception:
    PreciousMetalsPrice = None
    print("Warning: international_metals not found")


class PriceDataFetcher:
    """Fetches price data from all sources and calculates spreads"""

    # Conversion constants
    OZ_TO_GRAM = 31.1035  # 1 troy ounce in grams
    LUONG_TO_GRAM = 37.5  # 1 lượng (cây) in grams
    KG_TO_GRAM = 1000.0
    # Unit conversions:
    # - 1 oz  = OZ_TO_LUONG lượng
    # - 1 lượng = LUONG_TO_OZ oz
    OZ_TO_LUONG = OZ_TO_GRAM / LUONG_TO_GRAM  # 0.82942666...
    LUONG_TO_OZ = LUONG_TO_GRAM / OZ_TO_GRAM  # 1.20565070...
    KG_TO_OZ = KG_TO_GRAM / OZ_TO_GRAM  # 32.1507466...
    KG_TO_LUONG = KG_TO_GRAM / LUONG_TO_GRAM  # 26.6666666...

    def __init__(self):
        """Initialize all data fetchers"""
        self.gold_fetcher = GoldDataPG() if GoldDataPG else None
        self.silver_fetcher = SilverPriceScraper() if SilverPriceScraper else None
        self.intl_fetcher = None
        if PreciousMetalsPrice:
            try:
                self.intl_fetcher = PreciousMetalsPrice(cache_duration=600, primary_source="msn")
            except TypeError:
                self.intl_fetcher = PreciousMetalsPrice(cache_duration=600)
                if hasattr(self.intl_fetcher, "primary_source"):
                    self.intl_fetcher.primary_source = "msn"

        # Cached data
        self.cached_data = {}
        self.last_fetch = None
        self._last_good_intl = {"gold": None, "silver": None}
        self._last_good_intl_at = {"gold": None, "silver": None}
        self._intl_disk_cache_path = os.path.join(current_dir, ".intl_cache.json")
        self._load_intl_disk_cache()
        self._token_cache: Dict = {}
        self._token_last_fetch: Optional[datetime] = None
        self._history_db_path = os.path.join(current_dir, "price_history.db")
        self._init_history_db()

    def _connect_history_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._history_db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_history_db(self) -> None:
        try:
            conn = self._connect_history_db()
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS price_snapshots (
                    ts TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    usd_vnd REAL,
                    sjc_vnd_luong REAL,
                    phuquy_silver_vnd REAL,
                    phuquy_silver_unit TEXT,
                    intl_gold_usd_oz REAL,
                    intl_gold_source TEXT,
                    intl_silver_usd_oz REAL,
                    intl_silver_source TEXT,
                    paxg_usd_oz REAL,
                    paxg_source TEXT,
                    xaut_usd_oz REAL,
                    xaut_source TEXT,
                    gold_spread_vnd REAL,
                    gold_spread_percent REAL,
                    gold_intl_vnd_per_luong REAL,
                    silver_spread_vnd REAL,
                    silver_spread_percent REAL,
                    silver_intl_vnd_per_unit REAL,
                    silver_spread_unit TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sjc_items (
                    ts TEXT NOT NULL,
                    name TEXT NOT NULL,
                    branch TEXT,
                    buy_price REAL,
                    sell_price REAL,
                    date TEXT,
                    PRIMARY KEY (ts, name, branch)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sjc_items_name ON sjc_items(name)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sjc_items_ts ON sjc_items(ts)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS phuquy_items (
                    ts TEXT NOT NULL,
                    product TEXT NOT NULL,
                    unit TEXT,
                    buy_price REAL,
                    sell_price REAL,
                    PRIMARY KEY (ts, product)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_phuquy_items_product ON phuquy_items(product)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_phuquy_items_ts ON phuquy_items(ts)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_price_snapshots_created_at ON price_snapshots(created_at DESC)"
            )
            # Lightweight migrations for existing DBs
            cols = {r[1] for r in conn.execute("PRAGMA table_info(price_snapshots)").fetchall()}
            for name, sql_type in [
                ("paxg_usd_oz", "REAL"),
                ("paxg_source", "TEXT"),
                ("xaut_usd_oz", "REAL"),
                ("xaut_source", "TEXT"),
            ]:
                if name not in cols:
                    conn.execute(f"ALTER TABLE price_snapshots ADD COLUMN {name} {sql_type}")
            conn.commit()
            conn.close()
        except Exception:
            return

    def _save_snapshot(self, result: Dict) -> None:
        try:
            # Bucket to minute to avoid spamming DB on rapid reruns.
            now = datetime.now().replace(second=0, microsecond=0)
            ts = now.isoformat()

            usd_vnd = result.get("usd_vnd")
            sjc = (result.get("sjc") or {}).get("price_1l_10l")
            phuquy_price = (result.get("phuquy_silver") or {}).get("price")
            phuquy_unit = (result.get("phuquy_silver") or {}).get("unit")

            intl_gold = (result.get("international") or {}).get("gold") or {}
            intl_silver = (result.get("international") or {}).get("silver") or {}
            paxg = (result.get("tokenized") or {}).get("paxg") or {}
            xaut = (result.get("tokenized") or {}).get("xaut") or {}

            gold_spread = (result.get("spreads") or {}).get("gold") or {}
            silver_spread = (result.get("spreads") or {}).get("silver") or {}

            conn = self._connect_history_db()
            conn.execute(
                """
                INSERT OR REPLACE INTO price_snapshots (
                    ts, created_at,
                    usd_vnd, sjc_vnd_luong,
                    phuquy_silver_vnd, phuquy_silver_unit,
                    intl_gold_usd_oz, intl_gold_source,
                    intl_silver_usd_oz, intl_silver_source,
                    paxg_usd_oz, paxg_source,
                    xaut_usd_oz, xaut_source,
                    gold_spread_vnd, gold_spread_percent, gold_intl_vnd_per_luong,
                    silver_spread_vnd, silver_spread_percent, silver_intl_vnd_per_unit, silver_spread_unit
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ts,
                    datetime.now().isoformat(),
                    usd_vnd,
                    sjc,
                    phuquy_price,
                    phuquy_unit,
                    intl_gold.get("price"),
                    intl_gold.get("source"),
                    intl_silver.get("price"),
                    intl_silver.get("source"),
                    paxg.get("price"),
                    paxg.get("source"),
                    xaut.get("price"),
                    xaut.get("source"),
                    gold_spread.get("spread_vnd"),
                    gold_spread.get("spread_percent"),
                    gold_spread.get("intl_per_luong"),
                    silver_spread.get("spread_vnd"),
                    silver_spread.get("spread_percent"),
                    silver_spread.get("intl_per_luong"),
                    phuquy_unit,
                ),
            )

            # Save per-product details (SJC)
            sjc_rows = (result.get("sjc") or {}).get("data") or []
            if isinstance(sjc_rows, list) and sjc_rows:
                rows = []
                for item in sjc_rows:
                    name = (item.get("name") or "").strip()
                    branch = (item.get("branch") or "").strip() or None
                    buy = self._to_float(item.get("buy_price"))
                    sell = self._to_float(item.get("sell_price"))
                    date = item.get("date")
                    if name:
                        rows.append((ts, name, branch, buy, sell, date))
                if rows:
                    conn.executemany(
                        """
                        INSERT OR REPLACE INTO sjc_items
                        (ts, name, branch, buy_price, sell_price, date)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        rows,
                    )

            # Save per-product details (Phu Quý)
            pq = (result.get("phuquy_silver") or {}).get("data") or {}
            pq_prices = pq.get("prices") if isinstance(pq, dict) else None
            if isinstance(pq_prices, list) and pq_prices:
                rows = []
                for item in pq_prices:
                    product = (item.get("product") or item.get("type") or "").strip()
                    unit = (item.get("unit") or "").strip() or None
                    buy = self._to_float(item.get("buy_price") or item.get("buy"))
                    sell = self._to_float(item.get("sell_price") or item.get("sell"))
                    if product:
                        rows.append((ts, product, unit, buy, sell))
                if rows:
                    conn.executemany(
                        """
                        INSERT OR REPLACE INTO phuquy_items
                        (ts, product, unit, buy_price, sell_price)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        rows,
                    )

            conn.commit()
            conn.close()
        except Exception:
            return

    def get_history(self, days_back: int = 7):
        cutoff = (datetime.now() - timedelta(days=days_back)).replace(second=0, microsecond=0).isoformat()
        conn = self._connect_history_db()
        try:
            import pandas as pd

            df = pd.read_sql_query(
                """
                SELECT *
                FROM price_snapshots
                WHERE ts >= ?
                ORDER BY ts ASC
                """,
                conn,
                params=(cutoff,),
            )
            return df
        finally:
            conn.close()

    def get_history_daily(self, days_back: int = 30):
        """
        Return day-by-day history (1 point/day).

        We pick the latest snapshot for each day to avoid showing data for every refresh.
        """
        cutoff = (datetime.now() - timedelta(days=days_back)).replace(second=0, microsecond=0).isoformat()
        conn = self._connect_history_db()
        try:
            import pandas as pd

            df = pd.read_sql_query(
                """
                WITH per_day AS (
                    SELECT substr(ts, 1, 10) AS day, MAX(ts) AS ts
                    FROM price_snapshots
                    WHERE ts >= ?
                    GROUP BY day
                )
                SELECT ps.*
                FROM price_snapshots ps
                JOIN per_day pd ON ps.ts = pd.ts
                ORDER BY ps.ts ASC
                """,
                conn,
                params=(cutoff,),
            )
            return df
        finally:
            conn.close()

    def get_sjc_items_latest(self, max_age_days: int = 30):
        conn = self._connect_history_db()
        try:
            import pandas as pd

            # If the most recent refresh was partial (e.g., fallback source), MAX(ts) can
            # contain fewer products than exist overall. Instead, take the latest row per
            # (name, branch) over a recent window.
            cutoff = (datetime.now() - timedelta(days=max_age_days)).replace(second=0, microsecond=0).isoformat()

            def _query(params):
                return pd.read_sql_query(
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
                    conn,
                    params=params,
                )

            df = _query((cutoff,))
            if df is not None and not df.empty:
                return df

            # Fallback: no rows in window, return the latest per (name, branch) overall.
            df = pd.read_sql_query(
                """
                WITH latest AS (
                    SELECT
                        name,
                        COALESCE(branch, '') AS branch_key,
                        MAX(ts) AS ts
                    FROM sjc_items
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
                conn,
            )
            return df
        finally:
            conn.close()

    def get_sjc_item_history(self, name: str, branch: Optional[str] = None, days_back: int = 365):
        cutoff = (datetime.now() - timedelta(days=days_back)).replace(second=0, microsecond=0).isoformat()
        conn = self._connect_history_db()
        try:
            import pandas as pd

            if branch:
                df = pd.read_sql_query(
                    """
                    SELECT ts, name, branch, buy_price, sell_price
                    FROM sjc_items
                    WHERE ts >= ? AND name = ? AND branch = ?
                    ORDER BY ts ASC
                    """,
                    conn,
                    params=(cutoff, name, branch),
                )
            else:
                df = pd.read_sql_query(
                    """
                    SELECT ts, name, branch, buy_price, sell_price
                    FROM sjc_items
                    WHERE ts >= ? AND name = ?
                    ORDER BY ts ASC
                    """,
                    conn,
                    params=(cutoff, name),
                )
            return df
        finally:
            conn.close()

    def get_phuquy_items_latest(self, max_age_days: int = 30):
        conn = self._connect_history_db()
        try:
            import pandas as pd

            cutoff = (datetime.now() - timedelta(days=max_age_days)).replace(second=0, microsecond=0).isoformat()

            df = pd.read_sql_query(
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
                conn,
                params=(cutoff,),
            )
            if df is not None and not df.empty:
                return df

            df = pd.read_sql_query(
                """
                WITH latest AS (
                    SELECT product, MAX(ts) AS ts
                    FROM phuquy_items
                    GROUP BY product
                )
                SELECT p.*
                FROM phuquy_items p
                JOIN latest l
                  ON p.product = l.product
                 AND p.ts = l.ts
                ORDER BY p.product
                """,
                conn,
            )
            return df
        finally:
            conn.close()

    def get_phuquy_item_history(self, product: str, days_back: int = 365):
        cutoff = (datetime.now() - timedelta(days=days_back)).replace(second=0, microsecond=0).isoformat()
        conn = self._connect_history_db()
        try:
            import pandas as pd

            df = pd.read_sql_query(
                """
                SELECT ts, product, unit, buy_price, sell_price
                FROM phuquy_items
                WHERE ts >= ? AND product = ?
                ORDER BY ts ASC
                """,
                conn,
                params=(cutoff, product),
            )
            return df
        finally:
            conn.close()

    def _load_intl_disk_cache(self) -> None:
        try:
            with open(self._intl_disk_cache_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            saved_at = payload.get("saved_at")
            prices = payload.get("prices") or {}
            if not saved_at:
                return
            saved_dt = datetime.fromisoformat(saved_at)
            for metal in ["gold", "silver"]:
                data = prices.get(metal)
                if isinstance(data, dict) and isinstance(data.get("price"), (int, float)):
                    self._last_good_intl[metal] = data
                    self._last_good_intl_at[metal] = saved_dt
        except Exception:
            return

    def _save_intl_disk_cache(self, gold: Optional[Dict], silver: Optional[Dict]) -> None:
        try:
            payload = {
                "saved_at": datetime.now().isoformat(),
                "prices": {"gold": gold, "silver": silver},
            }
            tmp = self._intl_disk_cache_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
            os.replace(tmp, self._intl_disk_cache_path)
        except Exception:
            return

    @staticmethod
    def _to_float(value) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            text = value.strip()
            if not text or text.upper() in {"N/A", "NA", "NONE", "-"}:
                return None
            # keep digits, minus and dot only
            text = text.replace(",", "")
            text = re.sub(r"[^0-9.\-]", "", text)
            if not text or text in {"-", ".", "-."}:
                return None
            try:
                return float(text)
            except ValueError:
                return None
        return None

    @staticmethod
    def _norm_text(value: str) -> str:
        value = value or ""
        value = unicodedata.normalize("NFKD", value)
        value = "".join(ch for ch in value if not unicodedata.combining(ch))
        return re.sub(r"\\s+", " ", value).strip().upper()

    @staticmethod
    def _normalize_vn_unit(value: str) -> str:
        unit = (value or "").strip()
        if not unit:
            return ""
        # Common variants from scrapers
        unit_norm = unit.replace("Vnđ", "VND").replace("VNĐ", "VND")
        unit_norm = unit_norm.replace("Vnd", "VND")
        unit_norm = unit_norm.replace("Lượng", "lượng").replace("LUONG", "lượng")
        unit_norm = unit_norm.replace("Kg", "kg").replace("KG", "kg")
        unit_norm = re.sub(r"\\s+", "", unit_norm)
        # Ensure format VND/<unit>
        if unit_norm.lower().endswith("/kg"):
            return "VND/kg"
        if unit_norm.lower().endswith("/lượng") or unit_norm.lower().endswith("/luong"):
            return "VND/lượng"
        # Fallback keep original
        return unit

    def fetch_vnd_usd_rate(self) -> Optional[float]:
        """Fetch USD/VND exchange rate"""
        if self.gold_fetcher:
            try:
                result = self.gold_fetcher.get_usd_vnd_rate(save_to_db=False)
                # Result can be DataFrame or dict
                if hasattr(result, 'iloc'):  # DataFrame
                    if len(result) > 0 and 'currency_code' in result.columns:
                        df = result
                        usd_rows = df[df['currency_code'].astype(str).str.upper() == 'USD']
                        if len(usd_rows) > 0:
                            row = usd_rows.iloc[0]
                        else:
                            row = df.iloc[0]

                        for col in ['sell', 'sell_price', 'bank_sell']:
                            if col in df.columns:
                                value = row[col]
                                parsed = self._to_float(value)
                                if parsed is not None:
                                    return parsed
                elif isinstance(result, dict) and 'data' in result:
                    value = result['data'].get('sell')
                    if value:
                        return self._to_float(value)
            except Exception as e:
                print(f"Error fetching USD/VND rate: {e}")
        return None

    def fetch_sjc_gold(self) -> Dict:
        """Fetch SJC gold prices"""
        if self.gold_fetcher:
            try:
                result = self.gold_fetcher.get_sjc_gold_price(save_to_db=False)
                # Result is DataFrame
                if hasattr(result, 'iloc'):  # Check if DataFrame
                    if len(result) > 0:
                        # Convert DataFrame to list of dicts
                        return result.to_dict('records')
                    return {}
                elif isinstance(result, dict) and 'data' in result:
                    return result['data']
            except Exception as e:
                print(f"Error fetching SJC gold: {e}")
        return {}

    def fetch_phuquy_silver(self) -> Dict:
        """Fetch Phu Quy silver prices"""
        if self.silver_fetcher:
            try:
                data = self.silver_fetcher.get_silver_prices()
                return data
            except Exception as e:
                print(f"Error fetching Phu Quy silver: {e}")
        return {}

    def fetch_international_prices(self) -> Dict:
        """Fetch international gold and silver prices"""
        def _normalize_stooq(metal: str, payload: Optional[Dict]) -> Optional[Dict]:
            if not isinstance(payload, dict):
                return payload
            source = str(payload.get("source") or "")
            price = payload.get("price")
            if metal == "silver" and "STOOQ" in source.upper() and isinstance(price, (int, float)) and price > 1000:
                scale = 0.01
                out = dict(payload)
                for k in ["price", "change", "high", "low"]:
                    v = out.get(k)
                    if isinstance(v, (int, float)):
                        out[k] = v * scale
                return out
            return payload

        # If intl fetcher isn't available, fall back to last-known-good disk cache.
        if not self.intl_fetcher:
            now = datetime.now()
            max_age_seconds = 24 * 60 * 60
            gold_price = None
            silver_price = None
            if self._last_good_intl["gold"] and self._last_good_intl_at["gold"]:
                if (now - self._last_good_intl_at["gold"]).total_seconds() <= max_age_seconds:
                    gold_price = dict(self._last_good_intl["gold"])
                    gold_price["source"] = f"{gold_price.get('source', 'cached')} (cached)"
            if self._last_good_intl["silver"] and self._last_good_intl_at["silver"]:
                if (now - self._last_good_intl_at["silver"]).total_seconds() <= max_age_seconds:
                    silver_price = dict(self._last_good_intl["silver"])
                    silver_price["source"] = f"{silver_price.get('source', 'cached')} (cached)"
            return {"gold": _normalize_stooq("gold", gold_price), "silver": _normalize_stooq("silver", silver_price)}

        if self.intl_fetcher:
            try:
                # Use a single call to reduce flakiness and share MSN state/cache.
                prices = self.intl_fetcher.get_all_prices(use_cache=True)
                gold_price = _normalize_stooq("gold", prices.get("gold"))
                silver_price = _normalize_stooq("silver", prices.get("silver"))

                # If both are missing, do a few short retries (MSN SSR can be flaky).
                if gold_price is None and silver_price is None:
                    for attempt in range(5):
                        time.sleep(0.25 * (attempt + 1))
                        prices = self.intl_fetcher.get_all_prices(use_cache=False)
                        gold_price = _normalize_stooq("gold", prices.get("gold"))
                        silver_price = _normalize_stooq("silver", prices.get("silver"))
                        if gold_price is not None or silver_price is not None:
                            break

                now = datetime.now()
                if gold_price:
                    self._last_good_intl["gold"] = gold_price
                    self._last_good_intl_at["gold"] = now
                if silver_price:
                    self._last_good_intl["silver"] = silver_price
                    self._last_good_intl_at["silver"] = now

                if gold_price or silver_price:
                    self._save_intl_disk_cache(
                        self._last_good_intl["gold"],
                        self._last_good_intl["silver"],
                    )

                # If one side fails, fall back to last known good (disk-backed).
                # Keep it generous to avoid showing N/A due to transient MSN failures.
                max_age_seconds = 24 * 60 * 60
                if not gold_price and self._last_good_intl["gold"] and self._last_good_intl_at["gold"]:
                    age = (now - self._last_good_intl_at["gold"]).total_seconds()
                    if age <= max_age_seconds:
                        gold_price = dict(self._last_good_intl["gold"])
                        gold_price["source"] = f"{gold_price.get('source', 'MSN Money')} (cached)"

                if not silver_price and self._last_good_intl["silver"] and self._last_good_intl_at["silver"]:
                    age = (now - self._last_good_intl_at["silver"]).total_seconds()
                    if age <= max_age_seconds:
                        silver_price = dict(self._last_good_intl["silver"])
                        silver_price["source"] = f"{silver_price.get('source', 'MSN Money')} (cached)"

                return {"gold": _normalize_stooq("gold", gold_price), "silver": _normalize_stooq("silver", silver_price)}
            except Exception as e:
                print(f"Error fetching international prices: {e}")
        return {'gold': None, 'silver': None}

    def fetch_tokenized_gold_prices(self) -> Dict:
        """
        Fetch tokenized gold prices (PAXG, XAUT) in USD/oz.
        Source: CryptoCompare.
        """
        now = datetime.now()
        if self._token_last_fetch and (now - self._token_last_fetch).total_seconds() < 300 and self._token_cache:
            return dict(self._token_cache)

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
                    "source": "CryptoCompare",
                    "symbol": sym,
                    "price": round(float(price), 2),
                    "change": round(float(change), 2) if isinstance(change, (int, float)) else None,
                    "change_percent": round(float(change_pct), 2) if isinstance(change_pct, (int, float)) else None,
                    "unit": "USD/oz",
                    "timestamp": now.isoformat(),
                }

            out = {"paxg": _one("PAXG"), "xaut": _one("XAUT")}
            self._token_cache = out
            self._token_last_fetch = now
            return out
        except Exception:
            return {"paxg": None, "xaut": None}

    def calculate_gold_spread(self, sjc_price: float, intl_price: float, usd_vnd: float) -> Dict:
        """
        Calculate spread between SJC and international gold price

        Args:
            sjc_price: SJC gold price in VND/lượng
            intl_price: International gold price in USD/oz
            usd_vnd: USD/VND exchange rate

        Returns:
            Dict with spread calculations
        """
        if not all([sjc_price, intl_price, usd_vnd]):
            return {
                'spread_vnd': None,
                'spread_percent': None,
                'intl_in_vnd': None,
                'intl_per_luong': None
            }

        # Convert international price from USD/oz to VND/lượng
        intl_per_luong = intl_price * usd_vnd * self.LUONG_TO_OZ
        intl_in_vnd = intl_price * usd_vnd

        # Calculate spread
        spread_vnd = sjc_price - intl_per_luong
        spread_percent = (spread_vnd / intl_per_luong) * 100 if intl_per_luong > 0 else 0

        return {
            'spread_vnd': round(spread_vnd, 2),
            'spread_percent': round(spread_percent, 2),
            'intl_in_vnd': round(intl_in_vnd, 2),
            'intl_per_luong': round(intl_per_luong, 2)
        }

    def calculate_silver_spread(
        self, phuquy_price: float, intl_price: float, usd_vnd: float, phuquy_unit: str
    ) -> Dict:
        """
        Calculate spread between Phu Quy and international silver price

        Args:
            phuquy_price: Phu Quy silver price (unit depends on phuquy_unit)
            intl_price: International silver price in USD/oz
            usd_vnd: USD/VND exchange rate

        Returns:
            Dict with spread calculations
        """
        if not all([phuquy_price, intl_price, usd_vnd]):
            return {
                'spread_vnd': None,
                'spread_percent': None,
                'intl_in_vnd': None,
                'intl_per_luong': None
            }

        unit_norm = (phuquy_unit or "").strip().upper()
        if "KG" in unit_norm:
            intl_per_unit = intl_price * usd_vnd * self.KG_TO_OZ
        else:
            # Default to lượng
            intl_per_unit = intl_price * usd_vnd * self.LUONG_TO_OZ
        intl_in_vnd = intl_price * usd_vnd

        # Calculate spread
        spread_vnd = phuquy_price - intl_per_unit
        spread_percent = (spread_vnd / intl_per_unit) * 100 if intl_per_unit > 0 else 0

        return {
            'spread_vnd': round(spread_vnd, 2),
            'spread_percent': round(spread_percent, 2),
            'intl_in_vnd': round(intl_in_vnd, 2),
            'intl_per_luong': round(intl_per_unit, 2)
        }

    def fetch_all_data(self) -> Dict:
        """
        Fetch all data and calculate spreads

        Returns:
            Dict with all price data and spreads
        """
        # Fetch all data
        usd_vnd = self.fetch_vnd_usd_rate()
        sjc_data = self.fetch_sjc_gold()
        phuquy_data = self.fetch_phuquy_silver()
        intl_data = self.fetch_international_prices()
        token_data = self.fetch_tokenized_gold_prices()

        # Extract relevant prices
        sjc_price = None
        if sjc_data:
            # Get SJC price (vàng miếng)
            for item in sjc_data:
                name = item.get('name', '') or ''
                # Prefer sell price for UI display
                sell_price = item.get('sell_price') or item.get('sell')
                buy_price = item.get('buy_price') or item.get('buy')
                candidate = sell_price or buy_price
                if 'SJC' in self._norm_text(name) and candidate:
                    parsed = self._to_float(candidate)
                    if parsed is not None:
                        sjc_price = parsed
                        break
            # Normalize: some fallback sources may provide VNĐ/chỉ instead of VNĐ/lượng.
            if sjc_price is not None and sjc_price < 30_000_000:
                sjc_price *= 10

        phuquy_price = None
        phuquy_unit = None
        if phuquy_data and 'prices' in phuquy_data:
            # Standardize display unit to VND/lượng for consistency with gold.
            # Prefer: 1 lượng product; fallback: convert 1kg to per-lượng.
            raw_unit = None

            def _pick_price(match_norm: str):
                for item in phuquy_data['prices']:
                    name = item.get('type', '') or item.get('product', '') or ""
                    unit = item.get("unit") or ""
                    # Prefer sell price for UI display
                    sell_price = item.get('sell') or item.get('sell_price')
                    buy_price = item.get('buy') or item.get('buy_price')
                    candidate = sell_price or buy_price
                    if match_norm in self._norm_text(name) and candidate:
                        parsed = self._to_float(candidate)
                        if parsed is not None:
                            return parsed, unit
                return None, None

            # 1) Prefer 1 lượng
            phuquy_price, raw_unit = _pick_price("BAC MIENG PHU QUY 999 1 LUONG")

            # 2) Fallback: 1kg -> convert to per lượng
            if phuquy_price is None:
                kg_price, raw_unit = _pick_price("BAC THOI PHU QUY 999 1KILO")
                if kg_price is not None:
                    phuquy_price = kg_price / self.KG_TO_LUONG

            if phuquy_price is not None:
                phuquy_unit = "VND/lượng"
            else:
                phuquy_unit = None

        intl_gold_price = intl_data.get('gold', {}).get('price') if intl_data.get('gold') else None
        intl_silver_price = intl_data.get('silver', {}).get('price') if intl_data.get('silver') else None

        # Calculate spreads
        gold_spread = self.calculate_gold_spread(sjc_price, intl_gold_price, usd_vnd) if sjc_price and intl_gold_price else {}
        silver_spread = (
            self.calculate_silver_spread(phuquy_price, intl_silver_price, usd_vnd, phuquy_unit)
            if phuquy_price and intl_silver_price
            else {}
        )

        # Compile result
        result = {
            'timestamp': datetime.now().isoformat(),
            'usd_vnd': usd_vnd,
            'sjc': {
                'data': sjc_data,
                'price_1l_10l': sjc_price
            },
            'phuquy_silver': {
                'data': phuquy_data,
                'price': phuquy_price,
                'unit': phuquy_unit
            },
            'international': {
                'gold': intl_data.get('gold'),
                'silver': intl_data.get('silver')
            },
            'tokenized': token_data,
            'spreads': {
                'gold': gold_spread,
                'silver': silver_spread
            }
        }

        # Cache result
        self.cached_data = result
        self.last_fetch = datetime.now()
        self._save_snapshot(result)

        return result

    def get_formatted_data(self) -> Dict:
        """
        Get formatted data ready for UI display

        Returns:
            Dict with formatted data for UI
        """
        data = self.fetch_all_data()
        intl_gold = data["international"]["gold"] if data.get("international") else None
        intl_silver = data["international"]["silver"] if data.get("international") else None
        paxg = (data.get("tokenized") or {}).get("paxg")
        xaut = (data.get("tokenized") or {}).get("xaut")

        return {
            'update_time': data['timestamp'],
            'usd_vnd': data['usd_vnd'],
            'sjc_gold_all': data['sjc'].get('data') if data.get('sjc') else None,
            'phuquy_silver_all': data['phuquy_silver'].get('data') if data.get('phuquy_silver') else None,

            # Gold (SJC)
            'sjc_gold': {
                'price': data['sjc']['price_1l_10l'],
                'unit': 'VND/lượng',
                'source': 'SJC'
            },

            # Silver (Phu Quý)
            'phuquy_silver': {
                'price': data['phuquy_silver']['price'],
                'unit': 'VND/lượng',
                'source': 'Phú Quý'
            },

            # International Gold
            'intl_gold': {
                'price': intl_gold['price'] if intl_gold else None,
                'change': intl_gold['change'] if intl_gold else None,
                'change_percent': intl_gold['change_percent'] if intl_gold else None,
                'unit': 'USD/oz',
                'source': intl_gold.get('source') if intl_gold else None
            },

            # International Silver
            'intl_silver': {
                'price': intl_silver['price'] if intl_silver else None,
                'change': intl_silver['change'] if intl_silver else None,
                'change_percent': intl_silver['change_percent'] if intl_silver else None,
                'unit': 'USD/oz',
                'source': intl_silver.get('source') if intl_silver else None
            },

            # Tokenized Gold (PAXG/XAUT)
            'paxg': {
                'price': paxg['price'] if isinstance(paxg, dict) else None,
                'change': paxg.get('change') if isinstance(paxg, dict) else None,
                'change_percent': paxg.get('change_percent') if isinstance(paxg, dict) else None,
                'unit': 'USD/oz',
                'source': paxg.get('source') if isinstance(paxg, dict) else None
            },
            'xaut': {
                'price': xaut['price'] if isinstance(xaut, dict) else None,
                'change': xaut.get('change') if isinstance(xaut, dict) else None,
                'change_percent': xaut.get('change_percent') if isinstance(xaut, dict) else None,
                'unit': 'USD/oz',
                'source': xaut.get('source') if isinstance(xaut, dict) else None
            },

            # Spreads
            'gold_spread': {
                'spread_vnd': data['spreads']['gold'].get('spread_vnd'),
                'spread_percent': data['spreads']['gold'].get('spread_percent'),
                'intl_in_vnd': data['spreads']['gold'].get('intl_in_vnd'),
                'intl_per_luong': data['spreads']['gold'].get('intl_per_luong')
            },

            'silver_spread': {
                'spread_vnd': data['spreads']['silver'].get('spread_vnd'),
                'spread_percent': data['spreads']['silver'].get('spread_percent'),
                'intl_in_vnd': data['spreads']['silver'].get('intl_in_vnd'),
                'intl_per_luong': data['spreads']['silver'].get('intl_per_luong'),
                'unit': 'VND/lượng',
            }
        }


if __name__ == "__main__":
    # Test
    print("Testing PriceDataFetcher...")
    print("=" * 50)

    fetcher = PriceDataFetcher()
    data = fetcher.get_formatted_data()

    print(f"\nUpdate Time: {data['update_time']}")
    print(f"USD/VND: {data['usd_vnd']}")

    print(f"\nSJC Gold: {data['sjc_gold']['price']} {data['sjc_gold']['unit']}")
    print(f"Phu Quý Silver: {data['phuquy_silver']['price']} {data['phuquy_silver']['unit']}")

    print(f"\nInternational Gold: ${data['intl_gold']['price']} {data['intl_gold']['unit']}")
    print(f"International Silver: ${data['intl_silver']['price']} {data['intl_silver']['unit']}")

    print(f"\nGold Spread: {data['gold_spread']['spread_vnd']} VND ({data['gold_spread']['spread_percent']}%)")
    print(f"Silver Spread: {data['silver_spread']['spread_vnd']} VND ({data['silver_spread']['spread_percent']}%)")
