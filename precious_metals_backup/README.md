# Precious Metals Price Tracker 🥇🥈

Module Python để lấy giá vàng và bạc theo thời gian thực từ nhiều nguồn với cơ chế fallback tự động.

## Tính năng ✨

- ✅ **Nhiều nguồn dữ liệu**: Yahoo Finance, MSN Money, Yahoo ETF
- ✅ **Fallback tự động**: Tự động chuyển sang nguồn khác khi nguồn chính fail
- ✅ **Caching thông minh**: Giảm số lượng request với cache duration có thể tùy chỉnh
- ✅ **Error handling**: Xử lý lỗi toàn diện
- ✅ **Dễ sử dụng**: API đơn giản và intuitively
- ✅ **Không cần API key**: Tất cả các nguồn đều miễn phí, không cần đăng ký

## Cài đặt 📦

```bash
pip install -r requirements.txt
```

## Nguồn dữ liệu 📊

| Nguồn | Loại | API Key | Mô tả |
|-------|------|---------|-------|
| Yahoo Finance | Chính | Không cần | Nguồn chính, lấy giá futures (GC=F, SI=F) |
| MSN Money | Fallback 1 | Không cần | Web scraping từ msn.com |
| Yahoo ETF | Fallback 2 | Không cần | Sử dụng ETF (GLD, SLV) |

## Cách sử dụng 🚀

### 1. Cơ bản nhất

```python
from precious_metals import get_gold_price, get_silver_price

# Lấy giá vàng
gold = get_gold_price()
print(f"Giá vàng: ${gold['price']}/oz")

# Lấy giá bạc
silver = get_silver_price()
print(f"Giá bạc: ${silver['price']}/oz")
```

### 2. Sử dụng với Class

```python
from precious_metals import PreciousMetalsPrice

pm = PreciousMetalsPrice(cache_duration=300)  # Cache 5 phút

# Lấy giá vàng
gold_price = pm.get_price('gold')
if gold_price:
    print(f"Giá: ${gold_price['price']}")
    print(f"Thay đổi: ${gold_price['change']} ({gold_price['change_percent']}%)")
    print(f"Cao nhất: ${gold_price['high']}")
    print(f"Thấp nhất: ${gold_price['low']}")
```

### 3. Lấy tất cả giá cùng lúc

```python
from precious_metals import get_all_metals_prices

prices = get_all_metals_prices()
print(f"Vàng: ${prices['gold']['price']}/oz")
print(f"Bạc: ${prices['silver']['price']}/oz")
```

### 4. Cache management

```python
from precious_metals import PreciousMetalsPrice

pm = PreciousMetalsPrice(cache_duration=600)  # Cache 10 phút

# Lần gọi đầu - fetch từ API
price1 = pm.get_price('gold')

# Lần gọi thứ 2 - lấy từ cache (nếu chưa hết hạn)
price2 = pm.get_price('gold')

# Xóa cache
pm.clear_cache()

# Fetch lại từ API
price3 = pm.get_price('gold')
```

## Kết quả trả về 📋

Mỗi lần gọi `get_price()` trả về một dict với các trường:

```python
{
    'source': 'Yahoo Finance',           # Nguồn dữ liệu
    'symbol': 'GC=F',                    # Symbol
    'price': 2034.50,                    # Giá hiện tại
    'change': 12.30,                     # Thay đổi ($)
    'change_percent': 0.61,              # Thay đổi (%)
    'high': 2040.00,                     # Giá cao nhất ngày
    'low': 2025.00,                      # Giá thấp nhất ngày
    'volume': 123456,                    # Khối lượng
    'timestamp': '2026-01-03T10:30:00'   # Thời gian
}
```

## Examples 📝

Chạy file example để thấy các cách sử dụng khác nhau:

```bash
python example_usage.py
```

Hoặc test trực tiếp:

```bash
python precious_metals.py
```

## Symbols 🏷️

### Gold
- Yahoo Futures: `GC=F`
- Yahoo ETF: `GLD` (SPDR Gold Shares)
- MSN Money: `XAUUSD`

### Silver
- Yahoo Futures: `SI=F`
- Yahoo ETF: `SLV` (iShares Silver Trust)
- MSN Money: `XAGUSD`

## Cơ chế Fallback 🔄

```
1. Yahoo Finance (Primary)
   ↓ (fail)
2. MSN Money (Fallback 1 - Web Scraping)
   ↓ (fail)
3. Yahoo ETF (Fallback 2)
   ↓ (fail)
4. Return None
```

## Về MSN Money 🌐

**MSN Money** (https://www.msn.com/en-us/money) là một trong những portal tài chính lớn nhất, cung cấp:

- ✅ Giá real-time cho vàng, bạc và nhiều tài sản khác
- ✅ Không cần API key
- ✅ Dữ liệu tin cậy từ Microsoft
- ✅ Web scraping hợp pháp

**Implementation**: Module sử dụng BeautifulSoup để parse HTML và extract giá từ MSN Money.

## Logging 📝

Module sử dụng Python's logging module. Enable logging để debug:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

## Lưu ý ⚠️

1. **Giá theo ounce**: Tất cả giá đều tính theo troy ounce (31.1035 gram)
2. **Currency**: USD
3. **Cache duration**: Mặc định 5 phút (300 giây)
4. **Rate limits**: Yahoo Finance có thể rate limit nếu call quá nhiều
5. **Market hours**: Giá futures chỉ update khi market mở
6. **Web scraping**: MSN Money có thể thay đổi cấu trúc HTML, cần update module

## Tính toán thêm ➗

### Chuyển sang gram

```python
# 1 troy ounce = 31.1035 gram
price_per_oz = gold_price['price']
price_per_gram = price_per_oz / 31.1035
```

### Tỷ lệ Gold/Silver

```python
from precious_metals import get_all_metals_prices

prices = get_all_metals_prices()
ratio = prices['gold']['price'] / prices['silver']['price']
print(f"Tỷ lệ Gold/Silver: {ratio:.2f}:1")
```

## Troubleshooting 🔧

### Lỗi "No data from Yahoo"

- Kiểm tra kết nối internet
- Thử lại sau vài phút (Yahoo có thể đang rate limit)
- Module sẽ tự động chuyển sang MSN Money

### Lỗi "Could not parse MSN Money"

- MSN Money có thể đã thay đổi cấu trúc HTML
- Module sẽ tự động chuyển sang Yahoo ETF
- Cần update parsing logic

### Cache không hoạt động

- Kiểm tra `cache_duration` setting
- Sử dụng `pm.clear_cache()` để xóa cache

### Web scraping fail

- Kiểm tra user-agent headers
- MSN Money có thể block requests
- Module sẽ tự động dùng Yahoo ETF

## Architecture 🏗️

```
PreciousMetalsPrice
├── Yahoo Finance (Primary)
│   ├── Futures (GC=F, SI=F)
│   └── ETF Fallback (GLD, SLV)
├── MSN Money (Fallback 1)
│   ├── Web Scraping
│   └── BeautifulSoup Parser
└── Yahoo ETF (Fallback 2)
    └── Last Resort
```

## So sánh với phiên bản GoldAPI

| Tính năng | GoldAPI Version | MSN Money Version |
|-----------|-----------------|-------------------|
| API Key | Cần | Không cần |
| Free tier | 100 req/ngày | Unlimited |
| Setup complexity | Phải đăng ký | Không cần |
| Reliability | Cao | Cao |
| Maintenance | Ít hơn | Cần update parser |

**Ưu điểm của MSN Money version**:
- ✅ Không cần đăng ký API key
- ✅ Unlimited requests
- ✅ Miễn phí hoàn toàn
- ✅ Dễ sử dụng hơn

## Dependencies 📚

- `yfinance` >= 0.2.28 - Yahoo Finance API
- `requests` >= 2.31.0 - HTTP requests
- `pandas` >= 2.0.0 - Data processing
- `beautifulsoup4` >= 4.12.0 - Web scraping
- `lxml` >= 4.9.0 - HTML parser

## Advanced Usage 🎓

### Custom MSM Implementation

Nếu bạn muốn custom MSM implementation:

```python
from precious_metals import PreciousMetalsPrice

pm = PreciousMetalsPrice()

# Override MSN Money method
def custom_msn_handler(metal):
    # Your custom logic here
    return data

pm._get_from_msn_money = custom_msn_handler
```

### Use với config file

```python
# config.py
MSM_API_KEY = ""  # Để trống nếu dùng MSN Money web scraping

# main.py
from config import MSM_API_KEY
from precious_metals import PreciousMetalsPrice

pm = PreciousMetalsPrice()
gold_price = pm.get_price('gold', msm_api_key=MSM_API_KEY)
```

## License 📄

MIT License

## Contributing 🤝

Contributions welcome! Vui lòng mở PR hoặc issue.

## Roadmap 🛣️

- [ ] Thêm platinum và palladium
- [ ] Hỗ trợ multiple currencies
- [ ] Thêm chart visualization
- [ ] Alert system
- [ ] Historical data analysis
- [ ] Integration với trading platforms

---

Made with ❤️ for tracking precious metals prices

**Nguồn dữ liệu**: Yahoo Finance + MSN Money
**Không cần API key** - Miễn phí và unlimited!
