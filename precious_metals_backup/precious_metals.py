"""
Module lấy giá vàng và bạc từ các nguồn dữ liệu
Nguồn chính: Yahoo Finance
Nguồn fallback: MSM (MarketSmith/MSN Money/etc.)
"""

import requests
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import time
import logging
from bs4 import BeautifulSoup
import json as json_module

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PreciousMetalsPrice:
    """Class để lấy và cache giá vàng và bạc"""

    def __init__(self, cache_duration: int = 300):
        """
        Args:
            cache_duration: Thời gian cache tính bằng giây (mặc định 5 phút)
        """
        self.cache = {}
        self.cache_duration = cache_duration

        # Symbol mapping
        self.symbols = {
            'gold': {
                'yahoo': 'GC=F',  # Gold Futures
                'yahoo_alt': 'GLD',  # SPDR Gold Shares ETF
                'msm_symbol': 'XAUUSD'  # MSM symbol
            },
            'silver': {
                'yahoo': 'SI=F',  # Silver Futures
                'yahoo_alt': 'SLV',  # iShares Silver Trust ETF
                'msm_symbol': 'XAGUSD'  # MSM symbol
            }
        }

    def _is_cache_valid(self, key: str) -> bool:
        """Kiểm tra cache còn hợp lệ không"""
        if key not in self.cache:
            return False

        cache_time = self.cache[key]['timestamp']
        return (datetime.now() - cache_time).total_seconds() < self.cache_duration

    def _update_cache(self, key: str, data: Dict):
        """Cập nhật cache"""
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }

    def _get_from_yahoo(self, metal: str) -> Optional[Dict]:
        """Lấy giá từ Yahoo Finance (nguồn chính)"""
        try:
            if metal not in self.symbols:
                logger.error(f"Invalid metal type: {metal}")
                return None

            symbol = self.symbols[metal]['yahoo']
            ticker = yf.Ticker(symbol)

            # Lấy thông tin nhanh
            info = ticker.info

            # Lấy lịch sử giá gần nhất
            hist = ticker.history(period="5d")

            if hist.empty:
                logger.warning(f"No data from Yahoo for {symbol}, trying alt symbol...")
                # Thử symbol thay thế (ETF)
                symbol_alt = self.symbols[metal]['yahoo_alt']
                ticker_alt = yf.Ticker(symbol_alt)
                info = ticker_alt.info
                hist = ticker_alt.history(period="5d")

            if hist.empty:
                logger.warning(f"No data from Yahoo for {metal}")
                return None

            # Lấy giá hiện tại và các thông tin khác
            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price

            # Tính thay đổi
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
        Lấy giá từ MSM (MarketSmith/MSN Money) - nguồn fallback

        MSM implementation options:
        1. MSN Money (web scraping) - không cần API key
        2. MarketSmith API - cần subscription và API key
        3. Custom MSM endpoint

        Args:
            metal: 'gold' hoặc 'silver'
            api_key: API key cho MarketSmith (nếu có)
        """
        try:
            if metal not in self.symbols:
                return None

            # Phương pháp 1: MSN Money scraping (không cần API key)
            result = self._get_from_msn_money(metal)
            if result:
                return result

            # Phương pháp 2: MarketSmith API (nếu có API key)
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
        Lấy giá từ MSN Money bằng web scraping

        Args:
            metal: 'gold' hoặc 'silver'
        """
        try:
            # MSN Money URLs cho gold và silver
            urls = {
                'gold': 'https://www.msn.com/en-us/money/markets/gold',
                'silver': 'https://www.msn.com/en-us/money/markets/silver'
            }

            if metal not in urls:
                return None

            url = urls[metal]
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # MSN Money thường có price trong script tags hoặc specific elements
                # Cần parse HTML để tìm price data

                # Thử tìm trong script tags (JSON data)
                scripts = soup.find_all('script', {'type': 'application/json'})
                for script in scripts:
                    try:
                        data = json_module.loads(script.string)
                        # Parse data để tìm price
                        # Cấu trúc có thể thay đổi, cần update thường xuyên
                        if 'price' in str(data).lower():
                            logger.info(f"Found data in script tag for {metal}")
                            # Extract and return price
                            # Implementation tùy vào structure thực tế
                    except:
                        continue

                # Fallback: Tìm price trong HTML elements
                price_elements = soup.find_all(['span', 'div'], class_=lambda x: x and 'price' in x.lower())
                if price_elements:
                    # Lấy element đầu tiên
                    price_text = price_elements[0].get_text()
                    # Parse price từ text
                    import re
                    price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                    if price_match:
                        price = float(price_match.group())
                        result = {
                            'source': 'MSN Money (Web Scraping)',
                            'symbol': self.symbols[metal]['msm_symbol'],
                            'price': price,
                            'change': 0,
                            'change_percent': 0,
                            'high': price,
                            'low': price,
                            'timestamp': datetime.now().isoformat()
                        }
                        logger.info(f"Successfully fetched {metal} price from MSN Money: {price}")
                        return result

            logger.warning(f"Could not parse MSN Money for {metal}")
            return None

        except Exception as e:
            logger.error(f"Error scraping MSN Money for {metal}: {str(e)}")
            return None

    def _get_from_marketsmith_api(self, metal: str, api_key: str) -> Optional[Dict]:
        """
        Lấy giá từ MarketSmith API (nếu có subscription)

        Args:
            metal: 'gold' hoặc 'silver'
            api_key: MarketSmith API key
        """
        try:
            # MarketSmith API endpoint (placeholder - cần thực tế endpoint)
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
        Lấy giá kim loại (vàng hoặc bạc)

        Args:
            metal: 'gold' hoặc 'silver'
            msm_api_key: API key cho MarketSmith (optional - không cần cho MSN Money)
            use_cache: Có sử dụng cache không

        Returns:
            Dict chứa thông tin giá hoặc None nếu thất bại
        """
        if metal not in ['gold', 'silver']:
            logger.error(f"Invalid metal type: {metal}. Use 'gold' or 'silver'")
            return None

        cache_key = f"{metal}_price"

        # Kiểm tra cache
        if use_cache and self._is_cache_valid(cache_key):
            logger.info(f"Using cached data for {metal}")
            return self.cache[cache_key]['data']

        # Thử nguồn chính: Yahoo Finance
        logger.info(f"Fetching {metal} price from primary source (Yahoo Finance)...")
        data = self._get_from_yahoo(metal)

        # Nếu thất bại, thử fallback: MSM (MSN Money)
        if data is None:
            logger.info(f"Primary source failed, trying fallback (MSN Money)...")
            data = self._get_from_msm(metal, msm_api_key)

        # Cập nhật cache nếu thành công
        if data:
            self._update_cache(cache_key, data)
            return data
        else:
            logger.error(f"Failed to fetch {metal} price from all sources")
            return None

    def get_all_prices(self, msm_api_key: Optional[str] = None, use_cache: bool = True) -> Dict[str, Optional[Dict]]:
        """
        Lấy giá cả vàng và bạc

        Args:
            msm_api_key: API key cho MarketSmith (optional - không cần cho MSN Money)
            use_cache: Có sử dụng cache không

        Returns:
            Dict với keys 'gold' và 'silver'
        """
        results = {
            'gold': self.get_price('gold', msm_api_key, use_cache),
            'silver': self.get_price('silver', msm_api_key, use_cache)
        }
        return results

    def clear_cache(self):
        """Xóa cache"""
        self.cache.clear()
        logger.info("Cache cleared")


# Convenience functions
def get_gold_price(msm_api_key: Optional[str] = None, use_cache: bool = True) -> Optional[Dict]:
    """Lấy giá vàng nhanh"""
    pm = PreciousMetalsPrice()
    return pm.get_price('gold', msm_api_key, use_cache)


def get_silver_price(msm_api_key: Optional[str] = None, use_cache: bool = True) -> Optional[Dict]:
    """Lấy giá bạc nhanh"""
    pm = PreciousMetalsPrice()
    return pm.get_price('silver', msm_api_key, use_cache)


def get_all_metals_prices(msm_api_key: Optional[str] = None, use_cache: bool = True) -> Dict[str, Optional[Dict]]:
    """Lấy giá cả vàng và bạc"""
    pm = PreciousMetalsPrice()
    return pm.get_all_prices(msm_api_key, use_cache)


if __name__ == "__main__":
    # Test
    print("Testing Precious Metals Price Module")
    print("=" * 50)

    pm = PreciousMetalsPrice()

    # Lấy giá vàng
    print("\nFetching Gold Price:")
    gold_price = pm.get_price('gold')
    if gold_price:
        print(f"Price: ${gold_price['price']}")
        print(f"Change: ${gold_price['change']} ({gold_price['change_percent']}%)")
        print(f"Source: {gold_price['source']}")

    # Lấy giá bạc
    print("\nFetching Silver Price:")
    silver_price = pm.get_price('silver')
    if silver_price:
        print(f"Price: ${silver_price['price']}")
        print(f"Change: ${silver_price['change']} ({silver_price['change_percent']}%)")
        print(f"Source: {silver_price['source']}")

    # Lấy tất cả
    print("\nFetching All Prices:")
    all_prices = pm.get_all_prices()
    print(f"Gold: ${all_prices['gold']['price'] if all_prices['gold'] else 'N/A'}")
    print(f"Silver: ${all_prices['silver']['price'] if all_prices['silver'] else 'N/A'}")
