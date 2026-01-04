"""
DEMO: Scrape giá vàng từ topi.vn/gia-vang-hom-nay.html
⚠️  LƯU Ý: Trang này có Cloudflare protection
⚠️  Dữ liệu có thể được hardcode trong bài viết (không realtime)

Author: Claude Code
Date: 2026-01-03
"""

import re
import pandas as pd
from datetime import datetime


def parse_topi_markdown_content(content: str) -> pd.DataFrame:
    """
    Parse bảng giá vàng từ markdown content của topi.vn

    Args:
        content: Markdown content từ webReader

    Returns:
        pd.DataFrame: Giá vàng SJC
    """
    data = []

    # Pattern để match bảng giá SJC
    # Ví dụ: | Vàng SJC 1 Lượng | 117.600.000 | 119.600.000 |
    sjc_pattern = r'\|\s*Vàng (SJC\s+1\s+Lượng|miếng\s+SJC)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|'

    matches = re.finditer(sjc_pattern, content, re.IGNORECASE)

    for match in matches:
        gold_type = match.group(1).strip()
        buy_price = match.group(2).replace('.', '')
        sell_price = match.group(3).replace('.', '')

        data.append({
            'name': f'Vàng {gold_type}',
            'buy_price': buy_price,
            'sell_price': sell_price,
            'source': 'topi.vn',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    if data:
        df = pd.DataFrame(data)
        return df

    return pd.DataFrame()


def get_sjc_from_topi() -> pd.DataFrame:
    """
    Lấy giá vàng SJC từ topi.vn (GIẢ LẬP - dùng webReader content)

    ⚠️  LƯU Ý QUAN TRỌNG:
    - Trang này có Cloudflare protection
    - KHÔNG THỂ scrape bằng requests/BeautifulSoup thông thường
    - Cần dùng Selenium/Playwright HOẶC webReader API
    - Dữ liệu có thể CŨ (hardcode trong bài viết)

    Returns:
        pd.DataFrame: Giá vàng SJC
    """
    # Đây là GIẢ LẬP với content từ webReader
    # Trong thực tế, cần dùng webReader API hoặc browser automation

    sample_content = """
    #### __Công ty TNHH MTV Vàng bạc Đá quý Sài Gòn - SJC__

    |  |  |  |
    | --- | --- | --- |
    | __Loại vàng__ | __Giá mua (VNĐ/lượng)__ | __Giá bán (VNĐ/lượng)__ |
    | Vàng SJC 1 Lượng | 117.600.000 | 119.600.000 |
    | Vàng nhẫn SJC 99,99 | 113.700.000 | 116.200.000 |
    """

    return parse_topi_markdown_content(sample_content)


# ==================== ANALYSIS ====================

def compare_sources():
    """So sánh 2 nguồn fallback"""

    print("="*80)
    print("📊 SO SÁNH 2 NGUỒN FALLBACK")
    print("="*80)

    comparison = [
        {
            'Tiêu chí': 'Dữ liệu realtime',
            'phuquygroup.vn': '✅ Cập nhật real-time với timestamp',
            'topi.vn': '❌ Hardcode trong bài viết (có thể cũ)'
        },
        {
            'Tiêu chí': 'Dễ scrape',
            'phuquygroup.vn': '✅ HTML table đơn giản, không có protection',
            'topi.vn': '❌ Cloudflare protection, cần browser automation'
        },
        {
            'Tiêu chí': 'Độ tin cậy',
            'phuquygroup.vn': '✅ Nguồn chính thức từ Phú Quý Group',
            'topi.vn': '⚠️  Là bài blog tổng hợp, không phải API chính thức'
        },
        {
            'Tiêu chí': 'Tốc độ',
            'phuquygroup.vn': '✅ Nhanh (requests)',
            'topi.vn': '❌ Chậm (cần render JS hoặc browser automation)'
        },
        {
            'Tiêu chí': 'Bảo trì',
            'phuquygroup.vn': '✅ Dễ (HTML structure ổn định)',
            'topi.vn': '⚠️  Khó (Cloudflare có thể thay đổi)'
        },
        {
            'Tiêu chí': 'Số lượng thương hiệu',
            'phuquygroup.vn': '1 (chỉ Phú Quý)',
            'topi.vn': '7 (SJC, DOJI, PNJ, Mi Hồng, BTMC, Ngọc Thẩm, Phú Quý)'
        }
    ]

    df = pd.DataFrame(comparison)
    print(df.to_string(index=False))
    print("="*80)

    # Đề xuất
    print("\n💡 ĐỀ XUẤT:")
    print("   1️⃣  Ưu tiên: phuquygroup.vn (realtime, dễ scrape, tin cậy)")
    print("   2️⃣  Backup: topi.vn (chỉ khi cần nhiều thương hiệu)")
    print("   3️⃣  Cảnh báo: topi.vn KHÔNG PHÙ HỢP làm fallback chính")


if __name__ == "__main__":
    print("="*80)
    print("🥇 TEST FALLBACK TOPI.VN")
    print("="*80)

    print("\n⚠️  LƯU Ý:")
    print("   - topi.vn có Cloudflare protection")
    print("   - Dữ liệu có thể CŨ (hardcode trong bài viết)")
    print("   - KHÔNG KHUYẾN NGHỊ dùng làm fallback chính")

    print("\n1️⃣  Test parser (giả lập):")
    df = get_sjc_from_topi()
    if not df.empty:
        print(df.to_string(index=False))
    else:
        print("❌ Không parse được")

    print("\n2️⃣  So sánh 2 nguồn:")
    compare_sources()

    print("\n" + "="*80)
