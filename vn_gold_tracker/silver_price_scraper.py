#!/usr/bin/env python3
"""
Silver Price Scraper
Lấy giá bạc hàng ngày từ giabac.phuquygroup.vn (nguồn chính)
và topi.vn (fallback)"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
from typing import Dict, List, Optional

class SilverPriceScraper:
    """Class để scrape giá bạc từ multiple sources"""

    def __init__(self):
        self.primary_source = "https://giabac.phuquygroup.vn"
        self.fallback_source = "https://topi.vn/gia-bac-hom-nay.html"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def get_from_primary_source(self) -> Optional[Dict]:
        """
        Lấy giá bạc từ giabac.phuquygroup.vn (nguồn chính)
        Returns: Dict hoặc None nếu thất bại
        """
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
                print("❌ Không tìm thấy bảng giá ở nguồn chính")
                return None

            # Parse dữ liệu từ table
            prices = []
            current_category = None

            for row in table.find_all('tr'):
                # Kiểm tra nếu là dòng category header
                branch_title = row.find(class_='branch_title')
                if branch_title:
                    current_category = branch_title.text.strip()
                    continue

                # Parse dòng sản phẩm
                cols = row.find_all('td')
                if len(cols) >= 4:
                    product = cols[0].text.strip()
                    # Decode HTML entities
                    product = product.replace('&#218;', 'Ú').replace('&#221;', 'Ú')

                    unit = cols[1].text.strip()
                    buy_price = cols[2].text.strip()
                    sell_price = cols[3].text.strip()

                    # Chỉ thêm dòng có dữ liệu giá
                    if buy_price and buy_price != '-':
                        prices.append({
                            'category': current_category,
                            'product': product,
                            'unit': unit,
                            'buy_price': buy_price,
                            'sell_price': sell_price if sell_price and sell_price != '-' else 'N/A'
                        })

            result = {
                'source': self.primary_source,
                'update_time': update_time,
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'prices': prices
            }

            print(f"✅ Đã lấy được {len(prices)} dòng giá từ nguồn chính")
            return result

        except requests.RequestException as e:
            print(f"❌ Lỗi kết nối nguồn chính: {e}")
            return None
        except Exception as e:
            print(f"❌ Lỗi parse nguồn chính: {e}")
            return None

    def get_from_fallback_source(self) -> Optional[Dict]:
        """
        Lấy giá bạc từ topi.vn (fallback)
        WARNING: Trang này có Cloudflare Protection, có thể không hoạt động
        Returns: Dict hoặc None nếu thất bại
        """
        try:
            print("⚠️  WARNING: topi.vn có Cloudflare Protection")
            print("⚠️  Fallback có thể KHÔNG HOẠT ĐỘNG với requests thông thường")

            response = requests.get(self.fallback_source, headers=self.headers, timeout=10)

            # Kiểm tra nếu gặp Cloudflare challenge
            if 'Just a moment' in response.text or 'cf_chl_opt' in response.text:
                print("❌ Cloudflare Protection detected!")
                print("❌ Không thể scrape topi.vn bằng requests thông thường")
                print("💡 Đề xuất: Chỉ dùng nguồn chính (giabac.phuquygroup.vn)")
                return None

            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Tìm tất cả các table trong bài viết
            tables = soup.find_all('table')
            if not tables:
                print("❌ Không tìm thấy bảng giá ở nguồn fallback")
                return None

            prices = []
            update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Parse table giá bạc (table đầu tiên thường là giá Hà Nội & HCM)
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all(['td', 'th'])
                    if len(cols) >= 6:
                        text_content = [col.text.strip() for col in cols]

                        # Skip header rows
                        if 'Loại bạc' in text_content[0] or 'Đơn vị' in text_content[0]:
                            continue

                        # Parse dòng giá
                        product = text_content[0]
                        unit = text_content[1]

                        # Giá Hà Nội
                        hanoi_buy = text_content[2] if len(text_content) > 2 else 'N/A'
                        hanoi_sell = text_content[3] if len(text_content) > 3 else 'N/A'

                        # Giá TP.HCM
                        hcmc_buy = text_content[4] if len(text_content) > 4 else 'N/A'
                        hcmc_sell = text_content[5] if len(text_content) > 5 else 'N/A'

                        # Chỉ thêm dòng có dữ liệu
                        if product and product not in ['Loại bạc', 'Đơn vị']:
                            prices.append({
                                'category': 'Thị trường',
                                'product': product,
                                'unit': unit,
                                'hanoi_buy': hanoi_buy,
                                'hanoi_sell': hanoi_sell,
                                'hcmc_buy': hcmc_buy,
                                'hcmc_sell': hcmc_sell
                            })

            result = {
                'source': self.fallback_source,
                'update_time': update_time,
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'prices': prices
            }

            if len(prices) > 0:
                print(f"✅ Đã lấy được {len(prices)} dòng giá từ nguồn fallback")
            else:
                print("⚠️  Fallback trả về nhưng không có dữ liệu")

            return result

        except requests.RequestException as e:
            print(f"❌ Lỗi kết nối nguồn fallback: {e}")
            print("💡 Khả năng cao do Cloudflare Protection")
            return None
        except Exception as e:
            print(f"❌ Lỗi parse nguồn fallback: {e}")
            return None

    def get_silver_prices(self) -> Dict:
        """
        Lấy giá bạc từ nguồn chính, nếu thất bại thì dùng fallback
        Returns: Dict với dữ liệu giá
        """
        print("=" * 60)
        print("🥈 BẠC PRICE SCRAPER")
        print("=" * 60)
        print(f"⏰ Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Thử nguồn chính trước
        print("📍 Đang thử nguồn chính: giabac.phuquygroup.vn")
        result = self.get_from_primary_source()

        # Nếu nguồn chính thất bại, dùng fallback
        if not result or not result.get('prices'):
            print("⚠️  Nguồn chính thất bại, đang thử fallback...")
            result = self.get_from_fallback_source()

            if not result or not result.get('prices'):
                print("❌ Cả hai nguồn đều thất bại!")
                return {
                    'success': False,
                    'error': 'Không thể lấy dữ liệu từ cả hai nguồn',
                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

        result['success'] = True
        return result

    def print_prices(self, data: Dict):
        """In dữ liệu giá ra console theo format đẹp"""
        if not data.get('success'):
            print(f"\n❌ LỖI: {data.get('error')}")
            return

        print("\n" + "=" * 80)
        print(f"📊 BẢNG GIÁ BẠC - Nguồn: {data['source'].replace('https://', '')}")
        print(f"⏰ Cập nhật: {data['update_time']}")
        print("=" * 80)

        if 'hcmc_buy' in data['prices'][0]:
            # Format cho topi.vn
            print(f"{'Sản Phẩm':<30} {'Đơn Vị':<15} {'HN Mua':<15} {'HN Bán':<15} {'HCM Mua':<15} {'HCM Bán':<15}")
            print("-" * 105)
            for item in data['prices']:
                print(f"{item['product']:<30} {item['unit']:<15} {item['hanoi_buy']:<15} "
                      f"{item['hanoi_sell']:<15} {item['hcmc_buy']:<15} {item['hcmc_sell']:<15}")
        else:
            # Format cho giabac.phuquygroup.vn
            print(f"{'Sản Phẩm':<40} {'Đơn Vị':<15} {'Giá Mua':<20} {'Giá Bán':<20}")
            print("-" * 95)

            current_category = None
            for item in data['prices']:
                if item.get('category') and item['category'] != current_category:
                    current_category = item['category']
                    print(f"\n【{current_category}】")

                buy_price = item['buy_price']
                sell_price = item['sell_price'] if item['sell_price'] != 'N/A' else '-'
                print(f"{item['product']:<40} {item['unit']:<15} {buy_price:<20} {sell_price:<20}")

        print("\n" + "=" * 80)

    def save_to_json(self, data: Dict, filename: str = None):
        """Lưu dữ liệu vào file JSON"""
        if not filename:
            filename = f"silver_prices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"💾 Đã lưu dữ liệu vào: {filename}")
        except Exception as e:
            print(f"❌ Lỗi lưu file: {e}")


def main():
    """Main function"""
    scraper = SilverPriceScraper()

    # Lấy giá
    data = scraper.get_silver_prices()

    # In ra console
    scraper.print_prices(data)

    # Lưu vào JSON
    scraper.save_to_json(data, 'silver_prices.json')

    # Return data for programmatic use
    return data


if __name__ == "__main__":
    main()
