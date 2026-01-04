# WGC Auto-Refresh Scheduler

Mục tiêu: tự động cập nhật `data_wgc/wgc_gold_reserves_latest.csv` định kỳ để UI tab **Dự trữ → WGC (latest)** luôn có dữ liệu mới.

## Chuẩn bị (1 lần)

1) Tạo venv và cài dependencies
- macOS:
  - `python3 -m venv .venv_wgc`
  - `./.venv_wgc/bin/python -m pip install -U pip requests pandas openpyxl playwright`
  - `./.venv_wgc/bin/python -m playwright install chromium`
- Windows (PowerShell):
  - `python -m venv .venv_wgc`
  - `.\.venv_wgc\Scripts\python -m pip install -U pip requests pandas openpyxl playwright`
  - `.\.venv_wgc\Scripts\python -m playwright install chromium`

2) Lấy cookie đăng nhập WGC (1 lần, interactive)
- macOS:
  - `./.venv_wgc/bin/python scripts/wgc_bootstrap_cookie.py --timeout 600`
- Windows:
  - `.\.venv_wgc\Scripts\python scripts\wgc_bootstrap_cookie.py --timeout 600`

Cookie sẽ được lưu ở `./.secrets/wgc_auth_cookie.txt` (đã được `.gitignore`).

3) Test refresh thủ công
- macOS:
  - `./.venv_wgc/bin/python scripts/wgc_refresh.py --python ./.venv_wgc/bin/python --outdir data_wgc`
- Windows:
  - `.\.venv_wgc\Scripts\python scripts\wgc_refresh.py --python .\.venv_wgc\Scripts\python.exe --outdir data_wgc`

## macOS (LaunchAgent)

Cài lịch chạy hằng ngày (mặc định 08:10):
- `bash scripts/install_wgc_refresh_macos.sh`

Đổi giờ chạy:
- `bash scripts/install_wgc_refresh_macos.sh --time 07:30`

Gỡ:
- `bash scripts/install_wgc_refresh_macos.sh --uninstall`

Logs:
- `~/Library/Logs/wordasset-wgc-refresh.out.log`
- `~/Library/Logs/wordasset-wgc-refresh.err.log`

## Windows (Task Scheduler)

Cài lịch chạy hằng ngày (mặc định 08:10):
- `powershell -ExecutionPolicy Bypass -File scripts\\install_wgc_refresh_windows.ps1`

Đổi giờ chạy:
- `powershell -ExecutionPolicy Bypass -File scripts\\install_wgc_refresh_windows.ps1 -Time \"07:30\"`

Gỡ:
- `powershell -ExecutionPolicy Bypass -File scripts\\install_wgc_refresh_windows.ps1 -Uninstall`

Logs:
- `./.secrets/wgc_refresh_windows.out.log`
- `./.secrets/wgc_refresh_windows.err.log`

## Lưu ý
- Nếu WGC thay đổi cơ chế auth và cookie hết hạn: chạy lại `scripts/wgc_bootstrap_cookie.py`.
- Backend đã tự reload dataset nếu file `data_wgc/wgc_gold_reserves_latest.csv` được cập nhật (dựa trên mtime).

