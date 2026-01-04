# 🎯 CHIẾN LƯỢC FALLBACK CHO GOLD SCRAPER

## 📋 TÓM TẮT NGHIÊN CỨU

Đã nghiên cứu **3 nguồn** để làm fallback cho hệ thống lấy giá vàng:

| Nguồn | Kết quả | Khả dụng |
|-------|---------|----------|
| **phuquygroup.vn** | ✅ Test thành công | ✅ PHÙ HỢP NHẤT |
| **topi.vn/gia-vang-hom-nay.html** | ⚠️ Có Cloudflare | ⚠️ KHÔNG KHUYẾN NGHỊ |
| **topi.vn/gia-bac-hom-nay.html** | ❌ Chỉ có giá bạc | ❌ KHÔNG PHÙ HỢP |

---

## 🥇 NGUỒN 1: PHUQUYGROUP.VN (KHUYẾN NGHỊ)

### ✅ Ưu điểm

1. **Dữ liệu realtime**: Cập nhật theo thời gian thực với timestamp cụ thể
   ```
   Giá vàng cập nhật lần cuối lúc 08:15 03/01/2026
   ```

2. **Dễ scrape**: HTML structure đơn giản, không có protection
   ```html
   <table class="m-auto text-center">
     <tr>
       <td>Vàng miếng SJC</td>
       <td>15,080,000</td>
       <td>15,280,000</td>
     </tr>
   </table>
   ```

3. **Độ tin cậy cao**: Nguồn chính thức từ Tập đoàn Phú Quý

4. **Nhanh & nhẹ**: Dùng requests, không cần browser automation

5. **Dễ bảo trì**: HTML structure ổn định

### ❌ Nhược điểm

- Chỉ có 1 thương hiệu (Phú Quý)
- Không có giá các thương hiệu khác (DOJI, PNJ, etc.)

### 📊 Dữ liệu thực tế

```
Vàng miếng SJC: 15,080,000 - 15,280,000 VNĐ/chỉ
```

### 🔧 Implementation

**File**: `gold_fallback.py` (ĐÃ TẠO)

```python
def get_sjc_from_phuquy() -> pd.DataFrame:
    """Lấy giá vàng SJC từ phuquygroup.vn"""
    url = "https://phuquygroup.vn"
    # ... (code đầy đủ trong file gold_fallback.py)
```

---

## ⚠️ NGUỒN 2: TOPI.VN (KHÔNG KHUYẾN NGHỊ)

### ✅ Ưu điểm

1. **Đa dạng thương hiệu**: 7 thương hiệu (SJC, DOJI, PNJ, Mi Hồng, BTMC, Ngọc Thẩm, Phú Quý)
2. **Nhiều loại vàng**: Vàng miếng, nhẫn, nữ trang, etc.

### ❌ Nhược điểm (NẶNG NỀ)

1. **Cloudflare Protection**: Không thể scrape bằng requests thường
   ```html
   <title>Just a moment...</title>
   ```

2. **Dữ liệu KHÔNG realtime**: Hardcode trong bài viết
   ```
   Tính đến ngày 19/6/2025  ← NGÀY CŨ!
   ```

3. **Cần browser automation**: Phải dùng Selenium/Playwright (chậm, nặng)

4. **Khó bảo trì**: Cloudflare có thể thay đổi bất cứ lúc nào

5. **Không phải API chính thức**: Là bài blog tổng hợp

### 🔥 TẠI SAO KHÔNG NÊN DÙNG?

```
topi.vn/gia-vang-hom-nay.html
   ↓
Cloudflare Challenge
   ↓
Cần Selenium/Playwright (chậm 3-5s)
   ↓
Parse markdown content
   ↓
Dữ liệu CŨ (hardcode ngày 19/6/2025)
   ↓
❌ KHÔNG PHÙ HỢP LÀM FALLBACK REALTIME
```

---

## 🎯 CHIẾN LƯỢC FALLBACK ĐỀ XUẤT

### ⭐ OPTION 1: CHỈ DÙNG PHUQUYGROUP (KHUYẾN NGHỊ)

```python
def get_sjc_gold_price(use_fallback=True):
    # 1. Thử vnstock trước
    try:
        df = vnstock.sjc_gold_price()
        if not df.empty:
            return df
    except:
        pass

    # 2. Fallback: phuquygroup.vn
    if use_fallback:
        df = get_sjc_from_phuquy()
        if not df.empty:
            return df

    # 3. Thất bại
    return pd.DataFrame()
```

**Ưu điểm**:
- ✅ Realtime data
- ✅ Nhanh (< 1s)
- ✅ Đơn giản, dễ bảo trì
- ✅ Độ tin cậy cao

**Nhược điểm**:
- ❌ Chỉ có 1 nguồn fallback

---

### ⚠️ OPTION 2: DÙNG CẢ 2 NGUỒN (KHÔNG KHUYẾN NGHỊ)

```python
def get_sjc_gold_price(use_fallback=True):
    # 1. vnstock
    try:
        df = vnstock.sjc_gold_price()
        if not df.empty:
            return df
    except:
        pass

    # 2. Fallback 1: phuquygroup.vn
    if use_fallback:
        df = get_sjc_from_phuquy()
        if not df.empty:
            return df

    # 3. Fallback 2: topi.vn (KHÔNG KHUYẾN NGHỊ)
        df = get_sjc_from_topi()  # Cần Selenium
        if not df.empty:
            return df

    return pd.DataFrame()
```

**Ưu điểm**:
- ✅ Có 2 lớp fallback

**Nhược điểm**:
- ❌ topi.vn KHÔNG realtime
- ❌ Chậm (cần browser automation)
- ❌ Phức tạp, khó bảo trì
- ❌ Dữ liệu có thể CŨ

---

## 🏆 KHUYẾN NGHỊ CUỐI CÙNG

### ✅ DÙNG CHỈ PHUQUYGROUP.VN

**Lý do**:
1. ✅ **Realtime data** - Quan trọng nhất cho giá vàng
2. ✅ **Nhanh & nhẹ** - Không làm chậm system
3. ✅ **Đơn giản** - Dễ implement và bảo trì
4. ✅ **Tin cậy** - Nguồn chính thức
5. ✅ **Đã test thành công** - Ready to use

### ❌ KHÔNG DÙNG TOPI.VN

**Lý do**:
1. ❌ **KHÔNG realtime** - Dữ liệu hardcode (19/6/2025)
2. ❌ **Cloudflare protection** - Khó scrape
3. ❌ **Cần browser automation** - Chậm, phức tạp
4. ❌ **Không phải API** - Là blog post, không ổn định

---

## 📦 CÁC FILE ĐÃ TẠO

### 1. `gold_fallback.py` ✅ (READY TO USE)

Module fallback chính cho **phuquygroup.vn**:

```python
from gold_fallback import get_sjc_from_phuquy, get_btmc_from_phuquy

df = get_sjc_from_phuquy()
print(df)
#          name buy_price sell_price
# Vàng miếng SJC  15080000   15280000
```

### 2. `gold_fallback_topi.py` ⚠️ (DEMO ONLY)

Demo parser cho **topi.vn** (KHÔNG KHUYẾN NGHỊ production use)

### 3. `fallback_phuquy_demo.py` 📝 (REFERENCE)

Demo test scrape phuquygroup.vn

### 4. `INTEGRATION_GUIDE.md` 📖 (GUIDE)

Hướng dẫn tích hợp chi tiết

---

## 🚀 CÁCH TÍCH HỢP

### Bước 1: Import

```python
# gold_data_pg.py
from gold_fallback import get_sjc_from_phuquy, get_btmc_from_phuquy
```

### Bước 2: Update method

Xem file **`INTEGRATION_GUIDE.md`** để có code đầy đủ.

### Bước 3: Test

```bash
cd TaiSanQuocTe
python3 gold_fallback.py
```

---

## 📊 TÓM TẮT SO SÁNH

| Tiêu chí | phuquygroup.vn | topi.vn |
|----------|----------------|---------|
| **Realtime** | ✅ | ❌ |
| **Dễ scrape** | ✅ | ❌ |
| **Nhanh** | ✅ (<1s) | ❌ (3-5s) |
| **Tin cậy** | ✅ | ⚠️ |
| **Bảo trì** | ✅ | ❌ |
| **Multi-brand** | ❌ | ✅ |
| **KHUYẾN NGHỊ** | ✅ **CÓ** | ❌ **KHÔNG** |

---

## 🎓 KẾT LUẬN

**Chốt lại 2 fallback cho hệ thống**:

1. ✅ **Primary**: phuquygroup.vn (Nên dùng)
2. ❌ **Secondary**: topi.vn (Không nên dùng)

**Chiến lược tối ưu**:
```
vnstock (primary)
   ↓ (thất bại)
phuquygroup.vn (fallback)
   ↓ (thất bại)
Báo lỗi
```

---

**Author**: Claude Code
**Date**: 2026-01-03
**Status**: ✅ RESEARCH COMPLETED
