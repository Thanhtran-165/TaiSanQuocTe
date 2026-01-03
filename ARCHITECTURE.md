# 🏗️ WORD ASSET - TỔNG QUAN KIẾN TRÚC

## 📊 Cấu trúc tổng thể

```
Word Asset/
│
├── 🎨 ui/                          # LỚP GIAO DIỆN (NEW!)
│   ├── app.py                     # Streamlit UI
│   └── data_fetcher.py            # Data aggregation layer
│
├── 🇻🇳 vn_gold_tracker/            # LỚP DỮ LIỆU 1
│   ├── gold_data_pg.py            # Vàng SJC + USD/VND
│   └── auto_collect_db.py         # Auto collection
│
├── 🥈 silver_scraper/              # LỚP DỮ LIỆU 2
│   └── src/silver_scraper.py      # Bạc Phú Quý
│
└── 🌎 international_metals/        # LỚP DỮ LIỆU 3
    └── international_metals_pkg/  # Vàng bạc thế giới
        └── core.py                # Yahoo Finance + MSN Money
```

---

## 🔄 DATA FLOW ARCHITECTURE

```
┌──────────────────────────────────────────────────────┐
│             USER (Browser/Mobile)                    │
└───────────────────┬──────────────────────────────────┘
                    │ HTTP Request
                    ↓
┌──────────────────────────────────────────────────────┐
│          UI LAYER (ui/app.py)                        │
│  - Streamlit web interface                           │
│  - Display data & user interactions                  │
└───────────────────┬──────────────────────────────────┘
                    │ Call data_fetcher
                    ↓
┌──────────────────────────────────────────────────────┐
│      DATA AGGREGATION LAYER (data_fetcher.py)        │
│  - Fetch from all 3 data sources                     │
│  - Calculate spreads                                 │
│  - Format data for UI                                │
└──────┬──────────────┬──────────────┬──────────────────┘
       │              │              │
       ↓              ↓              ↓
┌──────────────┐ ┌──────────┐ ┌────────────────┐
│ DATA SOURCE 1│ │DATA SRC 2│ │  DATA SOURCE 3 │
│vn_gold_      │ │silver_   │ │international   │
│tracker       │ │scraper   │ │_metals         │
├──────────────┤ ├──────────┤ ├────────────────┤
│• Vàng SJC    │ │• Bạc PQ  │ │• Gold World    │
│• Vàng BTMC   │ │• 6 types │ │• Silver World  │
│• USD/VND     │ │          │ │• Yahoo Finance │
│• Database    │ │          │ │• MSN Money     │
└──────┬───────┘ └────┬─────┘ └──────┬─────────┘
       │              │               │
       ↓              ↓               ↓
┌────────────────────────────────────────────────────┐
│         EXTERNAL DATA SOURCES                       │
│  • vnstock API / phuquygroup.vn                    │
│  • giabac.phuquygroup.vn                           │
│  • Yahoo Finance / MSN Money                       │
└────────────────────────────────────────────────────┘
```

---

## 🎯 3-LAYER ARCHITECTURE

### Layer 1: DATA SOURCES (Bottom)

**Mục đích:** Fetch raw data từ external sources

**Components:**
1. **vn_gold_tracker** (`vn_gold_tracker/gold_data_pg.py`)
   - Input: vnstock API, phuquygroup.vn
   - Output: SJC/BTMC prices, USD/VND rate
   - Storage: SQLite/PostgreSQL

2. **silver_scraper** (`silver_scraper/src/silver_scraper.py`)
   - Input: giabac.phuquygroup.vn
   - Output: 6 silver price types
   - Storage: JSON/CSV

3. **international_metals** (`international_metals_pkg/core.py`)
   - Input: Yahoo Finance, MSN Money
   - Output: Gold/Silver world prices
   - Caching: In-memory (5-10 min)

**Characteristics:**
- ✅ Independent modules
- ✅ Can be used standalone
- ✅ Each has own data source
- ✅ Error handling & fallback

---

### Layer 2: DATA AGGREGATION (Middle)

**Mục đích:** Combine data from all sources & calculate spreads

**Component:** `ui/data_fetcher.py`

**Responsibilities:**
```python
class PriceDataFetcher:
    # 1. Fetch data from all 3 sources
    def fetch_vnd_usd_rate() -> float
    def fetch_sjc_gold() -> Dict
    def fetch_phuquy_silver() -> Dict
    def fetch_international_prices() -> Dict

    # 2. Calculate spreads
    def calculate_gold_spread(sjc_price, intl_price, usd_vnd) -> Dict
    def calculate_silver_spread(pq_price, intl_price, usd_vnd) -> Dict

    # 3. Format for UI
    def get_formatted_data() -> Dict
```

**Data Transformation:**
```
Raw Data → Normalized → Calculated → Formatted
  (3 sources)   (unified)    (spreads)    (for UI)
```

**Key Calculations:**
- Unit conversion: USD/oz → VND/lượng
- Spread calculation: VN price - World price
- Percentage: Spread / World price × 100

---

### Layer 3: PRESENTATION (Top)

**Mục đích:** Display data to user in beautiful UI

**Component:** `ui/app.py` (Streamlit)

**Features:**
1. **Tab 1: Today**
   - Main price cards (4 columns)
   - Spread visualization (2 columns)
   - Additional info (3 columns)

2. **Tab 2: History** (Coming soon)
   - Historical charts
   - Trend analysis

3. **Tab 3: Comparison**
   - Comparison table
   - Bar charts

**UI/UX:**
- Responsive design
- Auto-refresh
- Manual refresh button
- Data caching (10 min)
- Beautiful gradient cards
- Color-coded changes

---

## 📊 DATA MODEL

### Input Data (from sources):

```python
# vn_gold_tracker
{
    'type': 'Vàng SJC 1L-10L',
    'buy': 80000000,  # VND/lượng
    'sell': 82000000,
    'unit': 'VND/lượng'
}

# silver_scraper
{
    'type': 'Bạc miếng Phú Quý 999 1 lượng',
    'buy': 2700000,  # VND/lượng
    'sell': 2830000,
    'unit': 'VND/lượng'
}

# international_metals
{
    'price': 2034.50,  # USD/oz
    'change': 12.30,
    'change_percent': 0.61,
    'unit': 'USD/oz'
}
```

### Internal Data (aggregated):

```python
{
    'sjc_gold': {
        'price': 80000000,
        'unit': 'VND/lượng',
        'source': 'SJC'
    },
    'intl_gold': {
        'price': 2034.50,
        'unit': 'USD/oz',
        'source': 'Yahoo Finance'
    },
    'gold_spread': {
        'spread_vnd': 5000000,
        'spread_percent': 6.25,
        'intl_in_vnd': 50862500,  # VND/oz
        'intl_per_luong': 42200000  # VND/lượng
    }
}
```

### Output Data (for UI):

```python
{
    'display_price': '80,000,000 VND',
    'display_change': '+5,000,000 (+6.25%)',
    'color': 'positive',  # for styling
    'icon': '🇻🇳'
}
```

---

## 🔢 CONVERSION LOGIC

### Constants:

```python
OZ_TO_GRAM = 31.1035      # 1 troy ounce
LUONG_TO_GRAM = 37.5      # 1 lượng (Việt Nam)
OZ_TO_LUONG = 0.8294      # 31.1035 / 37.5
```

### Formula:

```python
# Convert international price (USD/oz) to VND/lượng
def convert_usd_oz_to_vnd_luong(price_usd_oz, usd_vnd_rate):
    price_vnd_oz = price_usd_oz * usd_vnd_rate
    price_vnd_luong = price_vnd_oz * OZ_TO_LUONG
    return price_vnd_luong

# Calculate spread
def calculate_spread(price_vn, price_intl_vnd_luong):
    spread_vnd = price_vn - price_intl_vnd_luong
    spread_pct = (spread_vnd / price_intl_vnd_luong) * 100
    return spread_vnd, spread_pct
```

### Example:

```python
# Gold
intl_gold = 2034.50  # USD/oz
usd_vnd = 25000     # VND

# Convert
intl_vnd_oz = 2034.50 * 25000 = 50,862,500 VND/oz
intl_vnd_luong = 50,862,500 * 0.8294 = 42,200,000 VND/lượng

# Spread (SJC = 80,000,000 VND/lượng)
spread = 80,000,000 - 42,200,000 = 37,800,000 VND
spread_pct = (37,800,000 / 42,200,000) * 100 = 89.57%
```

---

## 🔌 INTEGRATION POINTS

### 1. UI → Data Fetcher

```python
# In app.py
fetcher = PriceDataFetcher()
data = fetcher.get_formatted_data()
```

### 2. Data Fetcher → vn_gold_tracker

```python
# In data_fetcher.py
from vn_gold_tracker.gold_data_pg import GoldDataPG

self.gold_fetcher = GoldDataPG()
result = self.gold_fetcher.get_sjc_gold_price()
```

### 3. Data Fetcher → silver_scraper

```python
from silver_scraper.src.silver_scraper import SilverPriceScraper

self.silver_fetcher = SilverPriceScraper()
data = self.silver_fetcher.get_silver_prices()
```

### 4. Data Fetcher → international_metals

```python
from international_metals_pkg import PreciousMetalsPrice

self.intl_fetcher = PreciousMetalsPrice(cache_duration=600)
gold_price = self.intl_fetcher.get_price('gold')
```

---

## 🔐 ERROR HANDLING

### Layer 1 (Data Sources):

```python
# vn_gold_tracker
try:
    result = vnstock.get_gold_price()
except:
    result = fallback_phuquygroup.get_gold_price()

# international_metals
try:
    result = yahoo_finance.get_price()
except:
    result = msn_money.get_price()
```

### Layer 2 (Data Aggregation):

```python
# If any source fails, use None or cached data
if sjc_price is None:
    sjc_price = self.cached_data.get('sjc_price')

# Calculate spread only if all data available
if all([sjc_price, intl_price, usd_vnd]):
    spread = self.calculate_spread(...)
else:
    spread = None
```

### Layer 3 (UI):

```python
# Display error message if data unavailable
if data['sjc_gold']['price'] is None:
    st.warning("Không thể lấy giá vàng SJC")
else:
    st.metric("Vàng SJC", data['sjc_gold']['price'])
```

---

## ⚡ PERFORMANCE OPTIMIZATION

### Caching Strategy:

```python
# Layer 1: Source-level caching
# international_metals has 10-min cache

# Layer 2: Aggregation-level caching
@st.cache_resource(ttl=600)
def get_fetcher():
    return PriceDataFetcher()

# Layer 3: UI-level caching
# Streamlit auto-caches component outputs
```

### Request Reduction:

```python
# Instead of:
gold = get_gold_price()      # Request 1
silver = get_silver_price()  # Request 2

# Do this:
prices = get_all_metals_prices()  # Single batch request
```

### Async Loading (Future):

```python
# Can implement async fetching
import asyncio

async def fetch_all():
    results = await asyncio.gather(
        fetch_sjc_gold(),
        fetch_phuquy_silver(),
        fetch_international_prices()
    )
    return results
```

---

## 🚀 SCALABILITY

### Current State:

```
1 user → 1 instance → 3 data sources
```

### Future Scaling:

```
Multiple users → Load balancer → Multiple instances
                              ↓
                         Shared Cache (Redis)
                              ↓
                         Database (PostgreSQL)
```

### Horizontal Scaling:

1. **Backend API:**
   - FastAPI instead of Streamlit
   - Multiple workers
   - Load balancer (Nginx)

2. **Database:**
   - PostgreSQL instead of SQLite
   - Connection pooling
   - Replication

3. **Caching:**
   - Redis for distributed cache
   - Invalidate on updates
   - TTL-based expiration

---

## 📝 CONCLUSION

### Architecture Type:

**3-Layer Architecture with Data Aggregation**

**Why this design?**
- ✅ **Separation of Concerns:** Each layer has clear responsibility
- ✅ **Modularity:** Can swap out data sources without affecting UI
- ✅ **Reusability:** Each module can be used standalone
- ✅ **Maintainability:** Easy to debug and update
- ✅ **Scalability:** Can scale each layer independently

### Key Benefits:

1. **Flexible UI:** Can add web, mobile, desktop UIs without changing data sources
2. **Independent Modules:** Each data source works alone
3. **Easy Testing:** Can test each layer separately
4. **Future-Proof:** Easy to add new data sources or UI frameworks

---

**Architecture Version:** 1.0
**Last Updated:** 2026-01-03
**Status:** ✅ Production Ready
