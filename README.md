# Price Tracker (Vàng & Bạc) – Next.js + FastAPI

Dashboard theo dõi giá **Vàng/Bạc** (VN + quốc tế), có **lịch sử day-by-day**, **portfolio**, và **dự trữ vàng**.

## ✨ Tính năng

- `Today`: giá hiện tại + chênh lệch VN vs World
- `History`: biểu đồ day-by-day theo từng tài sản
- `Comparison`: Gold/Silver ratio + lịch sử
- `Portfolio`: nhập số lượng → theo dõi tổng giá trị + tỷ trọng (stacked chart)
- `Dự trữ`: top 20 và xem theo quốc gia (WDI history), snapshot WGC (optional)

## 🧱 Cấu trúc repo

- `price-tracker-backend/` – FastAPI API (`/api/*`)
- `price-tracker-frontend/` – Next.js UI
- `ui/` – data fetcher + SQLite history
- `vn_gold_tracker/` – vàng VN + USD/VND
- `silver_scraper/` – bạc Phú Quý
- `international_metals/` – giá quốc tế
- `Du_tru/` – scripts build dataset dự trữ (WDI)

## 🚀 Quickstart (Local)

### macOS / Linux

Backend:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r price-tracker-backend/requirements.txt
python -m uvicorn main:app --app-dir price-tracker-backend --reload --port 8000
```

Frontend:
```bash
npm -C price-tracker-frontend install
npm -C price-tracker-frontend run dev
```

Mở: `http://localhost:3000`

### Windows (PowerShell)

Backend:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r price-tracker-backend\requirements.txt
python -m uvicorn main:app --app-dir price-tracker-backend --reload --port 8000
```

Frontend:
```powershell
npm -C price-tracker-frontend install
npm -C price-tracker-frontend run dev
```

## 🏦 Dự trữ (WDI dataset)

Dataset dự trữ (WDI) **không commit** trong repo (để repo gọn). Generate:
```bash
python Du_tru/build_reserves_gold_dataset.py
```

## 🥇 WGC snapshot (optional)

WGC download có thể cần login + cookie.
- Xem `scripts/README_WGC_SCHEDULER.md` (macOS/Windows scheduler)
- Xem `SECURITY.md` trước khi public/push

## 🔒 Security

Xem `SECURITY.md`.

## 🖥️ Auto-start khi mở máy (Local)

### macOS (launchd)
```bash
bash scripts/install_autostart_macos.sh
```
Sau đó reboot / đăng xuất-đăng nhập, mở: `http://localhost:3000`

Gỡ:
```bash
bash scripts/uninstall_autostart_macos.sh
```

### Windows (Task Scheduler)
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install_autostart_windows.ps1
```
Gỡ:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\uninstall_autostart_windows.ps1
```
