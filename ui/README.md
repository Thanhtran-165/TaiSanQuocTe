# 🪙 Price Tracker UI

Giao diện theo dõi giá vàng và bạc - Việt Nam & Quốc tế

## ✨ Tính năng

### Tab 1: 📅 Today (Hiện tại)
- ✅ **Giá vàng SJC hôm nay** (1L-10L)
- ✅ **Giá bạc Phú Quý hôm nay** (1 lượng)
- ✅ **Giá vàng thế giới (XAU)** - USD/oz
- ✅ **Giá bạc thế giới (XAG)** - USD/oz
- ✅ **Chênh lệch vàng SJC vs thế giới** (quy đổi từ OZ ra lượng)
- ✅ **Chênh lệch bạc Phú Quý vs thế giới** (quy đổi từ OZ ra lượng)
- ✅ **Tỷ giá USD/VND**
- ✅ **Tỷ lệ Gold/Silver**

### Tab 2: 📈 History (Sắp có)
- 🚧 Chart giá vàng SJC 7 ngày qua
- 🚧 Chart giá bạc Phú Quý 7 ngày qua
- 🚧 Chart giá thế giới 7 ngày qua

### Tab 3: 📊 Comparison
- ✅ Bảng so sánh chi tiết
- ✅ Biểu đồ trực quan
- ✅ Tỷ lệ Gold/Silver

## 🚀 Cài đặt

### Bước 1: Cài đặt dependencies

```bash
cd ui
pip install -r requirements.txt
```

### Bước 2: Đảm bảo các modules đã được cài đặt

```bash
# Cài đặt vn_gold_tracker
cd ../vn_gold_tracker
pip install -r requirements.txt

# Cài đặt silver_scraper
cd ../silver_scraper
pip install -r requirements.txt

# Cài đặt international_metals
cd ../international_metals
pip install -e .
```

### Bước 3: Chạy ứng dụng

```bash
cd ui
streamlit run app.py
```

Hoặc với custom port:

```bash
streamlit run app.py --server.port 8501
```

## 📱 Sử dụng

### Giao diện chính

1. **Sidebar**: Cài đặt và thông tin
   - 🔄 Nút làm mới dữ liệu
   - ⚙️ Tự động làm mới
   - 📊 Thông tin cập nhật

2. **Tab Today**: Xem giá hiện tại
   - 4 card giá chính (Vàng SJC, Bạc PQ, Gold World, Silver World)
   - Phần chênh lệch giá VN vs Thế giới
   - Thông tin tỷ giá và quy đổi

3. **Tab History**: Xem lịch sử (coming soon)

4. **Tab Comparison**: So sánh chi tiết

### Tự động làm mới

- Bật "Tự động làm mới" ở sidebar
- Chọn khoảng thời gian (30-300 giây)
- Dữ liệu sẽ tự động reload

## 📊 Quy đổi đơn vị

### Hệ số quy đổi:

```
1 troy ounce (oz) = 31.1035 gram
1 lượng (cây) = 37.5 gram
1 oz = 0.8294 lượng
```

### Tính chênh lệch:

**Vàng:**
```
Giá thế giới (VND/lượng) = Giá thế giới (USD/oz) × USD/VND × 0.8294

Chênh lệch = Giá SJC (VND/lượng) - Giá thế giới (VND/lượng)
```

**Bạc:**
```
Giá thế giới (VND/lượng) = Giá thế giới (USD/oz) × USD/VND × 0.8294

Chênh lệch = Giá bạc PQ (VND/lượng) - Giá thế giới (VND/lượng)
```

## 🎨 Features

### ✅ Hiện tại:
- Real-time price updates
- Beautiful gradient cards
- Automatic data caching (10 minutes)
- Manual refresh button
- Responsive design
- Conversion calculator
- Spread visualization

### 🚧 Sắp có:
- Historical charts (7 days, 30 days)
- Price alerts
- Export to CSV/Excel
- Dark mode
- Mobile app

## 🔧 Troubleshooting

### Lỗi import modules

```
ImportError: No module named 'vn_gold_tracker'
```

**Giải pháp:**
```bash
# Cài đặt các modules từ thư mục cha
cd ../vn_gold_tracker
pip install -r requirements.txt

cd ../silver_scraper
pip install -r requirements.txt

cd ../international_metals
pip install -e .
```

### Lỗi Yahoo Finance rate limit

Nếu gặp lỗi `429 Too Many Requests`:

**Giải pháp 1:** Chờ 15-30 phút

**Giải pháp 2:** Dùng VPN đổi IP

**Giải pháp 3:** Tăng cache duration trong `data_fetcher.py`:
```python
self.intl_fetcher = PreciousMetalsPrice(cache_duration=1800)  # 30 phút
```

### Lỗi database connection

Nếu `vn_gold_tracker` cần database:

**Giải pháp:** Dùng SQLite thay vì PostgreSQL (default)

```python
# Trong vn_gold_tracker/gold_data_pg.py
# Đổi connection string sang SQLite
```

## 📁 Cấu trúc

```
ui/
├── app.py                 # Streamlit application
├── data_fetcher.py        # Data fetching & calculation
├── requirements.txt       # Dependencies
├── README.md             # This file
└── .streamlit/           # Streamlit config (optional)
    └── config.toml
```

## 🎯 Tương lai

### Phase 2 (Soon):
- [ ] Historical data charts
- [ ] Price alerts (telegram/email)
- [ ] Export to Excel/CSV
- [ ] Dark mode theme

### Phase 3 (Later):
- [ ] User authentication
- [ ] Custom watchlists
- [ ] Portfolio tracking
- [ ] Mobile app (React Native)
- [ ] Backend API (FastAPI)

## 📞 Support

Nếu gặp vấn đề:

1. Kiểm tra các modules cha có hoạt động không
2. Kiểm tra internet connection
3. Xem logs ở terminal
4. Tạo issue trên GitHub

## 📝 Notes

- Dữ liệu chỉ mang tính tham khảo
- Vui lòng xác nhận với nguồn chính thức
- Auto-refresh mỗi 10 phút (default)
- Cache duration: 600 seconds

## 🌐 Nguồn dữ liệu

- 🇻🇳 **Vàng SJC**: vnstock API / phuquygroup.vn
- 🥈 **Bạc Phú Quý**: giabac.phuquygroup.vn
- 🌎 **Thế giới**: Yahoo Finance (XAU, XAG)
- 💵 **USD/VND**: vnstock API

---

**Made with ❤️ for tracking precious metals prices**

**Version**: 1.0.0
**Status**: ✅ Production Ready (Tab 1)
**Last Updated**: 2026-01-03
