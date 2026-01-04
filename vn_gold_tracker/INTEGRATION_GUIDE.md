# 📋 HƯỚNG DẪN TÍCH HỢP FALLBACK CHO GOLD_SJC

## 📁 Các file đã tạo

1. **`gold_fallback.py`** - Module fallback chính
2. **`fallback_phuquy_demo.py`** - Demo/test scraper

## ✅ Kết quả nghiên cứu

### Nguồn fallback: **phuquygroup.vn** ✅

**Đã test thành công!**

```
Vàng miếng SJC: 15,080,000 - 15,280,000 VNĐ/chỉ
```

### Cấu trúc HTML

```html
<table class="m-auto text-center">
    <tbody>
        <tr>
            <td>Vàng miếng SJC</td>
            <td>15,080,000</td>  <!-- buy_price -->
            <td>15,280,000</td>  <!-- sell_price -->
        </tr>
    </tbody>
</table>
```

### Các nguồn KHÔNG dùng được ❌

1. **topi.vn/gia-bac-hom-nay.html** - Chỉ có GIÁ BẠC, không có GIÁ VÀNG
2. **giabac.vn** - Không có bảng giá cụ thể

---

## 🔧 Cách tích hợp vào `gold_data_pg.py`

### Bước 1: Import module

```python
# Thêm vào đầu file gold_data_pg.py
from gold_fallback import get_sjc_from_phuquy, get_btmc_from_phuquy
```

### Bước 2: Sửa method `get_sjc_gold_price()`

Tìm dòng 190-207 trong `gold_data_pg.py`:

```python
def get_sjc_gold_price(self, save_to_db: bool = True) -> pd.DataFrame:
    """Lấy giá vàng SJC hiện tại"""
    try:
        from vnstock.explorer.misc.gold_price import sjc_gold_price
        df = sjc_gold_price()

        if save_to_db and not df.empty:
            self._save_sjc_to_db(df)

        print(f"✓ Đã lấy giá vàng SJC ({len(df)} loại) - {datetime.now().strftime('%H:%M:%S')}")
        return df

    except ImportError:
        print("⚠ vnstock không có. Cài: pip install vnstock")
        return pd.DataFrame()
    except Exception as e:
        print(f"✗ Lỗi: {e}")
        return pd.DataFrame()
```

**THAY THÀNH:**

```python
def get_sjc_gold_price(self, save_to_db: bool = True, use_fallback: bool = True) -> pd.DataFrame:
    """
    Lấy giá vàng SJC hiện tại
    
    Args:
        save_to_db: Lưu vào database
        use_fallback: Dùng phuquygroup.vn khi vnstock thất bại
    """
    # 1. Thử lấy từ vnstock trước
    try:
        from vnstock.explorer.misc.gold_price import sjc_gold_price
        df = sjc_gold_price()

        if not df.empty:
            if save_to_db:
                self._save_sjc_to_db(df)
            print(f"✓ [vnstock] Đã lấy giá vàng SJC ({len(df)} loại)")
            return df

    except Exception as e:
        print(f"⚠️  vnstock thất bại: {e}")

    # 2. Fallback sang phuquygroup.vn
    if use_fallback:
        print("🔄 Đang thử fallback từ phuquygroup.vn...")
        try:
            df = get_sjc_from_phuquy()

            if not df.empty:
                if save_to_db:
                    self._save_sjc_to_db(df)
                print(f"✓ [fallback] Đã lấy giá vàng SJC từ phuquygroup.vn")
                return df
            else:
                print("❌ Fallback thất bại: Không có dữ liệu")

        except Exception as e:
            print(f"❌ Fallback lỗi: {e}")

    return pd.DataFrame()
```

### Bước 3: Tương tự cho BTMC

Áp dụng logic tương tự cho `get_btmc_gold_price()`:

```python
def get_btmc_gold_price(self, save_to_db: bool = True, use_fallback: bool = True) -> pd.DataFrame:
    """Lấy giá vàng BTMC hiện tại"""
    # 1. Thử vnstock
    try:
        from vnstock.explorer.misc.gold_price import btmc_goldprice
        df = btmc_goldprice()

        if not df.empty:
            if save_to_db:
                self._save_btmc_to_db(df)
            print(f"✓ [vnstock] Đã lấy giá vàng BTMC ({len(df)} loại)")
            return df

    except Exception as e:
        print(f"⚠️  vnstock thất bại: {e}")

    # 2. Fallback
    if use_fallback:
        print("🔄 Đang thử fallback từ phuquygroup.vn...")
        try:
            df = get_btmc_from_phuquy()

            if not df.empty:
                if save_to_db:
                    self._save_btmc_to_db(df)
                print(f"✓ [fallback] Đã lấy giá vàng BTMC từ phuquygroup.vn")
                return df

        except Exception as e:
            print(f"❌ Fallback lỗi: {e}")

    return pd.DataFrame()
```

---

## 🧪 Test

```bash
cd TaiSanQuocTe
python3 gold_fallback.py
```

**Kết quả:**
```
✅ [fallback] Đã lấy giá vàng SJC từ phuquygroup.vn
   Vàng miếng SJC: 15,080,000 - 15,280,000 VNĐ/chỉ
```

---

## 📦 Dependencies cần thiết

```bash
pip install requests beautifulsoup4 pandas
```

---

## ⚠️ Lưu ý

1. **Rate limiting**: Không scrape quá nhiều, có thể bị block
2. **HTML structure**: Nếu phuquygroup.vn thay đổi HTML, cần update lại selector
3. **Fallback priority**: vnstock > phuquygroup.vn > báo lỗi
4. **Logging**: Nên log rõ nguồn dữ liệu (vnstock hay fallback)

---

## 📊 So sánh

| Source | Ưu điểm | Nhược điểm |
|--------|---------|------------|
| **vnstock** | • Chính thức<br>• Đầy đủ dữ liệu<br>• API ổn định | • Phải cài package<br>• Phụ thuộc internet |
| **phuquygroup.vn** | • Không cần cài<br>• Fallback tốt<br>• Cập nhật real-time | • Web scraping<br>• Có thể thay đổi HTML<br>• Cần kiểm tra thường xuyên |

---

## 🎓 Author

Claude Code - 2026-01-03
