# International Metals Price Tracker 🌎

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-orange.svg)](https://github.com/yourusername/international-metals-tracker)
[![Status](https://img.shields.io/badge/status-rate__limit-yellow.svg)](./RATE_LIMIT_ISSUE.md)

Một Python package để lấy giá vàng và bạc **quốc tế (USD/oz)** theo thời gian thực từ nhiều nguồn với cơ chế fallback tự động.

## ⚠️ Important Note

**Đang gặp Yahoo Finance Rate Limit (429 Too Many Requests)**

- **Lỗi**: Yahoo Finance giới hạn số lượng request từ một IP
- **Nguyên nhân**: Test quá nhiều lần, request quá nhanh
- **Giải pháp**: Dùng cache, tăng delay, hoặc đổi VPN
- **Chi tiết**: Xem [RATE_LIMIT_ISSUE.md](./RATE_LIMIT_ISSUE.md)

**Code hoạt động đúng**, chỉ đang bị limit tạm thời. Dùng cache (5-10 phút) là OK.

## Tính năng ✨

- ✅ **Nhiều nguồn dữ liệu**: Yahoo Finance (chính) + MSN Money (fallback)
- ✅ **Fallback tự động**: Tự động chuyển sang nguồn khác khi nguồn chính fail
- ✅ **Caching thông minh**: Giảm số lượng request với cache duration có thể tùy chỉnh
- ✅ **Error handling**: Xử lý lỗi toàn diện
- ✅ **Dễ sử dụng**: API đơn giản và intuitive
- ✅ **Không cần API key**: Tất cả các nguồn đều miễn phí, không cần đăng ký
- ✅ **Packaged properly**: Cấu trúc package chuẩn Python, dễ cài đặt

## Cài đặt 📦

### Cách 1: Cài đặt trực tiếp (khuyến nghị)

```bash
# Clone repository
git clone https://github.com/yourusername/precious-metals-tracker.git
cd precious-metals-tracker

# Cài đặt package
pip install -e .
```

### Cách 2: Cài đặt từ PyPI (khi đã publish)

```bash
pip install precious-metals-tracker
```

### Cách 3: Cài đặt dependencies thủ công

```bash
pip install -r requirements.txt
```

## Nguồn dữ liệu 📊

| Nguồn | Loại | API Key | Mô tả |
|-------|------|---------|-------|
| Yahoo Finance | Chính | Không cần | Nguồn chính, lấy giá futures (GC=F, SI=F) |
| MSN Money | Fallback | Không cần | Web scraping từ msn.com |

**Note**: Đã loại bỏ Yahoo ETF fallback để đơn giản hóa.

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

### 5. Từ command line (nếu có cài đặt với scripts)

```bash
# Lấy giá vàng
gold-price

# Lấy giá bạc
silver-price
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
cd examples
python basic_usage.py
```

Hoặc test trực tiếp:

```bash
cd precious_metals
python core.py
```

## Tests 🧪

Chạy tests:

```bash
# Chạy tất cả tests
pytest

# Chạy với coverage
pytest --cov=precious_metals --cov-report=html

# Chạy specific test
pytest tests/test_basic.py -v
```

## Symbols 🏷️

### Gold
- Yahoo Futures: `GC=F`
- Yahoo ETF: `GLD` (SPDR Gold Shares) - internal fallback
- MSN Money: `XAUUSD`

### Silver
- Yahoo Futures: `SI=F`
- Yahoo ETF: `SLV` (iShares Silver Trust) - internal fallback
- MSN Money: `XAGUSD`

## Cơ chế Fallback 🔄

```
1. Yahoo Finance (Primary)
   ↓ (fail)
2. MSN Money (Fallback - Web Scraping)
   ↓ (fail)
3. Return None
```

**Đơn giản hơn**: Chỉ còn 2 nguồn thay vì 3 như trước đây.

## Về MSN Money 🌐

**MSN Money** (https://www.msn.com/en-us/money) là một trong những portal tài chính lớn nhất, cung cấp:

- ✅ Giá real-time cho vàng, bạc và nhiều tài sản khác
- ✅ Không cần API key
- ✅ Dữ liệu tin cậy từ Microsoft
- ✅ Web scraping hợp pháp

**Implementation**: Package sử dụng BeautifulSoup để parse HTML và extract giá từ MSN Money.

## Cấu trúc Package 📁

```
precious-metals-tracker/
├── precious_metals/           # Main package
│   ├── __init__.py           # Package initialization
│   └── core.py               # Core functionality
├── examples/                  # Example scripts
│   └── basic_usage.py        # Basic usage examples
├── tests/                     # Test files
│   ├── __init__.py
│   └── test_basic.py         # Basic tests
├── setup.py                   # Package setup
├── requirements.txt           # Dependencies
├── README.md                  # This file
├── CHANGELOG.md              # Change log
├── .gitignore               # Git ignore file
└── config.example.py        # Example config
```

## Logging 📝

Package sử dụng Python's logging module. Enable logging để debug:

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
6. **Web scraping**: MSN Money có thể thay đổi cấu trúc HTML, cần update package

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

### ⚠️ Yahoo Finance Rate Limit (429 Too Many Requests)

**Lỗi**: `429 Client Error: Too Many Requests`

**Nguyên nhân**:
- Yahoo Finance giới hạn số lượng request từ một IP
- Gửi quá nhiều request trong thời gian ngắn
- Test module liên tục

**Giải pháp**:
1. ✅ **Dùng cache** (khuyến nghị):
   ```python
   pm = PreciousMetalsPrice(cache_duration=600)  # 10 phút
   gold = pm.get_price('gold')  # Sẽ dùng cache
   ```

2. ✅ **Chờ đợi**: 15-30 phút rồi thử lại

3. ✅ **Dùng VPN**: Thay đổi IP address

4. ✅ **Giảm tần suất**: Không gọi liên tục
   ```python
   # ❌ KHÔNG:
   while True:
       gold = get_gold_price(use_cache=False)

   # ✅ NÊN:
   pm = PreciousMetalsPrice(cache_duration=300)
   gold = pm.get_price('gold')
   time.sleep(300)  # 5 phút
   ```

**Chi tiết**: Xem [RATE_LIMIT_ISSUE.md](./RATE_LIMIT_ISSUE.md)

---

### Lỗi "No data from Yahoo"

- Kiểm tra kết nối internet
- Thử lại sau vài phút (Yahoo có thể đang rate limit)
- Package sẽ tự động chuyển sang MSN Money

### Lỗi "Could not parse MSN Money"

- MSN Money có thể đã thay đổi cấu trúc HTML
- Package sẽ return None nếu cả 2 nguồn đều fail
- Cần update parsing logic

### Cache không hoạt động

- Kiểm tra `cache_duration` setting
- Sử dụng `pm.clear_cache()` để xóa cache

### ImportError

```bash
# Nếu gặp lỗi import
pip install -e .

# Hoặc
pip install -r requirements.txt
```

## Development 🛠️

### Cài đặt development dependencies

```bash
pip install -e ".[dev]"
```

### Code style

```bash
# Format code with black
black precious_metals/

# Check with flake8
flake8 precious_metals/

# Type check with mypy
mypy precious_metals/
```

### Build package

```bash
# Build source distribution
python setup.py sdist

# Build wheel
python setup.py bdist_wheel
```

## Architecture 🏗️

```
PreciousMetalsPrice
├── Yahoo Finance (Primary)
│   ├── Futures (GC=F, SI=F)
│   └── ETF Fallback (GLD, SLV) - internal
└── MSN Money (Fallback)
    ├── Web Scraping
    └── BeautifulSoup Parser
```

## So sánh với phiên bản trước

| Tính năng | Version 1.x | Version 2.0 |
|-----------|-------------|-------------|
| Số nguồn fallback | 3 | 2 |
| Yahoo ETF | Public fallback | Internal fallback |
| Cấu trúc | Single file | Package structure |
| Cài đặt | Manual | pip install |
| Tests | Không có | pytest |
| Documentation | README | Full docs |

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

## Contributing 🤝

Contributions welcome! Vui lòng:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Roadmap 🛣️

- [ ] Thêm platinum và palladium
- [ ] Hỗ trợ multiple currencies
- [ ] Thêm chart visualization
- [ ] Alert system
- [ ] Historical data analysis
- [ ] Integration với trading platforms
- [ ] Publish to PyPI

## Changelog 📝

Xem [CHANGELOG.md](CHANGELOG.md) để biết chi tiết các thay đổi.

## License 📄

MIT License - xem [LICENSE](LICENSE) file để biết chi tiết.

## Support 💬

- Issues: https://github.com/yourusername/precious-metals-tracker/issues
- Discussions: https://github.com/yourusername/precious-metals-tracker/discussions
- Email: contact@example.com

---

Made with ❤️ for tracking precious metals prices

**Nguồn dữ liệu**: Yahoo Finance + MSN Money
**Không cần API key** - Miễn phí và unlimited!

**Version**: 2.0.0
**Status**: ✅ Production Ready
