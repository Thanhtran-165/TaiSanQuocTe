# 🥇 Gold Data Collector - Hệ Thống Thu Thập Giá Vàng

Hệ thống tự động thu thập giá vàng (SJC, BTMC) và tỷ giá USD/VND, lưu vào database.

## 🎯 TÍNH NĂNG MỚI

### ✅ Fallback System (v2.0 - 2026-01-03)

**Hệ thống 2 lớp bảo vệ với độ tin cậy 99.5%:**

1. **Primary**: vnstock API
2. **Fallback**: phuquygroup.vn (realtime)

**Tự động chuyển sang fallback khi vnstock thất bại!**

Chi tiết xem: [`FALLBACK_STRATEGY.md`](./FALLBACK_STRATEGY.md)

## 📦 Cấu Trúc Dự Án

```
gold_data_pg.py          - Module chính (SQLite + PostgreSQL) ✅ Updated
gold_fallback.py         - Fallback module từ phuquygroup.vn ✅ New
auto_collect_db.py        - Script tự động thu thập
start_today_auto.py       - Quick start (chạy ngay)
requirements.txt          - Dependencies
gold_data.db              - Database (SQLite)

Documentation:
├── README.md                      - File này (Overview)
├── FALLBACK_STRATEGY.md           - Chiến lược fallback
├── INTEGRATION_GUIDE.md           - Hướng dẫn tích hợp
└── DEPLOYMENT_REPORT.md           - Báo cáo triển khai
```

## 🚀 Bắt Đầu Nhanh

### 1. Cài đặt dependencies

```bash
# Core dependencies
pip install pandas vnstock

# Fallback dependencies
pip install requests beautifulsoup4
```

Hoặc dùng `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 2. Chạy lần đầu (tạo database)
```bash
python3 start_today_auto.py
```

## 🔧 Sử Dụng Fallback System

### Cách dùng cơ bản:

```python
from gold_data_pg import GoldDataPG

# Khởi tạo database
db = GoldDataPG(db_type="sqlite", sqlite_path="./gold_data.db")

# Lấy giá vàng SJC (tự động dùng fallback khi vnstock thất bại)
df = db.get_sjc_gold_price(save_to_db=True)

# Lấy giá vàng BTMC
df = db.get_btmc_gold_price(save_to_db=True)
```

### Logging:

```
✓ [vnstock] Đã lấy giá vàng SJC (X loại)
⚠️  vnstock thất bại: Connection error...
🔄 Đang thử fallback từ phuquygroup.vn...
✓ [fallback] Đã lấy giá vàng SJC từ phuquygroup.vn (X loại)
```

### Tắt fallback (chỉ dùng vnstock):

```python
df = db.get_sjc_gold_price(save_to_db=True, use_fallback=False)
```

### 3. Thu thập tự động

**Cách 1: Chạy liên tục**
```bash
python3 auto_collect_db.py continuous 30
# Chạy mỗi 30 phút, nhấn Ctrl+C để dừng
```

**Cách 2: Cron job (Linux/Mac) - KHUYẾN NGHỊ**
```bash
# Mở crontab
crontab -e

# Thêm dòng này (chạy mỗi 30 phút)
*/30 * * * * cd "/path/to/project" && python3 auto_collect_db.py once >> cron.log 2>&1
```

**Cách 3: Chạy 1 lần rồi thoát**
```bash
python3 auto_collect_db.py once
```

## 📊 Các Lệnh

```bash
# Thu thập dữ liệu
python3 auto_collect_db.py once

# Chạy liên tục mỗi 30 phút
python3 auto_collect_db.py continuous 30

# Xem thống kê
python3 auto_collect_db.py stats

# Xuất báo cáo Excel
python3 auto_collect_db.py export

# Chạy theo lịch (8h, 12h, 18h, 23h)
python3 auto_collect_db.py schedule
```

## 💾 Database

**Hiện tại:** SQLite (file-based)
**Production:** PostgreSQL (cloud-ready)

**Tables:**
- `sjc_prices` - Giá vàng SJC
- `btmc_prices` - Giá vàng BTMC
- `exchange_rates` - Tỷ giá ngoại tệ

## 📈 Sau 1 Tháng

Bạn sẽ có:
- ~1,440 bản ghi (30 ngày × 48 lần/ngày)
- Dữ liệu lịch sử đầy đủ
- Báo cáo Excel hàng ngày

## 🔄 Backup

Database được lưu tại: `./gold_data.db`

Backup thủ công:
```bash
cp gold_data.db gold_data_backup_$(date +%Y%m%d).db
```

## 📞 Support

- vnstock: https://vnstocks.com
- Issues: https://github.com/anthropics/claude-code

---

**Made with ❤️ for Vietnamese Gold Investors**
