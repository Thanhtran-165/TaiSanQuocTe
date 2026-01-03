#!/usr/bin/env python3
"""
Silver Price Scraper
Lấy giá bạc hàng ngày từ giabac.phuquygroup.vn (nguồn chính)
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
from typing import Dict, List, Optional
import os
import html

class SilverPriceScraper:
    """Class để scrape giá bạc từ multiple sources"""

    def __init__(self, output_dir: str = None):
        self.primary_source = "https://giabac.phuquygroup.vn"
        self.fallback_source = "https://topi.vn/gia-bac-hom-nay.html"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        # Set output directory
        if output_dir:
            self.output_dir = output_dir
        else:
            self.output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')

        os.makedirs(self.output_dir, exist_ok=True)

    @staticmethod
    def _clean_text(value: str) -> str:
        text = html.unescape(value or "")
        text = text.replace("\u00a0", " ")
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def get_from_primary_source(self) -> Optional[Dict]:
        """Lấy giá bạc từ giabac.phuquygroup.vn"""
        try:
            response = requests.get(self.primary_source, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Lấy thời gian cập nhật
            update_time_div = soup.find(id='update-datetime')
            time_elem = update_time_div.find(class_='time')
            date_elem = update_time_div.find(class_='date')

            if time_elem and date_elem:
                update_time = f"{time_elem.text.strip()} {date_elem.text.strip()}"
            else:
                update_time = "N/A"

            # Lấy bảng giá
            table = soup.find('table', class_='table-striped')
            if not table:
                print("❌ Không tìm thấy bảng giá")
                return None

            # Parse dữ liệu
            prices = []
            current_category = None

            for row in table.find_all('tr'):
                branch_title = row.find(class_='branch_title')
                if branch_title:
                    current_category = self._clean_text(branch_title.get_text(" ", strip=True))
                    continue

                # Skip header rows
                if row.find_all("th"):
                    continue

                cols = row.find_all('td')
                if len(cols) >= 4:
                    product = self._clean_text(cols[0].get_text(" ", strip=True))
                    unit = self._clean_text(cols[1].get_text(" ", strip=True))
                    buy_price = self._clean_text(cols[2].get_text(" ", strip=True))
                    sell_price = self._clean_text(cols[3].get_text(" ", strip=True))

                    if buy_price and buy_price != '-':
                        prices.append({
                            'category': current_category,
                            'product': product,
                            'type': product,  # compat: some consumers use 'type'
                            'unit': unit,
                            'buy_price': buy_price,
                            'sell_price': sell_price if sell_price and sell_price != '-' else 'N/A'
                        })

            products = sorted({p.get("product") for p in prices if p.get("product")})
            result = {
                'source': self.primary_source,
                'update_time': update_time,
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'prices': prices,
                'products': products,
            }

            print(f"✅ Đã lấy được {len(prices)} dòng giá")
            return result

        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return None

    def get_from_fallback_source(self) -> Optional[Dict]:
        """Lấy giá từ topi.vn (có Cloudflare Protection)"""
        try:
            print("⚠️  topi.vn có Cloudflare Protection - có thể không hoạt động")
            response = requests.get(self.fallback_source, headers=self.headers, timeout=10)

            if 'Just a moment' in response.text or 'cf_chl_opt' in response.text:
                print("❌ Cloudflare Protection detected!")
                return None

            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            tables = soup.find_all('table')
            if not tables:
                return None

            prices = []
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all(['td', 'th'])
                    if len(cols) >= 6:
                        text_content = [col.text.strip() for col in cols]
                        if 'Loại bạc' not in text_content[0]:
                            product = self._clean_text(text_content[0])
                            unit = self._clean_text(text_content[1])
                            hanoi_buy = self._clean_text(text_content[2])
                            hanoi_sell = self._clean_text(text_content[3])
                            hcmc_buy = self._clean_text(text_content[4])
                            hcmc_sell = self._clean_text(text_content[5])
                            prices.append({
                                'category': 'Thị trường',
                                'product': product,
                                'type': product,
                                'unit': unit,
                                # Provide a unified schema for consumers (prefer Hanoi columns).
                                'buy_price': hanoi_buy,
                                'sell_price': hanoi_sell,
                                'hanoi_buy': hanoi_buy,
                                'hanoi_sell': hanoi_sell,
                                'hcmc_buy': hcmc_buy,
                                'hcmc_sell': hcmc_sell,
                            })

            products = sorted({p.get("product") for p in prices if p.get("product")})
            result = {
                'source': self.fallback_source,
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'prices': prices,
                'products': products,
            }

            if len(prices) > 0:
                print(f"✅ Đã lấy được {len(prices)} dòng giá từ fallback")
            return result

        except Exception as e:
            print(f"❌ Lỗi fallback: {e}")
            return None

    def get_silver_prices(self) -> Dict:
        """Lấy giá bạc (primary + fallback)"""
        print("=" * 60)
        print("🥈 BẠC PRICE SCRAPER")
        print("=" * 60)

        result = self.get_from_primary_source()

        if not result or not result.get('prices'):
            print("⚠️  Đang thử fallback...")
            result = self.get_from_fallback_source()

            if not result or not result.get('prices'):
                return {
                    'success': False,
                    'error': 'Không thể lấy dữ liệu',
                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

        result['success'] = True
        return result

    def get_product_names(self) -> List[str]:
        """Lấy danh sách tên sản phẩm (unique) từ nguồn chính."""
        data = self.get_silver_prices()
        if not data or not data.get("success"):
            return []
        products = data.get("products")
        if isinstance(products, list) and products:
            return [p for p in products if isinstance(p, str) and p.strip()]
        # Back-compat: derive from prices if older payload
        names = []
        for item in data.get("prices") or []:
            name = item.get("product") or item.get("type")
            if isinstance(name, str) and name.strip():
                names.append(name.strip())
        return sorted(set(names))

    def print_prices(self, data: Dict):
        """In bảng giá"""
        if not data.get('success'):
            print(f"\n❌ LỖI: {data.get('error')}")
            return

        print("\n" + "=" * 80)
        print(f"📊 BẢNG GIÁ BẠC - {data['source']}")
        print(f"⏰ {data['update_time']}")
        print("=" * 80)

        print(f"{'Sản Phẩm':<40} {'Đơn Vị':<15} {'Giá Mua':<20} {'Giá Bán':<20}")
        print("-" * 95)

        current_category = None
        for item in data['prices']:
            if item.get('category') and item['category'] != current_category:
                current_category = item['category']
                print(f"\n【{current_category}】")

            sell = item['sell_price'] if item['sell_price'] != 'N/A' else '-'
            print(f"{item['product']:<40} {item['unit']:<15} {item['buy_price']:<20} {sell:<20}")

        print("\n" + "=" * 80)

    def save_to_json(self, data: Dict, filename: str = None):
        """Lưu vào JSON"""
        if not filename:
            filename = f"silver_prices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = os.path.join(self.output_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"💾 Đã lưu vào: {filepath}")
        except Exception as e:
            print(f"❌ Lỗi lưu file: {e}")


def main():
    scraper = SilverPriceScraper()
    data = scraper.get_silver_prices()
    scraper.print_prices(data)
    scraper.save_to_json(data, 'silver_prices.json')
    return data


if __name__ == "__main__":
    main()
