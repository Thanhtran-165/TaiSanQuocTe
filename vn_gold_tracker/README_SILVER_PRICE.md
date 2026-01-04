# 🥈 Silver Price Scraper - Giá Bạc Hôm Nay

Script tự động lấy giá bạc hàng ngày từ các nguồn uy tín tại Việt Nam.

## 📊 Nguồn dữ liệu

### ✅ Nguồn chính: giabac.phuquygroup.vn
- **Trạng thái:** Hoạt động tốt
- **Dữ liệu:** Bảng giá đầy đủ từ Phú Quý
- **Cập nhật:** Hàng ngày
- **Chống bot:** Không có

**Dữ liệu bao gồm:**
- Bạc miếng Phú Quý 999 (1 lượng)
- Bạc thỏi Phú Quý 999 (10 lượng, 5 lượng)
- Đồng bạc mỹ nghệ Phú Quý 999
- Bạc thỏi Phú Quý 999 (1 kg)
- Bạc thương hiệu khác (trên/dưới 1500 lượng)

---

### ⚠️ Fallback: topi.vn
- **Trạng thái:** CÓ Cloudflare Protection
- **Vấn đề:** Trang web sử dụng Cloudflare anti-bot protection
- **Hệ quả:** Không thể scrape bằng requests thông thường

**Giải pháp đề xuất:**
1. **Chỉ dùng nguồn chính** (giabac.phuquygroup.vn) - đã hoạt động ổn định
2. Nếu cần backup source, có thể tìm các trang khác như:
   - Sjc.com.vn
   - Vnexpress.net/thi-truong/gia-vang-bac-hom-nay
   - Các trang vàng bạc khác

---

## 🚀 Cài đặt

### Yêu cầu:
- Python 3.7+
- Các thư viện trong `requirements.txt`

### Cài đặt:
```bash
pip install -r requirements.txt
```

---

## 📖 Cách sử dụng

### 1. Chạy script chính:
```bash
python3 silver_price_scraper.py
```

**Kết quả:**
- In bảng giá ra màn hình console
- Lưu dữ liệu vào `silver_prices.json`
- Tự động dùng nguồn chính, nếu thất bại sẽ thông báo lỗi

### 2. Chạy test script:
```bash
python3 test_fallback.py
```

**Kết quả:**
- Test cả 2 nguồn (primary & fallback)
- So sánh kết quả
- Lưu vào `silver_prices_fallback.json`

---

## 📁 Output Format

### JSON Structure:
```json
{
  "success": true,
  "source": "https://giabac.phuquygroup.vn",
  "update_time": "08:12 03/01/2026",
  "scraped_at": "2026-01-03 10:59:45",
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

---

## 🎯 Kết quả thực tế

```
================================================================================
📊 BẢNG GIÁ BẠC - Nguồn: giabac.phuquygroup.vn
⏰ Cập nhật: 08:12 03/01/2026
================================================================================
Sản Phẩm                                 Đơn Vị          Giá Mua              Giá Bán
-----------------------------------------------------------------------------------------------

【BẠC THƯƠNG HIỆU PHÚ QUÝ】
BẠC MIẾNG PHÚ QUÝ 999 1 LƯỢNG            Vnđ/Lượng       2,738,000            2,823,000
BẠC THỎI PHÚ QUÝ 999 10 LƯỢNG, 5 LƯỢNG   Vnđ/Lượng       2,738,000            2,823,000
ĐỒNG BẠC MỸ NGHỆ PHÚ QUÝ 999             Vnđ/Lượng       2,738,000            3,221,000
BẠC THỎI PHÚ QUÝ 999 1KILO               Vnđ/Kg          73,013,151           75,279,812

【BẠC THƯƠNG HIỆU KHÁC】
Bạc 999 trên 1500 lượng (miếng-thanh-thỏi) Vnđ/Lượng       2,385,480            -
Bạc 999 dưới 1500 lượng  (miếng-thanh-thỏi) Vnđ/Lượng       2,316,000            -
================================================================================
```

---

## ⚙️ Cấu hình nâng cao

### Sử dụng trong code Python:

```python
from silver_price_scraper import SilverPriceScraper

# Khởi tạo scraper
scraper = SilverPriceScraper()

# Lấy giá
data = scraper.get_silver_prices()

# Kiểm tra kết quả
if data['success']:
    print(f"Đã lấy được {len(data['prices'])} dòng giá")
    for item in data['prices']:
        print(f"{item['product']}: Mua {item['buy_price']} - Bán {item['sell_price']}")
else:
    print(f"Lỗi: {data['error']}")
```

### Đổi nguồn chính:
```python
scraper = SilverPriceScraper()
scraper.primary_source = "https://trang-khac.vn"
```

---

## 🔄 Lập lịch tự động

### Dùng cron (Linux/Mac):
```bash
# Mở crontab
crontab -e

# Thêm dòng sau (chạy mỗi ngày lúc 9:00 sáng)
0 9 * * * cd /path/to/project && python3 silver_price_scraper.py >> silver_price.log 2>&1
```

### Dùng schedule trong Python:
```python
import schedule
import time
from silver_price_scraper import SilverPriceScraper

def job():
    scraper = SilverPriceScraper()
    data = scraper.get_silver_prices()
    scraper.save_to_json(data)

# Chạy mỗi ngày lúc 9:00
schedule.every().day.at("09:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 📌 Lưu ý quan trọng

### ⚠️ Về topi.vn (Fallback source):
Trang web này sử dụng **Cloudflare Protection** với JavaScript challenge, nên:
- **KHÔNG THỂ** scrape bằng requests thông thường
- Cần giải pháp bypass như Selenium, Playwright, hoặc sử dụng API trả phí
- **ĐỀ XUẤT:** Chỉ dùng nguồn chính (giabac.phuquygroup.vn) vì đã đầy đủ và ổn định

### 📝 Độ tin cậy:
- **giabac.phuquygroup.vn:** Rất cao - nguồn chính thức từ Phú Quý
- **topi.vn:** Không thể dùng - có anti-bot protection

---

## 🛠️ Xử lý lỗi

Script đã được thiết kế để:
1. ✅ Tự động retry nếu kết nối thất bại
2. ✅ Parse HTML một cách an toàn với try-except
3. ✅ Trả về error message rõ ràng nếu không lấy được dữ liệu
4. ✅ Lưu log ra console để debug

---

## 📞 Support

Nếu có vấn đề:
1. Kiểm tra kết nối internet
2. Kiểm tra xem trang web còn hoạt động không
3. Xem log error trong console
4. Mở issue trên GitHub (nếu có)

---

## 📜 License

MIT License - Tự do sử dụng cho mục đích cá nhân và thương mại.

---

**Ngày tạo:** 03/01/2026
**Phiên bản:** 1.0.0
**Tác giả:** Claude Code
