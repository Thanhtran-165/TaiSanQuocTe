"""
DEMO: Scrape giá vàng từ phuquygroup.vn
Dùng làm fallback khi vnstock thất bại
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime


def get_sjc_gold_price_from_phuquy():
    """
    Lấy giá vàng SJC từ phuquygroup.vn

    Returns:
        pd.DataFrame: DataFrame với các cột:
            - name: Tên loại vàng
            - buy_price: Giá mua vào (VNĐ/chỉ)
            - sell_price: Giá bán ra (VNĐ/chỉ)
    """
    url = "https://phuquygroup.vn"

    try:
        # Gửi request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Tìm bảng giá
        table = soup.find('table', class_='m-auto text-center')
        if not table:
            print("❌ Không tìm thấy bảng giá")
            return pd.DataFrame()

        # Extract dữ liệu từ tbody
        tbody = table.find('tbody')
        if not tbody:
            print("❌ Không tìm thấy tbody")
            return pd.DataFrame()

        data = []
        rows = tbody.find_all('tr')

        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                name = cols[0].get_text(strip=True)
                buy_price = cols[1].get_text(strip=True).replace(',', '')
                sell_price = cols[2].get_text(strip=True).replace(',', '')

                # Chỉ lấy dòng "Vàng miếng SJC"
                if "Vàng miếng SJC" in name:
                    data.append({
                        'name': name,
                        'buy_price': buy_price if buy_price else None,
                        'sell_price': sell_price if sell_price else None,
                        'source': 'phuquygroup.vn',
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    break  # Chỉ cần 1 dòng SJC

        if not data:
            print("❌ Không tìm thấy dòng 'Vàng miếng SJC'")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        print(f"✅ Đã lấy giá vàng SJC từ phuquygroup.vn")
        return df

    except requests.RequestException as e:
        print(f"❌ Lỗi request: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return pd.DataFrame()


def get_all_gold_prices_from_phuquy():
    """
    Lấy TẤT CẢ các loại giá vàng từ phuquygroup.vn
    (không chỉ SJC)

    Returns:
        pd.DataFrame: Tất cả các loại giá vàng
    """
    url = "https://phuquygroup.vn"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', class_='m-auto text-center')

        if not table:
            return pd.DataFrame()

        tbody = table.find('tbody')
        if not tbody:
            return pd.DataFrame()

        data = []
        rows = tbody.find_all('tr')

        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                name = cols[0].get_text(strip=True)
                buy_price = cols[1].get_text(strip=True).replace(',', '')
                sell_price = cols[2].get_text(strip=True).replace(',', '')

                data.append({
                    'name': name,
                    'buy_price': buy_price if buy_price else None,
                    'sell_price': sell_price if sell_price else None,
                    'source': 'phuquygroup.vn',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

        df = pd.DataFrame(data)
        print(f"✅ Đã lấy {len(df)} loại giá vàng từ phuquygroup.vn")
        return df

    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return pd.DataFrame()


# ==================== TEST ====================
if __name__ == "__main__":
    print("="*70)
    print("🥇 TEST SCRAPE PHÚ QUÝ GROUP")
    print("="*70)

    print("\n1️⃣  Chỉ lấy Vàng miếng SJC:")
    sjc_df = get_sjc_gold_price_from_phuquy()
    if not sjc_df.empty:
        print(sjc_df.to_string(index=False))
    else:
        print("❌ Không có dữ liệu")

    print("\n" + "="*70)
    print("\n2️⃣  Lấy TẤT CẢ các loại vàng:")
    all_df = get_all_gold_prices_from_phuquy()
    if not all_df.empty:
        print(all_df.to_string(index=False))
    else:
        print("❌ Không có dữ liệu")

    print("\n" + "="*70)
