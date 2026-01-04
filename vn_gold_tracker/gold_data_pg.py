"""
Module PRODUCTION: PostgreSQL Database cho Web App
Hỗ trợ cả SQLite (dev) và PostgreSQL (production)
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("⚠️  psycopg2 không cài đặt. Chỉ hỗ trợ SQLite mode.")
    print("   Cài: pip install psycopg2-binary")

# Import fallback module
try:
    # Support both "run as script" and "import as package"
    try:
        from .gold_fallback import get_sjc_from_phuquy, get_btmc_from_phuquy
    except ImportError:
        from gold_fallback import get_sjc_from_phuquy, get_btmc_from_phuquy
    FALLBACK_AVAILABLE = True
except ImportError:
    FALLBACK_AVAILABLE = False
    print("⚠️  gold_fallback không có. Fallback sẽ không hoạt động.")
    print("   File gold_fallback.py cần nằm cùng thư mục với file này.")


class GoldDataPG:
    """
    Class quản lý dữ liệu giá vàng
    - Hỗ trợ SQLite cho development (mặc định)
    - Hỗ trợ PostgreSQL cho production
    """

    def __init__(
        self,
        db_type: str = "sqlite",  # 'sqlite' or 'postgresql'
        sqlite_path: str = "./gold_data.db",
        postgres_config: Optional[Dict] = None
    ):
        """
        Khởi tạo database

        Args:
            db_type: Loại database ('sqlite' hoặc 'postgresql')
            sqlite_path: Đường dẫn SQLite file (cho sqlite mode)
            postgres_config: Config cho PostgreSQL (cho postgresql mode)
                {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'gold_data',
                    'user': 'postgres',
                    'password': 'password'
                }
        """
        self.db_type = db_type
        self.sqlite_path = sqlite_path
        self.postgres_config = postgres_config or {}

        self.conn = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Kết nối database"""
        if self.db_type == "sqlite":
            self.conn = sqlite3.connect(self.sqlite_path, check_same_thread=False)
            self.conn.execute("PRAGMA foreign_keys = ON")

        elif self.db_type == "postgresql":
            if not POSTGRES_AVAILABLE:
                raise ImportError("psycopg2 không có. Cài đặt: pip install psycopg2-binary")

            self.conn = psycopg2.connect(
                host=self.postgres_config.get('host', 'localhost'),
                port=self.postgres_config.get('port', 5432),
                database=self.postgres_config.get('database', 'gold_data'),
                user=self.postgres_config.get('user', 'postgres'),
                password=self.postgres_config.get('password', 'password')
            )
            self.conn.set_session(autocommit=True)

        else:
            raise ValueError(f"db_type phải là 'sqlite' hoặc 'postgresql', không phải '{self.db_type}'")

    def _create_tables(self):
        """Tạo các bảng trong database"""
        cursor = self.conn.cursor()

        # Bảng giá vàng SJC
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sjc_prices (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                name VARCHAR(255) NOT NULL,
                buy_price DECIMAL(15, 2),
                sell_price DECIMAL(15, 2),
                date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """ if self.db_type == "postgresql" else """
            CREATE TABLE IF NOT EXISTS sjc_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                name TEXT NOT NULL,
                buy_price REAL,
                sell_price REAL,
                date DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Bảng giá vàng BTMC
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS btmc_prices (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                name VARCHAR(255) NOT NULL,
                karat VARCHAR(50),
                gold_content VARCHAR(50),
                buy_price DECIMAL(15, 2),
                sell_price DECIMAL(15, 2),
                world_price DECIMAL(15, 2),
                source_time VARCHAR(50),
                date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """ if self.db_type == "postgresql" else """
            CREATE TABLE IF NOT EXISTS btmc_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                name TEXT NOT NULL,
                karat TEXT,
                gold_content TEXT,
                buy_price REAL,
                sell_price REAL,
                world_price REAL,
                source_time TEXT,
                date DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Bảng tỷ giá
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exchange_rates (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                currency_code VARCHAR(10) NOT NULL,
                currency_name VARCHAR(100),
                buy_cash DECIMAL(15, 2),
                buy_transfer DECIMAL(15, 2),
                sell DECIMAL(15, 2),
                date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(currency_code, date)
            )
        """ if self.db_type == "postgresql" else """
            CREATE TABLE IF NOT EXISTS exchange_rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                currency_code TEXT NOT NULL,
                currency_name TEXT,
                buy_cash REAL,
                buy_transfer REAL,
                sell REAL,
                date DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(currency_code, date)
            )
        """)

        # Index cho performance
        self._create_indexes()

        self.conn.commit()

    def _create_indexes(self):
        """Tạo index để tối ưu query"""
        cursor = self.conn.cursor()

        # Index cho SQLite
        if self.db_type == "sqlite":
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sjc_date ON sjc_prices(date DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_btmc_date ON btmc_prices(date DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_exchange_date ON exchange_rates(date DESC)")

        # Index cho PostgreSQL
        else:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sjc_date ON sjc_prices(date DESC NULLS LAST)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_btmc_date ON btmc_prices(date DESC NULLS LAST)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_exchange_date ON exchange_rates(date DESC NULLS LAST)")

    # ==================== DATA COLLECTION METHODS ====================

    def get_sjc_gold_price(self, save_to_db: bool = True, use_fallback: bool = True) -> pd.DataFrame:
        """
        Lấy giá vàng SJC hiện tại

        Args:
            save_to_db: Lưu vào database
            use_fallback: Dùng phuquygroup.vn khi vnstock thất bại

        Returns:
            pd.DataFrame: Giá vàng SJC
        """
        # 1. Thử lấy từ vnstock trước (PRIMARY)
        try:
            from vnstock.explorer.misc.gold_price import sjc_gold_price
            df = sjc_gold_price()

            if not df.empty:
                if save_to_db:
                    self._save_sjc_to_db(df)
                print(f"✓ [vnstock] Đã lấy giá vàng SJC ({len(df)} loại) - {datetime.now().strftime('%H:%M:%S')}")
                return df

        except ImportError:
            print("⚠️  vnstock không có. Cài: pip install vnstock")
        except Exception as e:
            print(f"⚠️  vnstock thất bại: {e}")

        # 2. Fallback sang phuquygroup.vn
        if use_fallback and FALLBACK_AVAILABLE:
            print("🔄 Đang thử fallback từ phuquygroup.vn...")
            try:
                df = get_sjc_from_phuquy()

                if not df.empty:
                    if save_to_db:
                        self._save_sjc_to_db(df)
                    print(f"✓ [fallback] Đã lấy giá vàng SJC từ phuquygroup.vn ({len(df)} loại) - {datetime.now().strftime('%H:%M:%S')}")
                    return df
                else:
                    print("❌ Fallback thất bại: Không có dữ liệu")

            except Exception as e:
                print(f"❌ Fallback lỗi: {e}")

        # 3. Thất bại hoàn toàn
        print("❌ Không thể lấy giá vàng SJC từ cả 2 nguồn")
        return pd.DataFrame()

    def _save_sjc_to_db(self, df: pd.DataFrame):
        """Lưu giá SJC vào DB"""
        cursor = self.conn.cursor()
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now()

        for _, row in df.iterrows():
            buy_price = self._parse_price(row['buy_price'])
            sell_price = self._parse_price(row['sell_price'])

            if self.db_type == "postgresql":
                cursor.execute("""
                    INSERT INTO sjc_prices
                    (name, buy_price, sell_price, date, timestamp)
                    VALUES (%s, %s, %s, %s, %s)
                """, (row['name'], buy_price, sell_price, current_date, current_time))
            else:
                cursor.execute("""
                    INSERT INTO sjc_prices
                    (name, buy_price, sell_price, date, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (row['name'], buy_price, sell_price, current_date, current_time))

        self.conn.commit()
        print(f"  → Đã lưu {len(df)} bản ghi vào DB")

    def get_btmc_gold_price(self, save_to_db: bool = True, use_fallback: bool = True) -> pd.DataFrame:
        """
        Lấy giá vàng BTMC hiện tại

        Args:
            save_to_db: Lưu vào database
            use_fallback: Dùng phuquygroup.vn khi vnstock thất bại

        Returns:
            pd.DataFrame: Giá vàng BTMC
        """
        # 1. Thử lấy từ vnstock trước (PRIMARY)
        try:
            from vnstock.explorer.misc.gold_price import btmc_goldprice
            df = btmc_goldprice()

            if not df.empty:
                if save_to_db:
                    self._save_btmc_to_db(df)
                print(f"✓ [vnstock] Đã lấy giá vàng BTMC ({len(df)} loại) - {datetime.now().strftime('%H:%M:%S')}")
                return df

        except ImportError:
            print("⚠️  vnstock không có. Cài: pip install vnstock")
        except Exception as e:
            print(f"⚠️  vnstock thất bại: {e}")

        # 2. Fallback sang phuquygroup.vn
        if use_fallback and FALLBACK_AVAILABLE:
            print("🔄 Đang thử fallback từ phuquygroup.vn...")
            try:
                df = get_btmc_from_phuquy()

                if not df.empty:
                    if save_to_db:
                        self._save_btmc_to_db(df)
                    print(f"✓ [fallback] Đã lấy giá vàng BTMC từ phuquygroup.vn ({len(df)} loại) - {datetime.now().strftime('%H:%M:%S')}")
                    return df
                else:
                    print("❌ Fallback thất bại: Không có dữ liệu")

            except Exception as e:
                print(f"❌ Fallback lỗi: {e}")

        # 3. Thất bại hoàn toàn
        print("❌ Không thể lấy giá vàng BTMC từ cả 2 nguồn")
        return pd.DataFrame()

    def _save_btmc_to_db(self, df: pd.DataFrame):
        """Lưu giá BTMC vào DB"""
        cursor = self.conn.cursor()
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now()

        for _, row in df.iterrows():
            buy_price = self._parse_price(row['buy_price'])
            sell_price = self._parse_price(row['sell_price'])
            world_price = self._parse_price(row.get('world_price', 0))

            if self.db_type == "postgresql":
                cursor.execute("""
                    INSERT INTO btmc_prices
                    (name, karat, gold_content, buy_price, sell_price, world_price,
                     source_time, date, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    row['name'], row.get('karat', ''), row.get('gold_content', ''),
                    buy_price, sell_price, world_price, row.get('time', ''),
                    current_date, current_time
                ))
            else:
                cursor.execute("""
                    INSERT INTO btmc_prices
                    (name, karat, gold_content, buy_price, sell_price, world_price,
                     source_time, date, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['name'], row.get('karat', ''), row.get('gold_content', ''),
                    buy_price, sell_price, world_price, row.get('time', ''),
                    current_date, current_time
                ))

        self.conn.commit()
        print(f"  → Đã lưu {len(df)} bản ghi vào DB")

    def get_usd_vnd_rate(self, date: Optional[str] = None, save_to_db: bool = True) -> pd.DataFrame:
        """Lấy tỷ giá USD/VND"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        try:
            from vnstock.explorer.misc.exchange_rate import vcb_exchange_rate
            df = vcb_exchange_rate(date=date)

            if save_to_db and not df.empty:
                self._save_exchange_rate_to_db(df, date)

            print(f"✓ Đã lấy tỷ giá cho ngày {date}")
            return df

        except ImportError:
            print("⚠ vnstock không có. Cài: pip install vnstock")
            return pd.DataFrame()
        except Exception as e:
            print(f"✗ Lỗi: {e}")
            return pd.DataFrame()

    def _save_exchange_rate_to_db(self, df: pd.DataFrame, date: str):
        """Lưu tỷ giá vào DB"""
        cursor = self.conn.cursor()
        current_time = datetime.now()

        for _, row in df.iterrows():
            buy_cash = self._parse_price(row.get('buy _cash', 0))
            buy_transfer = self._parse_price(row.get('buy _transfer', 0))
            sell = self._parse_price(row.get('sell', 0))

            if self.db_type == "postgresql":
                cursor.execute("""
                    INSERT INTO exchange_rates
                    (currency_code, currency_name, buy_cash, buy_transfer, sell, date, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (currency_code, date) DO UPDATE SET
                        buy_cash = EXCLUDED.buy_cash,
                        buy_transfer = EXCLUDED.buy_transfer,
                        sell = EXCLUDED.sell,
                        timestamp = EXCLUDED.timestamp
                """, (
                    row['currency_code'], row.get('currency_name', ''),
                    buy_cash, buy_transfer, sell, date, current_time
                ))
            else:
                cursor.execute("""
                    INSERT OR REPLACE INTO exchange_rates
                    (currency_code, currency_name, buy_cash, buy_transfer, sell, date, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['currency_code'], row.get('currency_name', ''),
                    buy_cash, buy_transfer, sell, date, current_time
                ))

        self.conn.commit()
        print(f"  → Đã lưu {len(df)} tỷ giá vào DB")

    # ==================== QUERY METHODS ====================

    def get_sjc_history(self, days_back: int = 30) -> pd.DataFrame:
        """Lấy lịch sử giá vàng SJC"""
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        if self.db_type == "postgresql":
            query = """
                SELECT * FROM sjc_prices
                WHERE date >= %s
                ORDER BY timestamp DESC
            """
            df = pd.read_sql_query(query, self.conn, params=(cutoff_date,))
        else:
            query = """
                SELECT * FROM sjc_prices
                WHERE date >= ?
                ORDER BY timestamp DESC
            """
            df = pd.read_sql_query(query, self.conn, params=(cutoff_date,))

        return df

    def get_btmc_history(self, days_back: int = 30) -> pd.DataFrame:
        """Lấy lịch sử giá vàng BTMC"""
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        if self.db_type == "postgresql":
            query = """
                SELECT * FROM btmc_prices
                WHERE date >= %s
                ORDER BY timestamp DESC
            """
            df = pd.read_sql_query(query, self.conn, params=(cutoff_date,))
        else:
            query = """
                SELECT * FROM btmc_prices
                WHERE date >= ?
                ORDER BY timestamp DESC
            """
            df = pd.read_sql_query(query, self.conn, params=(cutoff_date,))

        return df

    def get_exchange_rate_history(self, days_back: int = 30) -> pd.DataFrame:
        """Lấy lịch sử tỷ giá"""
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        if self.db_type == "postgresql":
            query = """
                SELECT * FROM exchange_rates
                WHERE date >= %s
                ORDER BY timestamp DESC
            """
            df = pd.read_sql_query(query, self.conn, params=(cutoff_date,))
        else:
            query = """
                SELECT * FROM exchange_rates
                WHERE date >= ?
                ORDER BY timestamp DESC
            """
            df = pd.read_sql_query(query, self.conn, params=(cutoff_date,))

        return df

    # ==================== STATISTICS ====================

    def get_statistics(self) -> Dict:
        """Lấy thống kê database"""
        cursor = self.conn.cursor()
        stats = {}

        # SJC
        cursor.execute("SELECT COUNT(*) FROM sjc_prices")
        stats['sjc_total_records'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT date) FROM sjc_prices")
        stats['sjc_total_days'] = cursor.fetchone()[0]

        cursor.execute("SELECT MAX(date) FROM sjc_prices")
        result = cursor.fetchone()
        stats['sjc_latest_date'] = result[0] if result and result[0] else None

        # BTMC
        cursor.execute("SELECT COUNT(*) FROM btmc_prices")
        stats['btmc_total_records'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT date) FROM btmc_prices")
        stats['btmc_total_days'] = cursor.fetchone()[0]

        cursor.execute("SELECT MAX(date) FROM btmc_prices")
        result = cursor.fetchone()
        stats['btmc_latest_date'] = result[0] if result and result[0] else None

        # Exchange rate
        cursor.execute("SELECT COUNT(*) FROM exchange_rates")
        stats['exchange_total_records'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT date) FROM exchange_rates")
        stats['exchange_total_days'] = cursor.fetchone()[0]

        cursor.execute("SELECT MAX(date) FROM exchange_rates")
        result = cursor.fetchone()
        stats['exchange_latest_date'] = result[0] if result and result[0] else None

        return stats

    # ==================== UTILITY METHODS ====================

    def _parse_price(self, price_str) -> Optional[float]:
        """Chuyển string giá thành float"""
        if pd.isna(price_str) or price_str == '-' or price_str == '':
            return None

        if isinstance(price_str, (int, float)):
            return float(price_str)

        price_str = str(price_str).replace(',', '').replace('.', '').replace(' ', '')

        try:
            return float(price_str)
        except:
            return None

    def export_to_excel(self, output_file: str = "gold_data_report.xlsx"):
        """Xuất dữ liệu ra Excel"""
        print(f"📊 Đang xuất dữ liệu ra {output_file}...")

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            sjc_current = self.get_sjc_gold_price(save_to_db=False)
            if not sjc_current.empty:
                sjc_current.to_excel(writer, sheet_name='SJC_HienTai', index=False)

            btmc_current = self.get_btmc_gold_price(save_to_db=False)
            if not btmc_current.empty:
                btmc_current.to_excel(writer, sheet_name='BTMC_HienTai', index=False)

            rate_current = self.get_usd_vnd_rate(save_to_db=False)
            if not rate_current.empty:
                rate_current.to_excel(writer, sheet_name='TyGia_HienTai', index=False)

            sjc_history = self.get_sjc_history(days_back=365)
            if not sjc_history.empty:
                sjc_history.to_excel(writer, sheet_name='SJC_LichSu', index=False)

            btmc_history = self.get_btmc_history(days_back=365)
            if not btmc_history.empty:
                btmc_history.to_excel(writer, sheet_name='BTMC_LichSu', index=False)

            rate_history = self.get_exchange_rate_history(days_back=365)
            if not rate_history.empty:
                rate_history.to_excel(writer, sheet_name='TyGia_LichSu', index=False)

        print(f"✅ Đã xuất dữ liệu thành công!")

    def close(self):
        """Đóng kết nối database"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ==================== CONVENIENCE FUNCTIONS ====================

def get_sqlite_db():
    """Lấy SQLite DB (cho development)"""
    return GoldDataPG(db_type="sqlite", sqlite_path="./gold_data.db")


def get_postgresql_db(
    host="localhost",
    port=5432,
    database="gold_data",
    user="postgres",
    password: Optional[str] = None,
):
    """Lấy PostgreSQL DB (cho production)"""
    if password is None:
        password = os.environ.get("PGPASSWORD") or os.environ.get("POSTGRES_PASSWORD")
    if not password:
        raise ValueError("Missing PostgreSQL password. Pass `password=` or set env PGPASSWORD/POSTGRES_PASSWORD.")
    config = {
        'host': host,
        'port': port,
        'database': database,
        'user': user,
        'password': password
    }
    return GoldDataPG(db_type="postgresql", postgres_config=config)


if __name__ == "__main__":
    print("="*70)
    print("🥇 GOLD DATA PG - SQLITE & POSTGRESQL SUPPORT")
    print("="*70)

    # Test với SQLite
    print("\n1️⃣  TESTING SQLITE MODE:")
    db = get_sqlite_db()

    print("\n📊 Thu thập dữ liệu...")
    db.get_sjc_gold_price()
    db.get_btmc_gold_price()
    db.get_usd_vnd_rate()

    print("\n📈 Thống kê:")
    stats = db.get_statistics()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    db.close()
    print("\n✅ SQLite mode OK!")

    # Test với PostgreSQL (nếu có)
    if POSTGRES_AVAILABLE:
        print("\n2️⃣  TESTING POSTGRESQL MODE:")
        print("→ Cần config PostgreSQL connection")
        print("→ Uncomment để test")
        # db = get_postgresql_db(
        #     host="localhost",
        #     database="gold_data",
        #     user="postgres",
        #     password="your_password"
        # )
        # ... test code ...
    else:
        print("\n2️⃣  POSTGRESQL MODE:")
        print("→ Chưa cài đặt psycopg2-binary")
        print("→ Cài: pip install psycopg2-binary")

    print("\n" + "="*70)
