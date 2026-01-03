"""
Cấu hình cho Precious Metals Price Module
Copy file này thành config.py và điền thông tin của bạn
"""

# MSM (MarketSmith) Configuration - OPTIONAL
# MSN Money không cần API key (mặc định)
# MarketSmith API cần subscription (optional)
MSM_API_KEY = ""  # Thay bằng MarketSmith API key nếu có subscription, hoặc để trống

# Cache Configuration
CACHE_DURATION = 300  # Thời gian cache tính bằng giây (mặc định: 300 = 5 phút)

# Retry Configuration
MAX_RETRIES = 3  # Số lần thử lại khi thất bại
RETRY_DELAY = 2  # Độ trễ giữa các lần thử (giây)

# Logging Configuration
LOG_LEVEL = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Default Metals to Track
DEFAULT_METALS = ['gold', 'silver']

# Currency (chỉ hỗ trợ USD hiện tại)
DEFAULT_CURRENCY = 'USD'

# Unit (chỉ hỗ trợ oz - troy ounce hiện tại)
DEFAULT_UNIT = 'oz'
