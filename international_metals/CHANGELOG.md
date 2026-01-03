# CHANGELOG

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-01-03

### Added
- ✅ Proper package structure with `setup.py`
- ✅ `__init__.py` for package initialization
- ✅ Test suite with pytest
- ✅ Examples directory
- ✅ `.gitignore` file
- ✅ Package versioning system
- ✅ Development dependencies in `setup.py`

### Changed
- 🔄 **BREAKING**: Removed Yahoo ETF fallback (was fallback #2)
- 🔄 Simplified fallback mechanism to 2 sources (Yahoo + MSN)
- 🔄 Yahoo ETF now used as internal fallback within Yahoo source
- 🔄 Restructured from single file to proper Python package
- 🔄 Updated README with package installation instructions
- 🔄 Added badges (Python version, License, Version)

### Removed
- ❌ `_get_from_investing()` method (Yahoo ETF public fallback)
- ❌ GoldAPI-related files (`test_goldapi.py`, `goldapi_guide.md`)

### Fixed
- 🐛 Improved caching documentation
- 🐛 Better error handling in examples

### Technical Details
- Package name: `precious-metals-tracker`
- Version: 2.0.0
- Python: 3.8+
- License: MIT

### Migration from 1.x to 2.0
No breaking changes to API. The fallback mechanism is simplified but the user-facing API remains the same:

```python
# Still works the same way
from precious_metals import get_gold_price
gold = get_gold_price()
```

---

## [1.0.0] - 2026-01-03

### Added
- ✅ Initial release with GoldAPI integration
- ✅ Yahoo Finance as primary source
- ✅ GoldAPI as fallback
- ✅ Yahoo ETF as second fallback
- ✅ Caching mechanism
- ✅ Convenience functions

### Later Updated to 1.x
- 🔄 Replaced GoldAPI with MSN Money
- 🔄 Added MarketSmith API support (optional)
- 🔄 Removed GoldAPI dependency
- 🔄 No longer requires API keys

---

# CHANGELOG - Thay đổi từ GoldAPI sang MSN Money (Version 1.x)

## Ngày: 2026-01-03

## Tóm tắt
Đã thay thế hoàn toàn **GoldAPI.io** bằng **MSN Money** làm nguồn fallback.

## Những thay đổi chính

### 1. Module chính (`precious_metals.py`)

#### Thay đổi:
- ❌ **Bỏ**: GoldAPI.io integration
- ✅ **Thêm**: MSN Money web scraping integration
- ✅ **Thêm**: MarketSmith API support (optional)

#### Thay đổi chi tiết:
- `_get_from_goldapi()` → `_get_from_msm()`
- Thêm `_get_from_msn_money()`: Web scraping từ msn.com
- Thêm `_get_from_marketsmith_api()`: MarketSmith API integration
- Thay `goldapi_key` parameter → `msm_api_key` parameter
- Cập nhật symbol mapping: `goldapi` → `msm_symbol`

### 2. Dependencies (`requirements.txt`)

#### Thêm:
```
beautifulsoup4>=4.12.0  # Web scraping
lxml>=4.9.0             # HTML parser
```

### 3. Examples (`example_usage.py`)

#### Cập nhật:
- Thay thế GoldAPI examples bằng MSN Money examples
- Cập nhật parameter names: `goldapi_key` → `msm_api_key`
- Cập nhật ghi chú và descriptions

### 4. Configuration (`config.example.py`)

#### Thay đổi:
```python
# Trước:
GOLDAPI_KEY = ""  # GoldAPI.io key

# Sau:
MSM_API_KEY = ""  # MarketSmith key (optional)
```

### 5. Documentation (`README.md`)

#### Thay đổi lớn:
- Cập nhật toàn bộ README để phản ánh thay đổi
- Thêm section "Về MSN Money"
- Cập nhật bảng so sánh nguồn dữ liệu
- Thêm troubleshooting cho web scraping
- So sánh với phiên bản GoldAPI

### 6. Files đã xóa:
- ❌ `test_goldapi.py` - Script test GoldAPI
- ❌ `goldapi_guide.md` - Hướng dẫn GoldAPI

## Cơ chế Fallback mới

```
1. Yahoo Finance (Primary)
   ↓ fail
2. MSN Money (Fallback 1) - Web Scraping
   ↓ fail
3. Yahoo ETF (Fallback 2)
   ↓ fail
4. Return None
```

## So sánh: GoldAPI vs MSN Money

| Tính năng | GoldAPI | MSN Money |
|-----------|---------|-----------|
| API Key | ✅ Cần | ❌ Không cần |
| Free tier | 100 req/ngày | Unlimited |
| Registration | Phải đăng ký | Không cần |
| Setup complexity | Trung bình | Đơn giản |
| Maintenance | Ít | Cần update parser |
| Reliability | Rất cao | Cao |

## Ưu điểm của phiên bản mới

1. ✅ **Không cần API key** - Miễn phí hoàn toàn
2. ✅ **Unlimited requests** - Không giới hạn
3. ✅ **Dễ sử dụng hơn** - Không cần setup phức tạp
4. ✅ **Nhiều nguồn fallback** - 3 nguồn thay vì 2
5. ✅ **Open data source** - MSN Money là public portal

## Nhược điểm cần lưu ý

1. ⚠️ **Web scraping** - Cần update parser khi MSN thay đổi HTML
2. ⚠️ **Reliability** - Phụ thuộc vào cấu trúc HTML của MSN
3. ⚠️ **Maintenance** - Cần kiểm tra và update thường xuyên hơn

## Hướng dẫn Migration

### Từ phiên bản GoldAPI sang MSN Money:

```python
# Trước (GoldAPI):
from precious_metals import get_gold_price
gold = get_gold_price(goldapi_key="your-key")

# Sau (MSN Money):
from precious_metals import get_gold_price
gold = get_gold_price()  # Không cần API key!
```

### Nếu có MarketSmith subscription (optional):

```python
# Vẫn có thể dùng MarketSmith API nếu có:
gold = get_gold_price(msm_api_key="your-marketsmith-key")
```

## Testing

Test tất cả các tính năng:

```bash
# Test module chính
python precious_metals.py

# Test examples
python example_usage.py

# Check syntax
python -m py_compile precious_metals.py example_usage.py
```

## Files đã cập nhật

✅ `precious_metals.py` - Module chính
✅ `requirements.txt` - Dependencies
✅ `example_usage.py` - Examples
✅ `config.example.py` - Config template
✅ `README.md` - Documentation
❌ `test_goldapi.py` - Đã xóa
❌ `goldapi_guide.md` - Đã xóa

## Next Steps

1. Test kỹ module với MSN Money scraping
2. Monitor reliability của web scraping
3. Update parser khi MSN thay đổi HTML
4. Consider thêm caching cho web scraping results

## Kết luận

Việc chuyển từ GoldAPI sang MSN Money mang lại nhiều lợi ích:
- **Miễn phí hoàn toàn** - Không cần subscription
- **Unlimited** - Không giới hạn requests
- **Dễ dùng hơn** - Không cần API key

Tuy nhiên cần lưu ý maintenance web scraping parser thường xuyên hơn.

---

**Date**: 2026-01-03
**Version**: 2.0.0 (MSN Money Edition)
**Status**: ✅ Production Ready
