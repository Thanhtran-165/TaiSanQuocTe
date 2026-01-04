# 📚 INDEX - WORLD BANK GOLD RESERVES DATASET

## 🗂️ DANH MỤC FILES

Generated: 2026-01-03 22:02

---

## 📊 DATA FILES (4 files)

### Main Dataset
1. **reserves_gold_by_country_year.csv** (587 KB)
   - 9,305 records × 7 columns
   - Dữ liệu chính: reserves và gold value theo năm
   - Format: CSV (comma-separated)
   - Dùng cho: Excel, Python, R, SQL import

2. **reserves_gold_by_country_year.parquet** (240 KB)
   - Same data as CSV, compressed format
   - Format: Apache Parquet
   - Dùng cho: Python pandas, Spark, big data tools

### Coverage Report
3. **coverage_report.csv** (7.4 KB)
   - 182 records × 8 columns
   - Thống kê coverage theo quốc gia
   - Format: CSV

4. **coverage_report.parquet** (8.4 KB)
   - Same as CSV, Parquet format

---

## 📄 DOCUMENTATION (5 files)

### Main Docs
5. **README_reserves_gold.md** (1.8 KB)
   - Project overview
   - Cách chạy pipeline
   - Output files description
   - Use cases

6. **TOM_TAT.md** (7.7 KB) ⭐ **BẮT ĐẦU TỪ ĐÂY** ⭐
   - Tóm tắt ngắn gọn (2 trang)
   - Quick stats, top holders
   - Vietnam data highlights
   - Quick start guide

7. **BAO_CAO_DU_AN.md** (13 KB)
   - Báo cáo chi tiết (600+ dòng)
   - Full analysis, methodology
   - Complete statistics
   - Academic interpretation

### Reference
8. **schema_reserves_gold.sql** (1.6 KB)
   - Database schema (MySQL)
   - Table definitions
   - Indexes và views
   - Stored procedures

9. **project_summary.json** (2.9 KB)
   - Machine-readable summary
   - Key metrics in JSON
   - Dùng cho automation/scripts

---

## 💻 SOURCE CODE (1 file)

10. **build_reserves_gold_dataset.py** (21 KB)
    - Main pipeline script
    - ~640 dòng code
    - Production-ready
    - Fully documented

---

## 🚀 QUICK NAVIGATION

### Tùy theo mục đích:

| Tôi muốn... | File nên đọc |
|-------------|--------------|
| Xem overview nhanh | **TOM_TAT.md** |
| Hiểu chi tiết project | **BAO_CAO_DU_AN.md** |
| Chạy lại pipeline | **README_reserves_gold.md** + `build_reserves_gold_dataset.py` |
| Import vào database | **schema_reserves_gold.sql** |
| Parse bằng script | **project_summary.json** |
| Xem data sample | **reserves_gold_by_country_year.csv** (mở bằng Excel) |
| Phân tích bằng Python | `import pandas as pd; df = pd.read_csv('reserves_gold_by_country_year.csv')` |

---

## 📋 FILE SIZE SUMMARY

```
Data Files:       843 KB (CSV) + 248 KB (Parquet)
Documentation:    26.5 KB (Markdown)
Source Code:      21 KB (Python)
Schema:           1.6 KB (SQL)
────────────────────────────────
Total:            ~1.1 MB
```

---

## 🎯 RECOMMENDED READING ORDER

### Cách 1: Quick (5 phút)
1. **TOM_TAT.md** - Overview
2. **project_summary.json** - Key metrics
3. **reserves_gold_by_country_year.csv** - Data

### Cách 2: Detailed (15 phút)
1. **README_reserves_gold.md** - Introduction
2. **TOM_TAT.md** - Summary
3. **BAO_CAO_DU_AN.md** - Full report
4. **schema_reserves_gold.sql** - If using database

### Cách 3: Technical (30 phút)
1. **build_reserves_gold_dataset.py** - Code review
2. **README_reserves_gold.md** - Usage
3. **schema_reserves_gold.sql** - DB design
4. **BAO_CAO_DU_AN.md** - Analysis methodology

---

## 💡 TIPs

### Opening Files:
- **CSV:** Excel, Google Sheets, Numbers
- **Parquet:** Python pandas, PySpark, DuckDB
- **Markdown:** Any text editor, GitHub preview, VS Code
- **Python:** Any IDE (VS Code, PyCharm, Jupyter)
- **SQL:** MySQL Workbench, DBeaver, command line

### Working with Data:
```python
# Python
import pandas as pd
df = pd.read_csv('reserves_gold_by_country_year.csv')

# R
df <- read.csv('reserves_gold_by_country_year.csv')

# Excel/Sheets
# File → Open → Select CSV
```

### Database Import:
```bash
# MySQL
mysql -u username -p database_name < schema_reserves_gold.sql
mysqlimport --local database_name reserves_gold_by_country_year.csv
```

---

## 📞 WHAT'S INSIDE EACH FILE

### Data Files Contents:
**reserves_gold_by_country_year.csv/parquet:**
- 9,305 rows (country-year observations)
- 7 columns: iso2, country_name, year, total_reserves_usd, non_gold_reserves_usd, gold_value_usd_inferred, quality_flag
- 182 economies
- 1960-2024

**coverage_report.csv/parquet:**
- 182 rows (one per economy)
- 8 columns: iso2, country_name, has_total, has_non_gold, has_both, first_year, last_year, n_years

### Documentation Contents:
**README:** Setup, usage, output files, methodology
**TOM_TAT:** Quick summary, top holders, Vietnam data, stats
**BAO_CAO:** Full analysis, detailed stats, breakdown by region
**schema:** SQL CREATE TABLE statements, indexes, views, stored procedures

### Code Contents:
**build_reserves_gold_dataset.py:**
- fetch_countries() - Get economies
- fetch_indicator_data() - Download indicators
- calculate_gold_inference() - Compute gold value
- generate_coverage_report() - Statistics
- export_data() - Save CSV/Parquet
- main() - Pipeline orchestrator

---

## 🔍 SEARCH KEYWORDS

Nếu bạn đang tìm:

| Tôi cần... | File |
|------------|------|
| Dữ liệu Việt Nam | TOM_TAT.md (section 5), reserves_gold_by_country_year.csv (filter iso2='VN') |
| Top 10 gold holders | TOM_TAT.md (section 4), BAO_CAO_DU_AN.md (section 4.1) |
| Cách chạy pipeline | README_reserves_gold.md (section "How to Run") |
| SQL schema | schema_reserves_gold.sql |
| Thống kê chi tiết | BAO_CAO_DU_AN.md (section 4) |
| Code documentation | build_reserves_gold_dataset.py (docstrings) |
| Methodology | BAO_CAO_DU_AN.md (section 6) |

---

## ✅ COMPLETENESS CHECK

**Data:**
- ✅ Main dataset (CSV + Parquet)
- ✅ Coverage report (CSV + Parquet)
- ✅ All 182 economies
- ✅ 1960-2024 time span

**Documentation:**
- ✅ README (project overview)
- ✅ Summary (TOM_TAT)
- ✅ Detailed report (BAO_CAO)
- ✅ Database schema
- ✅ Machine-readable JSON

**Code:**
- ✅ Source code
- ✅ Fully commented
- ✅ Production-ready

**Total: 10 files**
**Status: COMPLETE ✅**

---

**Last Updated:** 2026-01-03 22:02
**Project Status:** ✅ Production Ready
**Next Update:** After World Bank Q1 2026 data release

---

*End of Index*
