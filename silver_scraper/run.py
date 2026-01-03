#!/usr/bin/env python3
"""
Main entry point for Silver Price Scraper
Chạy script này để lấy giá bạc hàng ngày
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from silver_scraper import SilverPriceScraper

def main():
    """Main function"""
    scraper = SilverPriceScraper()

    # Lấy giá
    data = scraper.get_silver_prices()

    # In ra console
    scraper.print_prices(data)

    # Lưu vào JSON (output/silver_prices.json)
    scraper.save_to_json(data, 'silver_prices.json')

    # Return data for programmatic use
    return data

if __name__ == "__main__":
    main()
