# 🏆 Tài Sản Quốc Tế - Gold & Silver Price Collectors

Dự án thu thập dữ liệu giá vàng và bạc hàng ngày từ các nguồn uy tín tại Việt Nam.

## 📁 Cấu trúc dự án

```
TaiSanQuocTe/
│
├── 📋 README_PROJECT.md      # File này - Overview toàn bộ dự án
├── 📋 README.md               # README cũ
│
├── 🥇 gold_scraper/           # GOLD SJC Data Collector
│   ├── README.md              # Hướng dẫn chi tiết
│   ├── run.py                 # Chạy: python3 run.py
│   ├── requirements.txt
│   ├── src/
│   │   ├── gold_scraper.py   # Main module (581 dòng)
│   │   └── __init__.py
│   ├── examples/
│   ├── tests/
│   └── output/
│       └── gold_data.db      # SQLite database
│
├── 🥈 silver_scraper/         # SILVER Price Scraper
│   ├── README.md              # Hướng dẫn chi tiết  
│   ├── run.py                 # Chạy: python3 run.py
│   ├── requirements.txt
│   ├── src/
│   │   ├── silver_scraper.py # Main module (222 dòng)
│   │   └── __init__.py
│   ├── examples/
│   ├── tests/
│   └── output/
│       └── silver_prices.json
│
└── 📁 [Các file cũ]           # Các file cũ chưa được organize
    ├── auto_collect_db.py
    ├── gold_data_pg.py        # Đã copy vào gold_scraper/src/
    ├── example_usage.py
    ├── test_fallback.py
    └── ...
```

## 🚀 Quick Start

### 1. Gold SJC Collector
```bash
cd gold_scraper
python3 run.py
```

**Chức năng:**
- Quản lý database giá vàng SJC
- Hỗ trợ SQLite & PostgreSQL
- Insert/Query/Export data

### 2. Silver Price Scraper
```bash
cd silver_scraper
python3 run.py
```

**Chức năng:**
- Scrape giá bạc từ giabac.phuquygroup.vn
- Fallback sang topi.vn (có Cloudflare warning)
- Export JSON, CSV

## 📊 Output

### Gold SJC:
- **Database:** `gold_scraper/output/gold_data.db`
- **Tables:** `sjc_prices`
- **Support:** SQLite, PostgreSQL

### Silver:
- **JSON:** `silver_scraper/output/silver_prices.json`
- **CSV:** `silver_scraper/output/silver_prices_YYYYMMDD.csv`
- **Source:** giabac.phuquygroup.vn (primary)

## 🔧 Cài đặt dependencies

```bash
# Gold scraper
cd gold_scraper && pip install -r requirements.txt

# Silver scraper  
cd silver_scraper && pip install -r requirements.txt
```

## 📖 Documentation chi tiết

Xem README trong từng thư mục:
- **Gold:** `gold_scraper/README.md`
- **Silver:** `silver_scraper/README.md`

## 🎯 Tính năng chính

### Gold SJC:
✅ SQLite & PostgreSQL support  
✅ Auto create tables  
✅ CRUD operations  
✅ Date range queries  
✅ Export to Excel/CSV  

### Silver:
✅ Web scraping giá bạc  
✅ Primary + Fallback sources  
✅ JSON & CSV export  
✅ Error handling  
✅ Auto output directory  

## 📝 Todo

- [ ] Di chuyển các file cũ vào đúng thư mục
- [ ] Tạo examples cho gold_scraper
- [ ] Tạo test cases
- [ ] Cleanup các file rời rạc

## 🤝 Contributing

Xem cấu trúc từng module trong thư mục tương ứng.

---

**Phiên bản:** 1.0.0  
**Last Updated:** 03/01/2026  
**Status:** ✅ Cả 2 scraper đều hoạt động tốt
