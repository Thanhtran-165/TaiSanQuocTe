#!/usr/bin/env python3
"""
Ví dụ sử dụng Silver Price Scraper trong production
"""

import sys
import os

# Add parent directory to path to import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.silver_scraper import SilverPriceScraper
import json
from datetime import datetime

def example_basic_usage():
    """Ví dụ cơ bản: Lấy và in giá bạc"""
    print("\n" + "="*60)
    print("VÍ DỤ 1: Sử dụng cơ bản")
    print("="*60 + "\n")

    scraper = SilverPriceScraper()
    data = scraper.get_silver_prices()

    if data['success']:
        print(f"✅ Thành công! Lấy được {len(data['prices'])} dòng giá")
        print(f"⏰ Cập nhật lúc: {data['update_time']}")
    else:
        print(f"❌ Thất bại: {data.get('error')}")

def example_filter_specific_product():
    """Ví dụ: Lọc sản phẩm cụ thể"""
    print("\n" + "="*60)
    print("VÍ DỤ 2: Lọc sản phẩm cụ thể")
    print("="*60 + "\n")

    scraper = SilverPriceScraper()
    data = scraper.get_silver_prices()

    if data['success']:
        # Tìm giá bạc miếng 1 lượng
        for item in data['prices']:
            if 'BẠC MIẾNG' in item['product'] and '1 LƯỢNG' in item['product']:
                print(f"🎯 {item['product']}")
                print(f"   Giá mua: {item['buy_price']} VNĐ")
                print(f"   Giá bán: {item['sell_price']} VNĐ")
                break

def example_save_to_database():
    """Ví dụ: Lưu vào database (giả lập)"""
    print("\n" + "="*60)
    print("VÍ DỤ 3: Lưu vào database")
    print("="*60 + "\n")

    scraper = SilverPriceScraper()
    data = scraper.get_silver_prices()

    if data['success']:
        # Giả lập lưu vào DB
        print("📦 Đang lưu dữ liệu vào database...")
        for item in data['prices']:
            # Giả lập INSERT query
            sql = f"""INSERT INTO silver_prices (
                product_name, unit, buy_price, sell_price,
                update_time, scraped_at, source
            ) VALUES (
                '{item['product']}', '{item['unit']}',
                {item['buy_price'].replace(',', '')},
                {item['sell_price'].replace(',', '') if item['sell_price'] != 'N/A' else 'NULL'},
                '{data['update_time']}', '{data['scraped_at']}', '{data['source']}'
            )"""
            print(f"✓ Saved: {item['product'][:30]}...")

def example_price_comparison():
    """Ví dụ: So sánh giá các loại bạc"""
    print("\n" + "="*60)
    print("VÍ DỤ 4: So sánh giá các loại bạc")
    print("="*60 + "\n")

    scraper = SilverPriceScraper()
    data = scraper.get_silver_prices()

    if data['success']:
        print(f"{'Sản phẩm':<40} {'Giá mua':<15} {'Giá bán':<15} {'Chênh lệch':<15}")
        print("-" * 85)

        for item in data['prices']:
            if item['sell_price'] != 'N/A':
                # Tính chênh lệch
                buy = int(item['buy_price'].replace(',', ''))
                sell = int(item['sell_price'].replace(',', ''))
                diff = sell - buy
                diff_str = f"{diff:,}"

                print(f"{item['product']:<40} {item['buy_price']:<15} "
                      f"{item['sell_price']:<15} {diff_str:<15}")

def example_alert_on_price_change():
    """Ví dụ: Cảnh báo khi giá thay đổi"""
    print("\n" + "="*60)
    print("VÍ DỤ 5: Cảnh báo giá thay đổi")
    print("="*60 + "\n")

    scraper = SilverPriceScraper()
    data = scraper.get_silver_prices()

    # Giả lập giá trước đó
    previous_price = 2700000  # 2,700,000

    if data['success']:
        for item in data['prices']:
            if 'BẠC MIẾNG' in item['product'] and '1 LƯỢNG' in item['product']:
                current_price = int(item['buy_price'].replace(',', ''))

                if current_price > previous_price:
                    increase = current_price - previous_price
                    percent = (increase / previous_price) * 100
                    print(f"🔺 GIÁ TĂNG!")
                    print(f"   Trước: {previous_price:,} VNĐ")
                    print(f"   Hiện tại: {current_price:,} VNĐ")
                    print(f"   Tăng {increase:,} VNĐ ({percent:.2f}%)")
                elif current_price < previous_price:
                    decrease = previous_price - current_price
                    percent = (decrease / previous_price) * 100
                    print(f"🔻 GIẢM GIÁ!")
                    print(f"   Trước: {previous_price:,} VNĐ")
                    print(f"   Hiện tại: {current_price:,} VNĐ")
                    print(f"   Giảm {decrease:,} VNĐ ({percent:.2f}%)")
                else:
                    print(f"➡️  GIÁ KHÔNG ĐỔI: {current_price:,} VNĐ")
                break

def example_export_to_csv():
    """Ví dụ: Xuất ra CSV"""
    print("\n" + "="*60)
    print("VÍ DỤ 6: Xuất ra CSV")
    print("="*60 + "\n")

    scraper = SilverPriceScraper()
    data = scraper.get_silver_prices()

    if data['success']:
        filename = f"silver_prices_{datetime.now().strftime('%Y%m%d')}.csv"

        # Lưu vào output directory
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            # Header
            f.write("Category,Product,Unit,Buy Price,Sell Price,Update Time\n")

            # Data rows
            for item in data['prices']:
                f.write(f"{item['category']},{item['product']},{item['unit']},"
                       f"{item['buy_price']},{item['sell_price']},{data['update_time']}\n")

        print(f"✅ Đã export {len(data['prices'])} dòng vào {filepath}")

def main():
    """Chạy tất cả các ví dụ"""
    print("\n" + "="*60)
    print("🥈 SILVER PRICE SCRAPER - PRODUCTION EXAMPLES")
    print("="*60)

    # Chạy các ví dụ
    example_basic_usage()
    example_filter_specific_product()
    example_save_to_database()
    example_price_comparison()
    example_alert_on_price_change()
    example_export_to_csv()

    print("\n" + "="*60)
    print("✅ TẤT CẢ VÍ DỤ ĐÃ CHẠY XONG!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
