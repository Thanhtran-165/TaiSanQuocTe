# Cấu trúc thư mục Word Asset - Giải thích chi tiết

## 📁 Cấu trúc hiện tại (sau khi dọn dẹp)

```
Word Asset/
├── README.md                          # Hướng dẫn tổng quan
├── .gitignore                         # Git ignore file
├── .DS_Store                          # macOS system file (auto-generated)
│
├── precious_metals_tracker/           # ⭐ PROJECT CHÍNH (Active)
│   ├── precious_metals/               #    Main package
│   │   ├── __init__.py               #    Package exports
│   │   └── core.py                   #    Core functionality
│   ├── examples/                      #    Example scripts
│   │   └── basic_usage.py            #    Basic usage examples
│   ├── tests/                         #    Test suite
│   │   ├── __init__.py               #    Test package
│   │   └── test_basic.py             #    Basic tests
│   ├── setup.py                       #    Package setup
│   ├── requirements.txt               #    Dependencies
│   ├── README.md                      #    Full documentation
│   ├── CHANGELOG.md                   #    Version history
│   ├── SUMMARY.md                     #    Quick summary
│   ├── config.example.py              #    Config template
│   └── .gitignore                     #    Package gitignore
│
├── precious_metals_backup/            # 📦 BACKUP (Archived)
│   ├── precious_metals.py             #    Old single-file version
│   ├── example_usage.py               #    Old examples
│   ├── config.example.py              #    Old config
│   ├── requirements.txt               #    Old requirements
│   ├── README.md                      #    Old README
│   └── CHANGELOG.md                   #    Old changelog
│
├── TaiSanQuocTe/                      # 💰 PROJECT KHÁC
│   └── (files...)
│
└── silver_scraper/                    # 🥈 PROJECT KHÁC
    └── (files...)
```

---

## 🎯 Project nào đang dùng?

### ✅ **Active**: `precious_metals_tracker/`

Đây là **package chính** bạn nên dùng:
- Version: 2.0.0
- Structure: Package chuẩn Python
- Features: Yahoo Finance + MSN Money fallback
- Tests: Có pytest test suite
- Documentation: Đầy đủ

### 📦 **Archived**: `precious_metals_backup/`

Phiên bản cũ (v1.x) - chỉ để backup:
- Single file structure
- Không có tests
- Không dùng nữa (đã thay thế)

---

## 🚀 Cách sử dụng project chính

### 1. Cài đặt
```bash
cd precious_metals_tracker
pip install -e .
```

### 2. Sử dụng trong code
```python
# Từ bất kỳ đâu (vì đã cài package)
from precious_metals import get_gold_price

gold = get_gold_price()
print(f"Giá vàng: ${gold['price']}/oz")
```

### 3. Chạy examples
```bash
cd precious_metals_tracker/examples
python basic_usage.py
```

### 4. Chạy tests
```bash
cd precious_metals_tracker
pytest
```

---

## ❓ Tại sao có 2 bản?

### Lịch sử:
1. **Ban đầu**: Single file (`precious_metals.py`) - Version 1.x
2. **Yêu cầu**: Bỏ Yahoo ETF + đóng gói thành package
3. **Kết quả**: Package structure (`precious_metals_tracker/`) - Version 2.0

### Đã làm gì:
- ✅ Bỏ Yahoo ETF fallback (3 nguồn → 2 nguồn)
- ✅ Đóng gói thành package chuẩn
- ✅ Thêm test suite
- ✅ Cập nhật documentation
- ✅ Di chuyển file cũ vào `backup/`

---

## 🧹 Có thể xóa gì?

### Có thể xóa an toàn:
```bash
# Nếu chắc chắn không cần backup
rm -rf precious_metals_backup/

# Xóa .DS_Store (macOS tự tạo lại)
find . -name ".DS_Store" -delete
```

### KHÔNG NÊN xóa:
- ❌ `precious_metals_tracker/` - Project chính
- ❌ `TaiSanQuocTe/` - Project khác
- ❌ `silver_scraper/` - Project khác

---

## 📊 Summary table

| Thư mục | Purpose | Status | Có thể xóa? |
|---------|---------|--------|-------------|
| `precious_metals_tracker/` | Package chính | ✅ Active | ❌ KHÔNG |
| `precious_metals_backup/` | Backup v1.x | 📦 Archived | ✅ CÓ THỂ |
| `TaiSanQuocTe/` | Project khác | ✅ Active | ❌ KHÔNG |
| `silver_scraper/` | Project khác | ✅ Active | ❌ KHÔNG |

---

## 🎓 Best Practices

### Moving forward:
1. **Chỉ dùng** `precious_metals_tracker/` cho các dự án mới
2. **Import** như một package bình thường:
   ```python
   from precious_metals import get_gold_price
   ```
3. **Update** package khi cần:
   ```bash
   cd precious_metals_tracker
   git pull  # hoặc manual update
   pip install -e . --force-reinstall
   ```
4. **Run tests** thường xuyên để đảm bảo hoạt động

---

## 📞 Need help?

**Documentation chính:** Xem `precious_metals_tracker/README.md`

**Examples:** Xem `precious_metals_tracker/examples/basic_usage.py`

**Tests:** Chạy `pytest` trong `precious_metals_tracker/`

---

**Created**: 2026-01-03
**Last updated**: 2026-01-03
**Version**: 2.0.0
