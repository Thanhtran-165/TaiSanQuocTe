# International Metals - Rate Limit Issue

## ⚠️ Vấn đề hiện tại

Module `international_metals` đang gặp **Yahoo Finance Rate Limiting**.

### 🔍 Chi tiết lỗi:

```
ERROR:international_metals_pkg.core:Error fetching from Yahoo Finance:
429 Client Error: Too Many Requests for url: https://query2.finance.yahoo.com/...
```

## 📊 Nghĩa là gì?

### HTTP 429 - Too Many Requests
- **Yahoo Finance** giới hạn số lượng request từ một IP
- Khi vượt quá giới hạn → bị block tạm thời
- Thường kéo dài **15-30 phút** hoặc lâu hơn

### Tại sao bị?

1. **Test quá nhiều**: Đã test module nhiều lần liên tục
2. **Không có delay**: Gửi request quá nhanh
3. **Cùng một IP**: Yahoo detect và limit
4. **Public API**: Yahoo Finance không có official API cho developer

## 🔧 Giải pháp

### Giải pháp 1: Chờ đợi (Đơn giản nhất)
```bash
# Chờ 15-30 phút rồi thử lại
cd international_metals
python -c "from international_metals_pkg import get_gold_price; print(get_gold_price())"
```

### Giải pháp 2: Tăng delay giữa các request
```python
from international_metals_pkg import PreciousMetalsPrice
import time

pm = PreciousMetalsPrice(cache_duration=600)  # Tăng cache lên 10 phút

# Chờ giữa các lần gọi
gold = pm.get_price('gold')
time.sleep(5)  # Chờ 5 giây

silver = pm.get_price('silver')
```

### Giải pháp 3: Dùng VPN (Thay đổi IP)
```bash
# Kết nối VPN rồi thử lại
# IP mới sẽ có limit mới
python -c "from international_metals_pkg import get_gold_price; print(get_gold_price())"
```

### Giải pháp 4: Dùng cache (Khuyến nghị)
```python
# Cache 10 phút để giảm request
from international_metals_pkg import PreciousMetalsPrice

pm = PreciousMetalsPrice(cache_duration=600)  # 10 phút

# Lần gọi đầu - fetch từ API
gold1 = pm.get_price('gold')

# Lần gọi thứ 2 - lấy từ cache (không gọi API)
gold2 = pm.get_price('gold')
```

### Giải pháp 5: Chỉ dùng khi cần thiết
```python
# KHÔNG gọi liên tục
# ❌ Đừng làm thế này:
while True:
    gold = get_gold_price()  # Spam!

# ✅ Hãy làm thế này:
pm = PreciousMetalsPrice(cache_duration=300)
gold = pm.get_price('gold')  # Gọi 1 lần, dùng cache
```

## 📈 So sánh với các module khác

| Module | Nguồn | Rate Limit | Giải pháp |
|--------|-------|------------|-----------|
| **vn_gold_tracker** | vnstock API | Ít hơn | Database + cron job OK |
| **silver_scraper** | Scraping | Không rõ | Chỉ chạy khi cần |
| **international_metals** | Yahoo Finance | **CÓ** | Dùng cache, chờ delay |

## 💡 Khuyến nghị

### Cách dùng đúng:
```python
from international_metals_pkg import PreciousMetalsPrice

# 1. Dùng cache dài (5-10 phút)
pm = PreciousMetalsPrice(cache_duration=600)

# 2. Gửi request ít
gold = pm.get_price('gold')

# 3. Dùng kết quả đã cache
# Thay vì gọi lại ngay
```

### Cách dùng SAI:
```python
# ❌ KHÔNG LÀM THẾ NÀY!
while True:
    gold = get_gold_price(use_cache=False)  # Spam request!
    time.sleep(1)  # Vẫn quá nhanh!
```

## 🔄 Fallback mechanism

Module đã có fallback:
```
1. Yahoo Finance (Primary)
   ↓ 429 Rate Limit
2. MSN Money (Fallback)
   ↓ Could not parse (scraping issue)
3. Return None
```

**Vấn đề**: MSN Money fallback cũng chưa hoạt động tốt.

## 🛠️ Cải thiện trong tương lai

### Có thể làm:
1. ✅ Thêm delay vào code
2. ✅ Tăng default cache duration
3. ✅ Thêm nhiều nguồn fallback khác
4. ✅ Thêm warning khi sắp rate limit
5. ✅ Implement exponential backoff

### Ví dụ code cải thiện:
```python
import time

def get_price_with_retry(metal, max_retries=3):
    for i in range(max_retries):
        try:
            result = pm.get_price(metal, use_cache=False)
            if result:
                return result
        except Exception as e:
            if i < max_retries - 1:
                wait_time = 2 ** i  # 2s, 4s, 8s
                print(f"Thử lại sau {wait_time}s...")
                time.sleep(wait_time)
    return None
```

## 📝 Real-world usage

### Dùng OK (ít request):
```python
# Chạy 1 lần / 5 phút → OK
pm = PreciousMetalsPrice(cache_duration=300)
gold = pm.get_price('gold')
```

### Dùng NGUY HIỂM (nhiều request):
```python
# Chạy liên tục mỗi 1 giây → Bị rate limit!
while True:
    gold = get_gold_price(use_cache=False)
    time.sleep(1)  # ❌ Quá nhanh!
```

### Dùng TỐT (có cache):
```python
# Chạy mỗi 5 phút, dùng cache → Tốt
pm = PreciousMetalsPrice(cache_duration=300)

while True:
    gold = pm.get_price('gold')  # Dùng cache
    time.sleep(300)  # ✅ 5 phút
```

## 🎯 Best Practices

### 1. Luôn dùng cache
```python
pm = PreciousMetalsPrice(cache_duration=600)  # 10 phút
```

### 2. Gửi request ít nhất có thể
```python
# Thay vì gọi 3 lần:
gold1 = get_gold_price()
silver1 = get_silver_price()

# Hãy gọi 1 lần:
prices = get_all_metals_prices()
```

### 3. Không loop liên tục
```python
# ❌ KHÔNG:
while True:
    price = get_gold_price(use_cache=False)

# ✅ NÊN:
pm = PreciousMetalsPrice()
price = pm.get_price('gold', use_cache=True)
```

### 4. Xử lý lỗi gracefully
```python
try:
    gold = get_gold_price()
    if gold is None:
        print("Không thể lấy giá (rate limit?)")
        # Dùng giá cũ trong cache hoặc database
except Exception as e:
    print(f"Lỗi: {e}")
```

## 📊 Thống kê sử dụng

### Tần suất an toàn:
- ✅ **1 request / 5 phút**: An toàn
- ✅ **10 requests / giờ**: Vẫn OK
- ⚠️ **60 requests / giờ**: Có thể bị limit
- ❌ **1000 requests / giờ**: Chắc chắn bị limit

### Tính toán:
```
Nếu cache = 5 phút:
- 1 ngày = 24 giờ = 288 request
- Yahoo limit thường ~100-200 request/giờ

→ Vẫn an toàn nếu dùng cache đúng!
```

## 🔍 Kiểm tra status

### Test hiện tại:
```bash
cd international_metals
python -c "from international_metals_pkg import get_gold_price; print(get_gold_price())"
```

### Nếu vẫn bị 429:
```bash
# Chờ 15-30 phút
# Hoặc đổi VPN
# Hoặc dùng cache
```

## 📞 Support

Nếu vẫn gặp vấn đề:
1. Kiểm tra internet connection
2. Dùng VPN thay đổi IP
3. Tăng cache duration
4. Giảm tần suất request
5. Chờ 15-30 phút

---

**Tóm lại**: Code không có lỗi, chỉ đang bị Yahoo Finance rate limit. Dùng cache và gửi request ít hơn là OK.

**Last updated**: 2026-01-03
**Status**: ⚠️ Rate Limit (Expected behavior)
