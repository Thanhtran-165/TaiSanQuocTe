# 🔒 Security Checklist

## ⚠️ CRITICAL: Files NOT to Commit

Đây là các file **KHÔNG BAO GIỜ** được push lên git (vì chứa thông tin nhạy cảm):

- ❌ `.secrets/wgc_auth_cookie.txt` - WGC authentication cookie
- ❌ `*.db` - Database files (price history, local data)
- ❌ `.env` - Environment variables với sensitive data
- ❌ `data_wgc/` - Downloaded WGC snapshot (có thể gắn với cookie/session)

## 📦 Generated Data (Khuyến nghị không commit)

Các file này không nhất thiết “nhạy cảm”, nhưng nên để ngoài git để repo gọn và tránh ràng buộc bản quyền/dung lượng:

- ⚠️ `Du_tru/*.csv`, `Du_tru/*.parquet` - dataset dự trữ (có thể regenerate từ WDI)
- ⚠️ `wgc_*.csv`, `*.xlsx`, `*.parquet` - data export/tạm thời

## ✅ Tất cả đã được `.gitignore` bảo vệ

Kiểm tra: `git status` - không nên thấy file nào ở trên

## 🛡️ Setup cho Deployment

### 1. Local Development
```bash
# Copy example file
cp .env.example .env

# Edit .env nếu cần (thường không cần cho local)
```

### 2. Production Deployment
Đặt environment variables trong platform dashboard:
- **Railway**: Settings → Environment Variables
- **Vercel**: Settings → Environment Variables
- **Render**: Environment tab

```bash
# Frontend (Vercel)
NEXT_PUBLIC_API_URL=https://your-backend.railway.app

# Backend (Railway)
WGC_AUTH_COOKIE=your_cookie_here
```

### 3. WGC Auth Cookie (Optional)
Chỉ cần nếu bạn muốn fetch official gold reserves data:

**Cách lấy cookie:**
1. Login vào https://www.gold.org/
2. Open DevTools → Application → Cookies
3. Copy `wgcAuth_cookie` value
4. Save vào `.secrets/wgc_auth_cookie.txt` (LOCAL ONLY)

**⚠️ KHÔNG BAO GIỜ push file này lên git!**

## 🧹 Regenerate Data (nếu cần)

### World Bank Reserves (Du_tru)
```bash
python Du_tru/build_reserves_gold_dataset.py
```

### WGC Snapshot (requires cookie)
```bash
python download_wgc_gold_reserves.py --mode playwright --no-parquet
```

## 🔍 Double-Check Trước Khi Commit

```bash
# Kiểm tra xem có file sensitive nào bị track không
git ls-files | grep -E "\.db$|\.env|\.secrets"

# Nếu có output, xóa khỏi git cache
git rm --cached <file_path>

# Hoặc reset toàn bộ sensitive files
git rm --cached *.db
git rm --cached .env
git rm --cached .secrets/*

# Commit thay đổi
git commit -m "chore: remove sensitive files from git tracking"
```

## 🚀 Best Practices

1. **Sử dụng environment variables** cho production
2. **Không bao giờ hardcode credentials** trong code
3. **Rotate credentials định kỳ** (API keys, cookies)
4. **Sử dụng .env.example** làm template
5. **Review git diff** trước mỗi commit: `git diff --cached`

## 📝 Notes

- Database files sẽ được **auto-create** khi chạy application
- WGC data là **optional**, app vẫn work mà không cần
- Frontend có **fallback logic** nếu backend không connect

Generated with Claude Code
