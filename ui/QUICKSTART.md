# 🚀 QUICK START - Price Tracker UI

## Bắt đầu nhanh trong 3 bước!

### Step 1: Cài đặt dependencies (5 phút)

```bash
# Vào thư mục UI
cd ui

# Cài đặt
pip install -r requirements.txt

# Cài đặt các modules từ thư mục cha
cd ../vn_gold_tracker && pip install -r requirements.txt
cd ../silver_scraper && pip install -r requirements.txt
cd ../international_metals && pip install -e .
```

### Step 2: Chạy ứng dụng (1 giây)

```bash
cd ui
streamlit run app.py
```

### Step 3: Mở browser

```
http://localhost:8501
```

---

## ✅ Done!

Bạn sẽ thấy:

**Tab Today:**
- 🇻🇳 Giá vàng SJC (VND/lượng)
- 🥈 Giá bạc Phú Quý (VND/lượng)
- 🌎 Giá vàng thế giới (USD/oz)
- 🌎 Giá bạc thế giới (USD/oz)
- 📊 Chênh lệch giá VN vs Thế giới
- 💵 Tỷ giá USD/VND

---

## ⚙️ Tùy chọn

### Thay đổi port:

```bash
streamlit run app.py --server.port 8080
```

### Tự động mở browser:

```bash
streamlit run app.py --server.headless false
```

### Debug mode:

```bash
streamlit run app.py --logger.level debug
```

---

## 📱 Screenshots

### Main Dashboard:
```
┌─────────────────────────────────────────────────────┐
│          🪙 PRICE TRACKER - VÀNG & BẠC              │
├─────────────────────────────────────────────────────┤
│  [📅 Today]  [📈 History]  [📊 Comparison]          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ Vàng SJC │ │ Bạc PQ   │ │ Gold W   │ │Silver W│ │
│  │ 80M VND  │ │ 2.7M VND │ │ $2034    │ │ $24.5  │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘ │
│                                                     │
│  📊 CHÊNH LỆCH GIÁ                                  │
│  ┌─────────────────────┐ ┌─────────────────────┐  │
│  │ Vàng: +5M/lượng     │ │ Bạc: +500k/lượng    │  │
│  └─────────────────────┘ └─────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 🐛 Troubleshooting

### Lỗi: "No module named 'vn_gold_tracker'"

```bash
# Install parent modules
cd ../vn_gold_tracker
pip install -r requirements.txt

cd ../silver_scraper
pip install -r requirements.txt

cd ../international_metals
pip install -e .

# Quay lại UI
cd ../ui
streamlit run app.py
```

### Lỗi: "Yahoo Finance 429"

→ Chỉ là tạm thời! Chờ 15-30 phút hoặc đổi VPN.

### Lỗi: Port đang dùng

```bash
# Dùng port khác
streamlit run app.py --server.port 8502
```

---

## 🎯 Tips

1. **Auto-refresh**: Bật ở sidebar để tự động cập nhật
2. **Cache**: Dữ liệu được cache 10 phút
3. **Manual refresh**: Bấm nút 🔄 để cập nhật ngay
4. **Mobile**: Mở trên điện thoại (localhost:8501)

---

## 📞 Need help?

- Xem `README.md` chi tiết
- Check logs ở terminal
- Test từng module riêng lẻ trước

---

**That's it! Happy tracking! 🪙✨**
