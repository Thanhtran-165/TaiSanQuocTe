#!/usr/bin/env python3
"""
Main entry point for Gold SJC Scraper
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gold_scraper import GoldDataPG

def main():
    """Main function"""
    print("=" * 60)
    print("🥇 GOLD SJC DATA COLLECTOR")
    print("=" * 60)
    
    # Đường dẫn database
    db_path = os.path.join(os.path.dirname(__file__), 'output', 'gold_data.db')
    
    # Khởi tạo database
    db = GoldDataPG(db_type="sqlite", sqlite_path=db_path)
    
    print(f"✅ Database connected: {db.db_type}")
    print(f"📁 Database: {db_path}")
    print()
    print("📌 Available methods:")
    print("   - db.insert_sjc_price(...)")
    print("   - db.get_latest_prices()")
    print("   - db.get_price_range(start, end)")
    print()
    
    return db

if __name__ == "__main__":
    db = main()
