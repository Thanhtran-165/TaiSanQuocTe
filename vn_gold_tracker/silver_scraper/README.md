# 🥈 Silver Price Scraper

Script tự động lấy giá bạc hàng ngày từ các nguồn uy tín tại Việt Nam.

## 📁 Cấu trúc thư mục

```
silver_scraper/
├── README.md                 # Hướng dẫn sử dụng
├── requirements.txt          # Dependencies
├── run.py                    # Entry point - chạy script này
├── src/                      # Source code
│   ├── __init__.py
│   └── silver_scraper.py    # Main scraper class
├── examples/                 # Ví dụ sử dụng
│   └── example_usage.py
├── tests/                    # Test scripts
│   └── test_fallback.py
└── output/                   # Output files (JSON, CSV)
    ├── silver_prices.json
    └── silver_prices_*.csv
```

## 🚀 Cài đặt

```bash
# Di chuyển vào thư mục silver_scraper
cd silver_scraper

# Cài đặt dependencies
pip install -r requirements.txt
```

## 📖 Cách sử dụng

### 1. Chạy chính (Quick Start)
```bash
python3 run.py
```

**Kết quả:**
- In bảng giá ra console
- Lưu vào `output/silver_prices.json`

### 2. Chạy ví dụ
```bash
# Chạy tất cả examples
python3 examples/example_usage.py

# Hoặc chạy test
python3 tests/test_fallback.py
```

### 3. Trong code Python
```python
import sys
sys.path.insert(0, 'src')

from silver_scraper import SilverPriceScraper

scraper = SilverPriceScraper()
data = scraper.get_silver_prices()

if data['success']:
    print(f"Đã lấy được {len(data['prices'])} dòng giá")
```

## 📊 Nguồn dữ liệu

### ✅ Nguồn chính: giabac.phuquygroup.vn
- **Trạng thái:** Hoạt động tốt
- **Dữ liệu:** Bảng giá đầy đủ từ Phú Quý
- **Cập nhật:** Hàng ngày

**Dữ liệu bao gồm:**
- Bạc miếng Phú Quý 999 (1 lượng)
- Bạc thỏi Phú Quý 999 (10 lượng, 5 lượng)
- Đồng bạc mỹ nghệ Phú Quý 999
- Bạc thỏi Phú Quý 999 (1 kg)
- Bạc thương hiệu khác

### ⚠️ Fallback: topi.vn
- **Trạng thái:** Có Cloudflare Protection
- **Vấn đề:** Không thể scrape bằng requests thông thường
- **Đề xuất:** Chỉ dùng nguồn chính

## 📈 Output Format

### Console Output:
```
================================================================================
📊 BẢNG GIÁ BẠC - Nguồn: giabac.phuquygroup.vn
⏰ Cập nhật: 08:12 03/01/2026
================================================================================

【BẠC THƯƠNG HIỆU PHÚ QUÝ】
BẠC MIẾNG PHÚ QUÝ 999 1 LƯỢNG    Vnđ/Lượng   2,738,000   2,823,000
...
```

### JSON (`output/silver_prices.json`):
```json
{
  "success": true,
  "source": "https://giabac.phuquygroup.vn",
  "update_time": "08:12 03/01/2026",
  "scraped_at": "2026-01-03 11:01:15",
  "prices": [
    {
      "category": "BẠC THƯƠNG HIỆU PHÚ QUÝ",
      "product": "BẠC MIẾNG PHÚ QUÝ 999 1 LƯỢNG",
      "unit": "Vnđ/Lượng",
      "buy_price": "2,738,000",
      "sell_price": "2,823,000"
    }
  ]
}
```

## 🔧 Tính năng

✅ Lấy giá từ giabac.phuquygroup.vn (nguồn chính)
✅ Fallback sang topi.vn (có warning về Cloudflare)
✅ Export ra JSON, CSV
✅ Error handling chi tiết
✅ Tự động tạo output directory
✅ Production-ready examples

## 📌 Lưu ý

- Script tự động tạo thư mục `output/` nếu chưa có
- File output được lưu trong `output/` directory
- Nếu nguồn chính thất bại, sẽ tự động thử fallback
- topi.vn có Cloudflare Protection nên có thể không hoạt động

## 🔄 Lập lịch tự động

### Cron job (Linux/Mac):
```bash
# Mở crontab
crontab -e

# Chạy mỗi ngày lúc 9:00 sáng
0 9 * * * cd /path/to/silver_scraper && python3 run.py >> output/silver_price.log 2>&1
```

## 📞 Support

Xem thêm ví dụ trong `examples/example_usage.py`

---

**Phiên bản:** 1.0.0
**Ngày tạo:** 03/01/2026
