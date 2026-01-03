"""
Core module for fetching precious metals prices
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import time
import logging
from bs4 import BeautifulSoup
import json as json_module
import uuid
import csv
import io

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PreciousMetalsPrice:
    """Class to fetch and cache gold and silver prices"""

    def __init__(self, cache_duration: int = 300, primary_source: str = "msn"):
        """
        Args:
            cache_duration: Cache duration in seconds (default: 5 minutes)
            primary_source: 'msn' or 'yahoo' (default: 'msn')
        """
        self.cache = {}
        self.cache_duration = cache_duration
        self.primary_source = primary_source.lower().strip()
        self._msn_state_cache: Optional[Dict] = None
        self._msn_state_cached_at: Optional[datetime] = None
        self._msn_state_failed_at: Optional[datetime] = None
        self._msn_state_fail_reason: Optional[str] = None

        # Symbol mapping
        self.symbols = {
            'gold': {
                'yahoo': 'GC=F',  # Gold Futures
                'yahoo_alt': 'GLD',  # SPDR Gold Shares ETF
                'msm_symbol': 'XAUUSD',  # MSM symbol
                'stooq': 'gc.f',  # Stooq Gold Futures
            },
            'silver': {
                'yahoo': 'SI=F',  # Silver Futures
                'yahoo_alt': 'SLV',  # iShares Silver Trust ETF
                'msm_symbol': 'XAGUSD',  # MSM symbol
                'stooq': 'si.f',  # Stooq Silver Futures
            }
        }

    def _is_msn_state_cache_valid(self) -> bool:
        if self._msn_state_cache is None or self._msn_state_cached_at is None:
            return False
        # Keep this short so we don't show stale intraday moves, but still reduce flakiness.
        ttl = max(10, min(60, int(self.cache_duration)))
        return (datetime.now() - self._msn_state_cached_at).total_seconds() < ttl

    def _fetch_msn_redux_state(self) -> Optional[Dict]:
        if self._is_msn_state_cache_valid():
            return self._msn_state_cache

        # Avoid hammering MSN if it's temporarily serving shell pages.
        if self._msn_state_failed_at is not None:
            if (datetime.now() - self._msn_state_failed_at).total_seconds() < 20:
                return None

        url = "https://www.msn.com/en-us/money"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "no-cache",
        }

        response_text = None
        attempt_params = [
            lambda: {"ocid": "msn", "cvid": uuid.uuid4().hex},
            lambda: {"ocid": "msn"},
            lambda: {"cvid": uuid.uuid4().hex},
            lambda: {},
        ]

        for _ in range(16):
            params = attempt_params[_ % len(attempt_params)]()
            try:
                resp = requests.get(url, headers=headers, params=params, timeout=15)
            except Exception:
                continue
            if resp.status_code != 200:
                continue
            if 'id="redux-data"' not in resp.text:
                continue
            response_text = resp.text
            break

        if response_text is None:
            self._msn_state_failed_at = datetime.now()
            self._msn_state_fail_reason = "no redux-data SSR payload"
            logger.warning("MSN Money did not return a redux-data SSR payload after retries")
            return None

        soup = BeautifulSoup(response_text, "html.parser")
        redux_script = soup.find("script", {"id": "redux-data"})
        if not redux_script or not redux_script.string:
            self._msn_state_failed_at = datetime.now()
            self._msn_state_fail_reason = "missing redux-data script"
            logger.warning("MSN Money landing page missing redux-data script")
            return None

        try:
            state = json_module.loads(redux_script.string)
        except Exception as e:
            self._msn_state_failed_at = datetime.now()
            self._msn_state_fail_reason = f"json parse error: {e}"
            logger.warning(f"Failed to parse MSN redux-data JSON: {e}")
            return None

        self._msn_state_cache = state
        self._msn_state_cached_at = datetime.now()
        self._msn_state_failed_at = None
        self._msn_state_fail_reason = None
        return state

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache is still valid"""
        if key not in self.cache:
            return False

        cache_time = self.cache[key]['timestamp']
        return (datetime.now() - cache_time).total_seconds() < self.cache_duration

    def _update_cache(self, key: str, data: Dict):
        """Update cache"""
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }

    def _get_from_yahoo(self, metal: str) -> Optional[Dict]:
        """Fetch price from Yahoo Finance (primary source)"""
        try:
            try:
                import yfinance as yf  # Optional dependency (only needed for Yahoo)
            except ModuleNotFoundError:
                logger.warning("yfinance is not installed; skipping Yahoo Finance source")
                return None

            if metal not in self.symbols:
                logger.error(f"Invalid metal type: {metal}")
                return None

            symbol = self.symbols[metal]['yahoo']
            ticker = yf.Ticker(symbol)

            # Get quick info
            info = ticker.info

            # Get recent price history
            hist = ticker.history(period="5d")

            if hist.empty:
                logger.warning(f"No data from Yahoo for {symbol}, trying alt symbol...")
                # Try alternative symbol (ETF)
                symbol_alt = self.symbols[metal]['yahoo_alt']
                ticker_alt = yf.Ticker(symbol_alt)
                info = ticker_alt.info
                hist = ticker_alt.history(period="5d")

            if hist.empty:
                logger.warning(f"No data from Yahoo for {metal}")
                return None

            # Get current price and other info
            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price

            # Calculate change
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100 if prev_close != 0 else 0

            result = {
                'source': 'Yahoo Finance',
                'symbol': symbol,
                'price': round(float(current_price), 2),
                'change': round(float(change), 2),
                'change_percent': round(float(change_percent), 2),
                'high': round(float(hist['High'].iloc[-1]), 2),
                'low': round(float(hist['Low'].iloc[-1]), 2),
                'volume': int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0,
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"Successfully fetched {metal} price from Yahoo: {result['price']}")
            return result

        except Exception as e:
            logger.error(f"Error fetching from Yahoo Finance for {metal}: {str(e)}")
            return None

    def _get_from_msm(self, metal: str, api_key: Optional[str] = None) -> Optional[Dict]:
        """
        Fetch price from MSM (MarketSmith/MSN Money) - fallback source

        MSM implementation options:
        1. MSN Money (web scraping) - no API key needed
        2. MarketSmith API - requires subscription and API key
        3. Custom MSM endpoint

        Args:
            metal: 'gold' or 'silver'
            api_key: MarketSmith API key (if available)
        """
        try:
            if metal not in self.symbols:
                return None

            # Method 1: MSN Money scraping (no API key needed)
            result = self._get_from_msn_money(metal)
            if result:
                return result

            # Method 2: MarketSmith API (if API key is provided)
            if api_key:
                result = self._get_from_marketsmith_api(metal, api_key)
                if result:
                    return result

            logger.warning(f"MSM methods failed for {metal}")
            return None

        except Exception as e:
            logger.error(f"Error fetching from MSM for {metal}: {str(e)}")
            return None

    def _get_from_msn_money(self, metal: str) -> Optional[Dict]:
        """
        Fetch price from MSN Money by parsing embedded redux state on https://www.msn.com/en-us/money.

        Note: MSN pages are heavily client-rendered; many deep URLs 404 or change often. The landing
        page includes a `script#redux-data` JSON blob containing commodity futures quotes (COMEX)
        for Gold and Silver, including price and change values.

        Args:
            metal: 'gold' or 'silver'
        """
        try:
            if metal not in ["gold", "silver"]:
                return None

            state = self._fetch_msn_redux_state()
            if state is None:
                return None

            target_name = "Gold" if metal == "gold" else "Silver"

            def iter_dicts(obj):
                if isinstance(obj, dict):
                    yield obj
                    for v in obj.values():
                        yield from iter_dicts(v)
                elif isinstance(obj, list):
                    for v in obj:
                        yield from iter_dicts(v)

            candidates = []
            for d in iter_dicts(state):
                if d.get("displayName") != target_name:
                    continue
                price = d.get("priceNumber")
                if not isinstance(price, (int, float)):
                    continue
                if d.get("currency") and d.get("currency") != "USD":
                    continue
                candidates.append(d)

            if not candidates:
                logger.warning(f"MSN redux-data did not contain quote for {target_name}")
                return None

            # Prefer futures (COMEX) if multiple entries exist.
            chosen = None
            for d in candidates:
                if d.get("securityType") == "future" and d.get("exchangeName") == "COMEX":
                    chosen = d
                    break
            if chosen is None:
                chosen = candidates[0]

            price = float(chosen.get("priceNumber"))
            change = chosen.get("changeValueNumber")
            change_pct = chosen.get("changePcntNumber")
            updated = (
                (chosen.get("timeLastUpdated") or {}).get("dataValue")
                or datetime.now().isoformat()
            )

            result = {
                "source": "MSN Money",
                "symbol": chosen.get("symbol") or self.symbols[metal]["msm_symbol"],
                "msn_id": chosen.get("id"),
                "exchange": chosen.get("exchangeName"),
                "security_type": chosen.get("securityType"),
                "price": round(price, 2),
                "change": round(float(change), 2) if isinstance(change, (int, float)) else 0.0,
                "change_percent": round(float(change_pct), 2) if isinstance(change_pct, (int, float)) else 0.0,
                "high": round(price, 2),
                "low": round(price, 2),
                "timestamp": updated,
            }

            logger.info(f"Successfully fetched {metal} price from MSN Money: {result['price']}")
            return result

        except Exception as e:
            logger.error(f"Error scraping MSN Money for {metal}: {str(e)}")
            return None

    def _get_from_stooq(self, metal: str) -> Optional[Dict]:
        """
        Fetch futures price from Stooq (CSV endpoint) - no API key.

        Uses:
        - Gold futures: gc.f
        - Silver futures: si.f
        """
        try:
            if metal not in self.symbols:
                return None

            symbol = self.symbols[metal].get("stooq")
            if not symbol:
                return None

            url = f"https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlcv&h&e=csv"
            headers = {"User-Agent": "Mozilla/5.0", "Accept": "text/csv,*/*"}
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200 or not resp.text:
                return None

            reader = csv.DictReader(io.StringIO(resp.text))
            row = next(reader, None)
            if not row:
                return None

            close = row.get("Close")
            if not close or close.upper() == "N/A":
                return None

            close_f = float(close)
            open_v = row.get("Open")
            high_v = row.get("High")
            low_v = row.get("Low")
            volume_v = row.get("Volume")

            open_f = float(open_v) if open_v and open_v.upper() != "N/A" else close_f
            high_f = float(high_v) if high_v and high_v.upper() != "N/A" else close_f
            low_f = float(low_v) if low_v and low_v.upper() != "N/A" else close_f
            vol_i = int(float(volume_v)) if volume_v and volume_v.upper() != "N/A" else 0

            change = close_f - open_f
            change_percent = (change / open_f) * 100 if open_f else 0.0

            date = row.get("Date") or ""
            t = row.get("Time") or ""
            timestamp = f"{date}T{t}Z" if date and t else datetime.now().isoformat()

            return {
                "source": "Stooq",
                "symbol": symbol.upper(),
                "price": round(close_f, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "high": round(high_f, 2),
                "low": round(low_f, 2),
                "volume": vol_i,
                "timestamp": timestamp,
            }
        except Exception as e:
            logger.error(f"Error fetching from Stooq for {metal}: {str(e)}")
            return None

    def _get_from_marketsmith_api(self, metal: str, api_key: str) -> Optional[Dict]:
        """
        Fetch price from MarketSmith API (if subscription is available)

        Args:
            metal: 'gold' or 'silver'
            api_key: MarketSmith API key
        """
        try:
            # MarketSmith API endpoint (placeholder - needs actual endpoint)
            base_url = "https://api.marketsmith.com/v1"  # Placeholder

            symbol = self.symbols[metal]['msm_symbol']
            url = f"{base_url}/quotes/{symbol}"

            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()

                result = {
                    'source': 'MarketSmith API',
                    'symbol': symbol,
                    'price': round(float(data.get('price', 0)), 2),
                    'change': round(float(data.get('change', 0)), 2),
                    'change_percent': round(float(data.get('changePercent', 0)), 2),
                    'high': round(float(data.get('high', 0)), 2),
                    'low': round(float(data.get('low', 0)), 2),
                    'timestamp': datetime.now().isoformat()
                }

                logger.info(f"Successfully fetched {metal} price from MarketSmith: {result['price']}")
                return result
            else:
                logger.warning(f"MarketSmith API returned status {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error fetching from MarketSmith API for {metal}: {str(e)}")
            return None

    def get_price(self, metal: str, msm_api_key: Optional[str] = None, use_cache: bool = True) -> Optional[Dict]:
        """
        Fetch metal price (gold or silver)

        Args:
            metal: 'gold' or 'silver'
            msm_api_key: MarketSmith API key (optional - not needed for MSN Money)
            use_cache: Whether to use cache

        Returns:
            Dict with price info or None if failed
        """
        if metal not in ['gold', 'silver']:
            logger.error(f"Invalid metal type: {metal}. Use 'gold' or 'silver'")
            return None

        cache_key = f"{metal}_price"

        # Check cache
        if use_cache and self._is_cache_valid(cache_key):
            logger.info(f"Using cached data for {metal}")
            return self.cache[cache_key]['data']

        if self.primary_source not in {"msn", "stooq", "yahoo"}:
            logger.warning(f"Invalid primary_source='{self.primary_source}', defaulting to 'msn'")
            self.primary_source = "msn"

        # Try primary source first, then fallback
        if self.primary_source == "msn":
            logger.info(f"Fetching {metal} price from primary source (MSN Money)...")
            data = self._get_from_msn_money(metal)
            if data is None:
                logger.info("Primary source failed, trying fallback (Stooq)...")
                data = self._get_from_stooq(metal)
            if data is None:
                logger.info("Fallback failed, trying Yahoo Finance...")
                data = self._get_from_yahoo(metal)
        elif self.primary_source == "stooq":
            logger.info(f"Fetching {metal} price from primary source (Stooq)...")
            data = self._get_from_stooq(metal)
            if data is None:
                logger.info("Primary source failed, trying fallback (MSN Money)...")
                data = self._get_from_msn_money(metal)
            if data is None:
                logger.info("Fallback failed, trying Yahoo Finance...")
                data = self._get_from_yahoo(metal)
        else:
            logger.info(f"Fetching {metal} price from primary source (Yahoo Finance)...")
            data = self._get_from_yahoo(metal)
            if data is None:
                logger.info("Primary source failed, trying fallback (MSN Money)...")
                data = self._get_from_msm(metal, msm_api_key)

        # Update cache if successful
        if data:
            self._update_cache(cache_key, data)
            return data
        else:
            logger.error(f"Failed to fetch {metal} price from all sources")
            return None

    def get_all_prices(self, msm_api_key: Optional[str] = None, use_cache: bool = True) -> Dict[str, Optional[Dict]]:
        """
        Fetch both gold and silver prices

        Args:
            msm_api_key: MarketSmith API key (optional - not needed for MSN Money)
            use_cache: Whether to use cache

        Returns:
            Dict with keys 'gold' and 'silver'
        """
        results = {
            'gold': self.get_price('gold', msm_api_key, use_cache),
            'silver': self.get_price('silver', msm_api_key, use_cache)
        }
        return results

    def clear_cache(self):
        """Clear cache"""
        self.cache.clear()
        logger.info("Cache cleared")


# Convenience functions
def get_gold_price(msm_api_key: Optional[str] = None, use_cache: bool = True) -> Optional[Dict]:
    """Quick fetch gold price"""
    pm = PreciousMetalsPrice()
    return pm.get_price('gold', msm_api_key, use_cache)


def get_silver_price(msm_api_key: Optional[str] = None, use_cache: bool = True) -> Optional[Dict]:
    """Quick fetch silver price"""
    pm = PreciousMetalsPrice()
    return pm.get_price('silver', msm_api_key, use_cache)


def get_all_metals_prices(msm_api_key: Optional[str] = None, use_cache: bool = True) -> Dict[str, Optional[Dict]]:
    """Quick fetch both gold and silver prices"""
    pm = PreciousMetalsPrice()
    return pm.get_all_prices(msm_api_key, use_cache)


if __name__ == "__main__":
    # Test
    print("Testing Precious Metals Price Module")
    print("=" * 50)

    pm = PreciousMetalsPrice()

    # Fetch gold price
    print("\nFetching Gold Price:")
    gold_price = pm.get_price('gold')
    if gold_price:
        print(f"Price: ${gold_price['price']}")
        print(f"Change: ${gold_price['change']} ({gold_price['change_percent']}%)")
        print(f"Source: {gold_price['source']}")

    # Fetch silver price
    print("\nFetching Silver Price:")
    silver_price = pm.get_price('silver')
    if silver_price:
        print(f"Price: ${silver_price['price']}")
        print(f"Change: ${silver_price['change']} ({silver_price['change_percent']}%)")
        print(f"Source: {silver_price['source']}")

    # Fetch all
    print("\nFetching All Prices:")
    all_prices = pm.get_all_prices()
    print(f"Gold: ${all_prices['gold']['price'] if all_prices['gold'] else 'N/A'}")
    print(f"Silver: ${all_prices['silver']['price'] if all_prices['silver'] else 'N/A'}")
