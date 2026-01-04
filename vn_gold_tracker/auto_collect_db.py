"""
Script TỰ ĐỘNG thu thập dữ liệu giá vàng hàng ngày
Dùng để chạy tự động (cron job / scheduler / task scheduler)
Dữ liệu được lưu vào SQLite Database
"""

import schedule
import time
from datetime import datetime
from gold_data_db import GoldDataDB
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_collect.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def collect_data_job():
    """Job thu thập dữ liệu chính"""
    logger.info("="*70)
    logger.info("🔄 BẮT ĐẦU THU THẬP DỮ LIỆU...")
    logger.info(f"⏰ Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        db = GoldDataDB()

        # 1. Lấy giá vàng SJC
        logger.info("\n🥇 1. Đang lấy giá vàng SJC...")
        sjc = db.get_sjc_gold_price(save_to_db=True)
        if not sjc.empty:
            logger.info(f"✓ Đã lấy và lưu {len(sjc)} bản ghi SJC vào DB")
        else:
            logger.warning("✗ Không lấy được dữ liệu SJC")

        time.sleep(3)

        # 2. Lấy giá vàng BTMC
        logger.info("\n🥈 2. Đang lấy giá vàng BTMC...")
        btmc = db.get_btmc_gold_price(save_to_db=True)
        if not btmc.empty:
            logger.info(f"✓ Đã lấy và lưu {len(btmc)} bản ghi BTMC vào DB")
        else:
            logger.warning("✗ Không lấy được dữ liệu BTMC")

        time.sleep(3)

        # 3. Lấy tỷ giá USD/VND
        logger.info("\n💵 3. Đang lấy tỷ giá USD/VND...")
        rate = db.get_usd_vnd_rate(save_to_db=True)
        if not rate.empty:
            usd = rate[rate['currency_code'] == 'USD']
            if not usd.empty:
                logger.info(f"✓ USD/VND: Mua {usd.iloc[0]['buy _cash']} / Bán {usd.iloc[0]['sell']}")
            logger.info(f"✓ Đã lưu {len(rate)} tỷ giá vào DB")
        else:
            logger.warning("✗ Không lấy được dữ liệu tỷ giá")

        # 4. Hiển thị thống kê
        logger.info("\n📊 THỐNG KÊ DATABASE:")
        stats = db.get_statistics()
        logger.info(f"  - SJC: {stats['sjc_total_records']} bản ghi, {stats['sjc_total_days']} ngày")
        logger.info(f"  - BTMC: {stats['btmc_total_records']} bản ghi, {stats['btmc_total_days']} ngày")
        logger.info(f"  - Tỷ giá: {stats['exchange_total_records']} bản ghi, {stats['exchange_total_days']} ngày")

        # 5. Xuất báo cáo hàng ngày (lúc 23:00)
        hour = datetime.now().hour
        if hour == 23:
            logger.info("\n📊 Đang xuất báo cáo cuối ngày...")
            db.export_to_excel(f"bao_cao_{datetime.now().strftime('%Y%m%d')}.xlsx")
            logger.info("✓ Đã xuất báo cáo cuối ngày")

        db.close()

        logger.info("\n✅ HOÀN TẤT THU THẬP DỮ LIỆU!")

    except Exception as e:
        logger.error(f"❌ Lỗi trong quá trình thu thập: {e}", exc_info=True)


def show_statistics():
    """Hiển thị thống kê database chi tiết"""
    try:
        db = GoldDataDB()
        stats = db.get_statistics()

        logger.info("\n" + "="*70)
        logger.info("📊 THỐNG KÊ DATABASE CHI TIẾT")
        logger.info("="*70)

        logger.info(f"\n🥇 VÀNG SJC:")
        logger.info(f"   └─ Tổng bản ghi: {stats['sjc_total_records']}")
        logger.info(f"   └─ Số ngày có dữ liệu: {stats['sjc_total_days']}")
        logger.info(f"   └─ Ngày mới nhất: {stats['sjc_latest_date']}")

        logger.info(f"\n🥈 VÀNG BTMC:")
        logger.info(f"   └─ Tổng bản ghi: {stats['btmc_total_records']}")
        logger.info(f"   └─ Số ngày có dữ liệu: {stats['btmc_total_days']}")
        logger.info(f"   └─ Ngày mới nhất: {stats['btmc_latest_date']}")

        logger.info(f"\n💵 TỶ GIÁ:")
        logger.info(f"   └─ Tổng bản ghi: {stats['exchange_total_records']}")
        logger.info(f"   └─ Số ngày có dữ liệu: {stats['exchange_total_days']}")
        logger.info(f"   └─ Ngày mới nhất: {stats['exchange_latest_date']}")

        # Hiển thị một số dữ liệu mẫu
        logger.info(f"\n📋 DỮ LIỆU GẦN NHẤT:")

        sjc_latest = db.get_sjc_history(days_back=1)
        if not sjc_latest.empty:
            logger.info(f"\n   SJC ({len(sjc_latest)} bản ghi trong 24h qua)")
            vang_miang = sjc_latest[sjc_latest['name'].str.contains('1L, 10L', case=False, na=False)]
            if not vang_miang.empty:
                latest = vang_miang.iloc[0]
                logger.info(f"   └─ Vàng miếng 1L-10L: Mua {latest['buy_price']:,} / Bán {latest['sell_price']:,}")

        btmc_latest = db.get_btmc_history(days_back=1)
        if not btmc_latest.empty:
            logger.info(f"\n   BTMC ({len(btmc_latest)} bản ghi trong 24h qua)")
            vang_sjc = btmc_latest[btmc_latest['name'].str.contains('VÀNG MIẾNG SJC', case=False, na=False)]
            if not vang_sjc.empty:
                latest = vang_sjc.iloc[0]
                logger.info(f"   └─ Vàng miếng SJC: Mua {latest['buy_price']:,} / Bán {latest['sell_price']:,}")

        rate_latest = db.get_exchange_rate_history(days_back=1)
        if not rate_latest.empty:
            logger.info(f"\n   Tỷ giá ({len(rate_latest)} bản ghi trong 24h qua)")
            usd = rate_latest[rate_latest['currency_code'] == 'USD'].iloc[0]
            logger.info(f"   └─ USD/VND: Mua {usd['buy_cash']:,} / Bán {usd['sell']:,}")

        db.close()

    except Exception as e:
        logger.error(f"❌ Lỗi khi thống kê: {e}", exc_info=True)


def export_report(output_file: str = None):
    """Xuất báo cáo Excel"""
    try:
        logger.info("\n📊 ĐANG XUẤT BÁO CÁO...")

        db = GoldDataDB()

        if output_file is None:
            output_file = f"bao_cao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        db.export_to_excel(output_file)
        db.close()

        logger.info(f"✓ Đã xuất báo cáo: {output_file}")

    except Exception as e:
        logger.error(f"❌ Lỗi khi xuất báo cáo: {e}", exc_info=True)


def run_once():
    """Chạy thu thập 1 lần rồi thoát"""
    logger.info("🚀 CHẠY THU THẬP DỮ LIỆU (1 LẦN)")
    collect_data_job()
    show_statistics()
    logger.info("\n✅ HOÀN TẤT!")


def run_continuous(interval_minutes: int = 30):
    """
    Chạy liên tục mỗi interval_minutes

    Args:
        interval_minutes: Khoảng thời gian giữa các lần (mặc định: 30 phút)
    """
    logger.info(f"🔄 BẮT ĐẦU CHẾ ĐỘ TỰ ĐỘNG...")
    logger.info(f"⏰ Khoảng thời gian: {interval_minutes} phút")
    logger.info("⌨️  Nhấn Ctrl+C để dừng")

    # Schedule job
    schedule.every(interval_minutes).minutes.do(collect_data_job)

    # Chạy ngay lần đầu
    collect_data_job()

    # Vòng lặp chính
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n⏹️  Đã dừng bởi người dùng")
        show_statistics()


def run_at_specific_times(times=['08:00', '12:00', '18:00', '23:00']):
    """
    Chạy vào các giờ cố định trong ngày

    Args:
        times: List các giờ muốn chạy (format: 'HH:MM')
    """
    logger.info(f"🔄 BẮT ĐẦU CHẾ ĐỘ TỰ ĐỘNG (GIỜ CỐ ĐỊNH)...")
    logger.info(f"⏰ Thời gian chạy: {', '.join(times)}")
    logger.info("⌨️  Nhấn Ctrl+C để dừng")

    # Schedule jobs
    for time_str in times:
        schedule.every().day.at(time_str).do(collect_data_job)

    # Show next run time
    next_run = schedule.next_run()
    if next_run:
        logger.info(f"📅 Lần chạy tiếp theo: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

    # Vòng lặp chính
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n⏹️  Đã dừng bởi người dùng")
        show_statistics()


def print_help():
    """In hướng dẫn sử dụng"""
    print("\n" + "="*70)
    print("🤖 AUTO COLLECT DB - SCRIPT THU THẬP TỰ ĐỘNG VỚI DATABASE")
    print("="*70)

    print("\n📖 CÁCH SỬ DỤNG:")
    print("="*70)

    print("\n1️⃣  Chạy 1 lần rồi thoát:")
    print("   python auto_collect_db.py once")
    print("   → Thu thập xong sẽ tự động thoát")

    print("\n2️⃣  Chạy liên tục mỗi X phút:")
    print("   python auto_collect_db.py continuous 30")
    print("   → Số 30 là số phút, có thể thay đổi")
    print("   → Chạy 24/7, nhấn Ctrl+C để dừng")

    print("\n3️⃣  Chạy theo lịch cố định:")
    print("   python auto_collect_db.py schedule")
    print("   → Mặc định: 8h, 12h, 18h, 23h hàng ngày")
    print("   → Có thể chỉnh trong code")

    print("\n4️⃣  Xem thống kê database:")
    print("   python auto_collect_db.py stats")
    print("   → Xem tổng số bản ghi, ngày gần nhất...")

    print("\n5️⃣  Xuất báo cáo Excel:")
    print("   python auto_collect_db.py export")
    print("   → Xuất tất cả dữ liệu ra file Excel")

    print("\n" + "="*70)
    print("\n💡 GỢI Ý SỬ DỤNG:")
    print("="*70)

    print("\n✅ BẮT ĐẦU NGAY:")
    print("   1. Chạy lần đầu: python auto_collect_db.py once")
    print("   2. Kiểm tra DB: python auto_collect_db.py stats")
    print("   3. Setup tự động (xem bên dưới)")

    print("\n🔧 SETUP TỰ ĐỘNG (Linux/Mac - Cron Job):")
    print("   # Mở crontab:")
    print("   crontab -e")
    print("\n   # Thêm dòng sau (chạy mỗi 30 phút):")
    print("   */30 * * * * cd /path/to/project && /usr/bin/python3 auto_collect_db.py once >> auto_cron.log 2>&1")

    print("\n🪟 SETUP TỰ ĐỘNG (Windows - Task Scheduler):")
    print("   1. Mở Task Scheduler")
    print("   2. Create Basic Task")
    print("   3. Trigger: Daily")
    print("   4. Action: Start a program")
    print("   5. Program: python")
    print("   6. Arguments: auto_collect_db.py once")
    print("   7. Start in: /path/to/project")

    print("\n📁 FILES SẼ ĐƯỢC TẠO:")
    print("   - gold_data.db (SQLite Database)")
    print("   - auto_collect.log (Log file)")
    print("   - bao_cao_YYYYMMDD.xlsx (Báo cáo hàng ngày)")

    print("\n📊 DATABASE INFO:")
    print("   - Type: SQLite")
    print("   - Location: ./gold_data.db")
    print("   - Tables: sjc_prices, btmc_prices, exchange_rates")
    print("   - Auto-index: Đã index theo date để query nhanh")

    print("\n" + "="*70)
    print()


if __name__ == "__main__":
    import sys

    print("\n" + "="*70)
    print("🤖 AUTO COLLECT DB - THU THẬP DỮ LIỆU VÀNG TỰ ĐỘNG")
    print("="*70)

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "once":
            run_once()

        elif command == "continuous":
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            run_continuous(interval)

        elif command == "schedule":
            run_at_specific_times()

        elif command == "stats":
            show_statistics()

        elif command == "export":
            output_file = sys.argv[2] if len(sys.argv) > 2 else None
            export_report(output_file)

        else:
            print("❌ Lệnh không recognized!")
            print_help()
    else:
        print_help()
