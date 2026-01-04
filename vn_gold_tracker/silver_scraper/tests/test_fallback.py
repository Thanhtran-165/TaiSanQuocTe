#!/usr/bin/env python3
"""
Test script để kiểm tra fallback function
"""

import sys
import os

# Add parent directory to path to import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.silver_scraper import SilverPriceScraper
import json

def test_fallback():
    """Test fallback function bằng cách skip nguồn chính"""
    scraper = SilverPriceScraper()

    print("=" * 80)
    print("🧪 TEST FALLBACK FUNCTION")
    print("=" * 80)
    print()

    # Test trực tiếp fallback
    print("📍 Đang test fallback: topi.vn")
    result = scraper.get_from_fallback_source()

    if result:
        print("\n✅ Fallback THÀNH CÔNG!")
        scraper.print_prices(result)
        scraper.save_to_json(result, 'silver_prices_fallback.json')
        print(f"\n📊 Tổng số dòng giá: {len(result['prices'])}")
    else:
        print("\n❌ Fallback THẤT BẠI!")

    return result

def test_primary():
    """Test nguồn chính"""
    scraper = SilverPriceScraper()

    print("\n" + "=" * 80)
    print("🧪 TEST PRIMARY SOURCE")
    print("=" * 80)
    print()

    print("📍 Đang test primary: giabac.phuquygroup.vn")
    result = scraper.get_from_primary_source()

    if result:
        print("\n✅ Primary THÀNH CÔNG!")
        scraper.print_prices(result)
        print(f"\n📊 Tổng số dòng giá: {len(result['prices'])}")
    else:
        print("\n❌ Primary THẤT BẠI!")

    return result

if __name__ == "__main__":
    # Test cả 2 nguồn
    primary_result = test_primary()
    fallback_result = test_fallback()

    # So sánh kết quả
    print("\n" + "=" * 80)
    print("📊 KẾT QUẢ SO SÁNH")
    print("=" * 80)
    print(f"Primary Source: {'✅ THÀNH CÔNG' if primary_result else '❌ THẤT BẠI'}")
    print(f"Fallback Source: {'✅ THÀNH CÔNG' if fallback_result else '❌ THẤT BẠI'}")
    print()
