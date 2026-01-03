"""
Example Usage của Precious Metals Price Module
"""

from precious_metals import (
    PreciousMetalsPrice,
    get_gold_price,
    get_silver_price,
    get_all_metals_prices
)
import json


def print_separator():
    print("\n" + "=" * 70)


def example_1_basic_usage():
    """Ví dụ 1: Cách sử dụng cơ bản"""
    print_separator()
    print("VÍ DỤ 1: CÁCH SỬ DỤNG CƠ BẢN")
    print_separator()

    # Lấy giá vàng
    print("\n1. Lấy giá vàng:")
    gold_data = get_gold_price()
    if gold_data:
        print(f"   Giá vàng: ${gold_data['price']}/oz")
        print(f"   Thay đổi: ${gold_data['change']} ({gold_data['change_percent']}%)")
        print(f"   Cao nhất: ${gold_data['high']}")
        print(f"   Thấp nhất: ${gold_data['low']}")
        print(f"   Nguồn: {gold_data['source']}")

    # Lấy giá bạc
    print("\n2. Lấy giá bạc:")
    silver_data = get_silver_price()
    if silver_data:
        print(f"   Giá bạc: ${silver_data['price']}/oz")
        print(f"   Thay đổi: ${silver_data['change']} ({silver_data['change_percent']}%)")
        print(f"   Nguồn: {silver_data['source']}")


def example_2_with_cache():
    """Ví dụ 2: Sử dụng cache"""
    print_separator()
    print("VÍ DỤ 2: SỬ DỤNG CACHE")
    print_separator()

    pm = PreciousMetalsPrice(cache_duration=300)  # Cache 5 phút

    # Lần gọi đầu - fetch từ API
    print("\n1. Lần gọi đầu tiên (fetch từ API):")
    gold_price = pm.get_price('gold', use_cache=True)
    if gold_price:
        print(f"   Giá vàng: ${gold_price['price']}")
        print(f"   Cache hit: No")

    # Lần gọi thứ hai - sử dụng cache
    print("\n2. Lần gọi thứ hai (từ cache):")
    gold_price = pm.get_price('gold', use_cache=True)
    if gold_price:
        print(f"   Giá vàng: ${gold_price['price']}")
        print(f"   Cache hit: Yes")

    print("\n3. Xóa cache và fetch lại:")
    pm.clear_cache()
    gold_price = pm.get_price('gold', use_cache=True)
    if gold_price:
        print(f"   Giá vàng: ${gold_price['price']}")


def example_3_with_fallback():
    """Ví dụ 3: Sử dụng MSM làm fallback"""
    print_separator()
    print("VÍ DỤ 3: SỬ DỤNG FALLBACK")
    print_separator()

    # MSN Money không cần API key
    # MarketSmith API cần subscription (optional)
    msm_api_key = None  # Thay bằng MarketSmith API key nếu có

    pm = PreciousMetalsPrice()

    print("\n1. Tự động thử nguồn chính (Yahoo Finance):")
    print("   - Nếu Yahoo fail → tự động dùng MSN Money")
    print("   - Nếu MSN fail → tự động dùng Yahoo ETF")

    gold_price = pm.get_price('gold', msm_api_key=msm_api_key)
    if gold_price:
        print(f"   ✓ Thành công với nguồn: {gold_price['source']}")
        print(f"   Giá vàng: ${gold_price['price']}")
    else:
        print(f"   ✗ Tất cả các nguồn đều thất bại")


def example_4_get_all():
    """Ví dụ 4: Lấy tất cả giá cùng lúc"""
    print_separator()
    print("VÍ DỤ 4: LẤY TẤT CẢ GIÁ CÙNG LÚC")
    print_separator()

    print("\n1. Lấy giá cả vàng và bạc:")
    all_prices = get_all_metals_prices()

    print("\n   Kết quả:")
    print("-" * 70)

    if all_prices['gold']:
        g = all_prices['gold']
        print(f"   VÀNG: ${g['price']}/oz | Change: ${g['change']} ({g['change_percent']}%) | Source: {g['source']}")
    else:
        print("   VÀNG: Failed to fetch")

    if all_prices['silver']:
        s = all_prices['silver']
        print(f"   BẠC:  ${s['price']}/oz | Change: ${s['change']} ({s['change_percent']}%) | Source: {s['source']}")
    else:
        print("   BẠC:  Failed to fetch")


def example_5_json_format():
    """Ví dụ 5: Export ra JSON format"""
    print_separator()
    print("VÍ DỤ 5: EXPORT RA JSON FORMAT")
    print_separator()

    pm = PreciousMetalsPrice()

    print("\n1. Lấy tất cả giá và format thành JSON:")
    all_prices = pm.get_all_prices()

    # Format lại để dễ đọc
    formatted_data = {
        'timestamp': all_prices['gold']['timestamp'] if all_prices['gold'] else None,
        'metals': {
            'gold': all_prices['gold'],
            'silver': all_prices['silver']
        }
    }

    print("\n   JSON Output:")
    print("-" * 70)
    print(json.dumps(formatted_data, indent=2, ensure_ascii=False))


def example_6_comparison():
    """Ví dụ 6: So sánh giá vàng/bạc và tỷ lệ"""
    print_separator()
    print("VÍ DỤ 6: SO SÁNH VÀ TÍNH TOÁN")
    print_separator()

    pm = PreciousMetalsPrice()
    all_prices = pm.get_all_prices()

    if all_prices['gold'] and all_prices['silver']:
        gold_price = all_prices['gold']['price']
        silver_price = all_prices['silver']['price']

        # Tính tỷ lệ gold/silver
        ratio = gold_price / silver_price

        print(f"\n1. Giá hiện tại:")
        print(f"   Vàng: ${gold_price}/oz")
        print(f"   Bạc: ${silver_price}/oz")

        print(f"\n2. Tỷ lệ Gold/Silver: {ratio:.2f}:1")

        print(f"\n3. Phân tích:")
        if ratio > 70:
            print(f"   - Tỷ lệ cao (> 70): Bạc có thể được định giá thấp")
        elif ratio < 60:
            print(f"   - Tỷ lệ thấp (< 60): Vàng có thể được định giá thấp")
        else:
            print(f"   - Tỷ lệ bình thường (60-70)")

        # Tính giá theo gram
        # 1 oz = 31.1035 gram
        gold_per_gram = gold_price / 31.1035
        silver_per_gram = silver_price / 31.1035

        print(f"\n4. Giá theo gram:")
        print(f"   Vàng: ${gold_per_gram:.2f}/gram")
        print(f"   Bạc: ${silver_per_gram:.2f}/gram")


def example_7_error_handling():
    """Ví dụ 7: Xử lý lỗi"""
    print_separator()
    print("VÍ DỤ 7: XỬ LÝ LỖI")
    print_separator()

    pm = PreciousMetalsPrice()

    # Test với metal type không hợp lệ
    print("\n1. Test với metal type không hợp lệ:")
    result = pm.get_price('platinum')  # Không hỗ trợ
    if result is None:
        print("   ✓ Xử lý lỗi đúng: trả về None")

    # Test khi tất cả các nguồn đều fail
    print("\n2. Test với các metal type hợp lệ:")
    print("   (Module sẽ tự động thử tất cả các nguồn)")

    result = pm.get_price('gold')
    if result:
        print(f"   ✓ Thành công: ${result['price']}")
    else:
        print("   ✗ Tất cả nguồn đều fail")


def main():
    """Chạy tất cả examples"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "     PRECIOUS METALS PRICE TRACKER - EXAMPLES".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")

    # Chạy các examples
    examples = [
        ("Cơ bản", example_1_basic_usage),
        ("Cache", example_2_with_cache),
        ("Fallback", example_3_with_fallback),
        ("Tất cả giá", example_4_get_all),
        ("JSON format", example_5_json_format),
        ("So sánh", example_6_comparison),
        ("Xử lý lỗi", example_7_error_handling),
    ]

    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n❌ Lỗi ở example '{name}': {str(e)}")

    print_separator()
    print("\n✓ Hoàn thành tất cả examples!")
    print("\nGhi chú:")
    print("  - Yahoo Finance: Nguồn chính, không cần API key")
    print("  - MSN Money: Nguồn fallback, không cần API key (web scraping)")
    print("  - Yahoo ETF: Fallback cuối cùng, không cần API key")
    print("  - MarketSmith API: Optional fallback, cần subscription")
    print("\nĐể cài đặt dependencies: pip install -r requirements.txt")
    print_separator()
    print("\n")


if __name__ == "__main__":
    main()
