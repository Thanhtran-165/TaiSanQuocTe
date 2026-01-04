# 🥇 Gold SJC Data Collector

Module quản lý dữ liệu giá vàng SJC với support cho cả SQLite và PostgreSQL.

## 📁 Cấu trúc thư mục

```
gold_scraper/
├── README.md
├── run.py                    # Entry point
├── src/
│   ├── __init__.py
│   └── gold_scraper.py       # Main module (581 dòng)
├── examples/                 (coming soon)
├── tests/                    (coming soon)
└── output/
    └── gold_data.db          # SQLite database
```

## 🚀 Cách sử dụng

### 1. Chạy chính
```bash
cd gold_scraper
python3 run.py
```

### 2. Trong code Python
```python
import sys
sys.path.insert(0, 'src')

from gold_scraper import GoldDataPG

# Khởi tạo database (SQLite)
db = GoldDataPG(db_type="sqlite", sqlite_path="output/gold_data.db")

# Hoặc PostgreSQL
db = GoldDataPG(
    db_type="postgresql",
    postgres_config={
        'host': 'localhost',
        'port': 5432,
        'database': 'gold_data',
        'user': 'postgres',
        'password': 'password'
    }
)
```

## 📊 Database Schema

### Table: sjc_prices
```sql
CREATE TABLE sjc_prices (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    name TEXT,
    buy_price REAL,
    sell_price REAL,
    date DATE,
    created_at DATETIME
)
```

## 🔧 Tính năng

✅ Hỗ trợ SQLite (development) và PostgreSQL (production)  
✅ Auto create tables  
✅ Insert/Update/Delete operations  
✅ Query với date range  
✅ Export to Excel/CSV  
✅ Transaction support  

## 📝 Methods chính

- `insert_sjc_price(name, buy_price, sell_price, date)`
- `get_latest_prices(limit=10)`
- `get_price_range(start_date, end_date)`
- `get_price_by_name(name)`
- `update_price(id, buy_price, sell_price)`
- `delete_price(id)`
- `export_to_excel(filename)`
- `get_statistics()`

Xem full documentation trong `src/gold_scraper.py`

## 📞 Support

Xem examples trong `examples/` (coming soon)

---

**Phiên bản:** 1.0.0  
**Based on:** gold_data_pg.py (581 lines)
