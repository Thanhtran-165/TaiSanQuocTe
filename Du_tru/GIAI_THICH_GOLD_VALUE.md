# 💡 GIẢI THÍCH: GOLD_RESERVES_VALUE_USD_INFERRED

## ❓ ĐÂY LÀ GÌ?

`gold_reserves_value_usd_inferred` là **giá trị dự trữ vàng tính bằng USD**, được suy ra từ sự chênh lệch giữa tổng dự trữ và dự trữ không vàng.

---

## 🧮 CÔNG THỨC TÍNH TOÁN

```
gold_reserves_value_usd_inferred = total_reserves_usd - non_gold_reserves_usd
```

**Trong đó:**
- `total_reserves_usd` - Tổng dự trữ (bao gồm vàng)
  - Indicator: `FI.RES.TOTL.CD`
  - Includes: gold, foreign exchange, SDR, reserve position in IMF

- `non_gold_reserves_usd` - Tổng dự trữ (trừ vàng)
  - Indicator: `FI.RES.XGLD.CD`
  - Includes: foreign exchange, SDR, reserve position in IMF

**Kết quả:** Giá trị vàng theo USD

---

## ⚠️ RẤT QUAN TRỌNG: ĐÂY KHÔNG PHẢI TONNES!

### 1. **Đơn vị là USD, KHÔNG PHẢI khối lượng**
- ✅ **Là:** Giá trị tiền tệ ($ USD)
- ❌ **KHÔNG phải:** Khối lượng vàng (kg/tonnes/oz)

### 2. **Là inferred value, KHÔNG PHẢI direct**
- ✅ **Là:** Giá trị suy ra bằng phép trừ
- ❌ **KHÔNG phải:** Số liệu trực tiếp từ World Bank
- ⚠️ **Có thể:** Có sai số do data revisions

### 3. **Annual frequency**
- Tần suất: Hàng năm
- Mỗi quan sát = 1 quốc gia trong 1 năm
- Time span: 1960-2024

### 4. **Current US$, không adjusted**
- ✅ Current US$ (giá trị tại thời điểm đó)
- ❌ Không inflation-adjusted
- ❌ Không real (constant) US$

---

## 📊 VÍ DỤ CỤ THỂ

### Example 1: United States (2024)

```csv
iso2: US
country_name: United States
year: 2024
total_reserves_usd: 682,276,848,452.78
non_gold_reserves_usd: 682,276,848,452.78
gold_reserves_value_usd_inferred: 0.0
quality_flag: GOLD_ZERO_OR_NOT_REPORTED
```

**Giải thích:**
- Total reserves: $682.3 billion
- Non-gold reserves: $682.3 billion
- Gold inferred: $0.0
- Flag: `GOLD_ZERO_OR_NOT_REPORTED` - Có thể World Bank không tách riêng gold cho US

### Example 2: Afghanistan (2020)

```csv
iso2: AF
country_name: Afghanistan
year: 2020
total_reserves_usd: 9,748,946,326.72
non_gold_reserves_usd: 8,419,488,003.82
gold_reserves_value_usd_inferred: 1,329,458,322.90
quality_flag: OK
```

**Giải thích:**
- Total reserves: $9.75 billion
- Non-gold reserves: $8.42 billion
- **Gold inferred: $1.33 billion** ✅
- Flag: `OK` - Giá trị hợp lý

### Example 3: Vietnam (2020-2024)

```csv
iso2: VN
year: 2024
total_reserves_usd: 83,081,854,928.12
non_gold_reserves_usd: 83,081,854,928.12
gold_reserves_value_usd_inferred: 0.0
quality_flag: GOLD_ZERO_OR_NOT_REPORTED

year: 2023
total_reserves_usd: 92,237,540,812.25
non_gold_reserves_usd: 92,237,540,812.25
gold_reserves_value_usd_inferred: 0.0
quality_flag: GOLD_ZERO_OR_NOT_REPORTED
```

**Giải thích:**
- Vietnam có 0 gold trong World Bank data
- Tất cả reserves đều là foreign exchange/SDR
- Flag: `GOLD_ZERO_OR_NOT_REPORTED` - Không có gold hoặc không báo cáo

---

## 🔬 TẠI SAO DÙNG "INFERRED"?

### 1. **World Bank không báo cáo trực tiếp gold value**
- World Bank chỉ cung cấp:
  - Total reserves (including gold)
  - Total reserves minus gold
- Không có indicator "Gold reserves value"

### 2. **Phải tính toán**
```
Gold = Total - Non_Gold
```
- Đây là phép tính suy ra
- Không phải measurement trực tiếp

### 3. **Hạn chế**
- ⚠️ Có thể có inconsistencies
- ⚠️ Data revisions có thể tạo ra giá trị âm
- ⚠️ Definitional changes between years

---

## 📈 PHÂN BỔ QUALITY FLAGS

| Flag | Ý nghĩa | Tỷ lệ trong dataset |
|------|---------|---------------------|
| `OK` | Gold value dương, hợp lệ | 69.1% (6,429 records) |
| `GOLD_ZERO_OR_NOT_REPORTED` | Gold = 0 (không có hoặc không báo) | 30.9% (2,876 records) |
| `NEGATIVE_GOLD_INFERRED` | Gold âm (lỗi/sai số) | 0% (0 records) |

---

## 🎓 Ý NGHĨA HỌC THUẬT

### 1. **Đây là measure của gold importance**
- High gold value → Gold đóng vai trò lớn trong reserve portfolio
- Zero gold value → Economy phụ thuộc vào foreign exchange/SDR

### 2. **Longitudinal analysis**
- Có thể track changes trong gold holdings over 65 years
- Understand policy shifts in reserve management

### 3. **Cross-country comparison**
- Compare strategies across economies
- Identify "gold-loving" vs "forex-focused" countries

### 4. **Limitations to acknowledge**
- Không phản ánh physical gold tonnes
- Giá trị biến động theo gold price
- Inferred value, not directly reported

---

## 🔄 SO SÁNH VỚI GOLD TONNES

| Aspect | gold_reserves_value_usd_inferred | Gold Tonnes (World Gold Council) |
|--------|----------------------------------|----------------------------------|
| **Đơn vị** | US dollars | Metric tonnes |
| **Nguồn** | World Bank (inferred) | World Gold Council (direct) |
| **Frequency** | Annual | Monthly/Quarterly |
| **Coverage** | 182 economies | ~100 countries |
| **Tính chất** | Financial value | Physical quantity |
| **Ưu điểm** | Long time series, global coverage | Precise physical measure |

**Recommendation:** Nên dùng cả 2 sources nếu cần comprehensive analysis!

---

## 💡 USE CASES

### ✅ Good for:
- Longitudinal analysis (1960-2024)
- Global comparison (182 economies)
- Reserve composition studies
- Financial stability research
- Policy evaluation

### ❌ Not suitable for:
- Physical gold flow analysis
- Gold market trading
- Precise weight measurements
- Real-time monitoring

---

## 📝 CÁCH TRÍCH DẪN TRONG BÀI RESEARCH

```
"We use World Bank World Development Indicators (WDI) data to construct
an inferred measure of gold reserve value. Following standard practice,
gold reserves value (in USD) is calculated as the difference between
total reserves (including gold, indicator FI.RES.TOTL.CD) and total
reserves excluding gold (FI.RES.XGLD.CD). This provides an annual
panel of gold's financial role in reserve portfolios across 182 economies
from 1960 to 2024."

Source: World Bank WDI API, accessed 2026-01-03
```

---

## 🔗 NGUỒN DỮ LIỆU

**Primary:**
- World Bank World Development Indicators (WDI)
- API: https://api.worldbank.org/v2/
- Last updated: 2025-12-19

**Indicators:**
- `FI.RES.TOTL.CD` - Total reserves (includes gold), current US$
- `FI.RES.XGLD.CD` - Total reserves minus gold, current US$

**Complementary Sources:**
- World Gold Council - Gold tonnes data
- IMF COFER - Currency composition of reserves
- BIS - International banking statistics

---

## ✅ TÓM TẮT TRONG 3 DÒNG

1. **`gold_reserves_value_usd_inferred` là giá trị USD của vàng, được tính bằng phép trừ: Total reserves - Non-gold reserves**

2. **Đây là inferred annual USD value, KHÔNG PHẢI khối lượng vàng (tonnes) và KHÔNG PHẢI số liệu trực tiếp**

3. **Dữ liệu phù hợp cho longitudinal analysis và cross-country comparison, nhưng cần lưu ý limitations khi interpret results**

---

**Generated:** 2026-01-03
**Status:** ✅ Final
