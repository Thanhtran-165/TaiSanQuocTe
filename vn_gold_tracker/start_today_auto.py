"""
🚀 START TODAY AUTO - BẮN ĐẦU THU THẬP TỰ ĐỘNG (KHÔNG CẦN CONFIRM)
"""

from datetime import datetime
from gold_data_pg import get_sqlite_db


def main():
    print("\n" + "="*80)
    print("🥇 GOLD DATA COLLECTOR - BẮT ĐẦU THU THẬP TỰ ĐỘNG")
    print("="*80)
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*80)

    db = get_sqlite_db()

    print("\n📊 ĐANG THU THẬP DỮ LIỆU...\n")

    # SJC
    print("🥇 1. Giá vàng SJC...")
    sjc = db.get_sjc_gold_price(save_to_db=True)

    # BTMC
    print("\n🥈 2. Giá vàng BTMC...")
    btmc = db.get_btmc_gold_price(save_to_db=True)

    # Exchange rate
    print("\n💵 3. Tỷ giá USD/VND...")
    rate = db.get_usd_vnd_rate(save_to_db=True)

    # Stats
    print("\n📊 THỐNG KÊ:")
    stats = db.get_statistics()
    for k, v in stats.items():
        print(f"   {k}: {v}")

    # Export
    print("\n📊 ĐANG XUẤT BÁO CÁO...")
    filename = f"bao_cao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    db.export_to_excel(filename)

    db.close()

    print("\n✅ HOÀN TẤT!")
    print(f"📁 Database: ./gold_data.db")
    print(f"📁 Report: {filename}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
