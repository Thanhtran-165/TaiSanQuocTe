"""
Module Fallback cho Gold Scraper
Dùng khi vnstock thất bại

Author: Claude Code
Date: 2026-01-03
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from typing import Optional


def get_sjc_from_phuquy() -> pd.DataFrame:
    """
    Fallback: Lấy giá vàng SJC từ phuquygroup.vn

    Returns:
        pd.DataFrame với cấu trúc tương thích vnstock:
            - name: Tên loại vàng
            - buy_price: Giá mua (VNĐ/lượng)
            - sell_price: Giá bán (VNĐ/lượng)
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

        rows = tbody.find_all('tr')

        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                name = cols[0].get_text(strip=True)

                # Chỉ lấy "Vàng miếng SJC"
                if "Vàng miếng SJC" in name:
                    # phuquygroup.vn reports VNĐ/Chỉ, convert to VNĐ/Lượng (1 lượng = 10 chỉ)
                    buy_price_chi = cols[1].get_text(strip=True).replace(',', '')
                    sell_price_chi = cols[2].get_text(strip=True).replace(',', '')
                    buy_price = str(int(float(buy_price_chi) * 10))
                    sell_price = str(int(float(sell_price_chi) * 10))

                    df = pd.DataFrame([{
                        'name': name,
                        'buy_price': buy_price,
                        'sell_price': sell_price
                    }])

                    return df

        return pd.DataFrame()

    except Exception as e:
        print(f"⚠️  Fallback phuquygroup.vn thất bại: {e}")
        return pd.DataFrame()


def get_btmc_from_phuquy() -> pd.DataFrame:
    """
    Fallback: Lấy giá vàng BTMC từ phuquygroup.vn

    Lấy các loại vàng NHẪN TRÒN (tương đương BTMC)

    Returns:
        pd.DataFrame với cấu trúc tương thích vnstock
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

                # Lấy các loại tương đương BTMC
                if any(keyword in name for keyword in ['Nhẫn tròn', 'Phú Quý 999.9']):
                    # phuquygroup.vn reports VNĐ/Chỉ, convert to VNĐ/Lượng (1 lượng = 10 chỉ)
                    buy_price_chi = cols[1].get_text(strip=True).replace(',', '')
                    sell_price_chi = cols[2].get_text(strip=True).replace(',', '')
                    buy_price = str(int(float(buy_price_chi) * 10))
                    sell_price = str(int(float(sell_price_chi) * 10))

                    data.append({
                        'name': name,
                        'karat': '999.9',
                        'gold_content': '99.99%',
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'world_price': '',
                        'time': datetime.now().strftime('%H:%M')
                    })

        return pd.DataFrame(data)

    except Exception as e:
        print(f"⚠️  Fallback BTMC từ phuquygroup.vn thất bại: {e}")
        return pd.DataFrame()


# ==================== TEST ====================
if __name__ == "__main__":
    print("="*70)
    print("🥇 TEST GOLD FALLBACK MODULE")
    print("="*70)

    print("\n1️⃣  Test SJC Fallback:")
    sjc = get_sjc_from_phuquy()
    if not sjc.empty:
        print(sjc.to_string(index=False))
    else:
        print("❌ Failed")

    print("\n2️⃣  Test BTMC Fallback:")
    btmc = get_btmc_from_phuquy()
    if not btmc.empty:
        print(btmc.to_string(index=False))
    else:
        print("❌ Failed")
