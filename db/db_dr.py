import os
import sys
import traceback
import dbfread
from sqlalchemy import create_engine, text
from PyQt6.QtCore import QObject, pyqtSignal, QCoreApplication

# --- CONFIGURATION ---
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "postgres",
    "user": "postgres",
    "password": "password"
}
DBF_BASE_PATH = r'\\system-server\SYSTEM-NEW-OLD'
DELIVERY_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_del01.dbf')
DELIVERY_ITEMS_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_del02.dbf')

# --- DATABASE ENGINE SETUP ---
db_url = (
    f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
)
try:
    engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=3600)
except Exception as e:
    print(f"FATAL: Could not create database engine. Error: {e}")
    exit(1)


def create_delivery_legacy_tables():
    """Creates the necessary PostgreSQL tables for storing the legacy delivery data."""
    try:
        with engine.connect() as connection:
            with connection.begin():
                # Primary table for delivery headers
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS product_delivery_primary (
                        id SERIAL PRIMARY KEY,
                        dr_no TEXT NOT NULL UNIQUE,
                        delivery_date DATE,
                        customer_name TEXT,
                        po_no TEXT
                    );
                """))

                # Items table for delivery details.
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS product_delivery_items (
                        id SERIAL PRIMARY KEY,
                        dr_no TEXT NOT NULL,
                        product_code TEXT,
                        product_color TEXT,
                        lot_numbers TEXT,
                        attachments TEXT,
                        FOREIGN KEY (dr_no) REFERENCES product_delivery_primary (dr_no) ON DELETE CASCADE
                    );
                """))

    except Exception as e:
        print(f"FATAL: Could not initialize delivery database tables: {e}")
        raise


class SyncDeliveryWorker(QObject):
    """Syncs delivery data from legacy DBF files to PostgreSQL (incremental sync)."""
    finished = pyqtSignal(bool, str)

    def _get_safe_dr_num(self, dr_num_raw):
        """
        Safely converts raw DR_NUM to string, handling None and non-numeric inputs.
        Returns None if not convertible to a clean integer string.
        """
        if dr_num_raw is None:
            return None
        try:
            # First attempt to convert to float (handles scientific notation, decimals)
            # then to int (truncates), then to string
            return str(int(float(dr_num_raw)))
        except (ValueError, TypeError):
            # Fallback for strings that are not directly numeric but might contain numbers
            s_dr_num = str(dr_num_raw).strip()
            if s_dr_num.isdigit():  # Check if it's purely digits
                return s_dr_num
            return None  # Not a valid DR_NUM

    def _to_float(self, value, default=0.0):
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            try:
                # Attempt to strip and convert if it's a string
                return float(str(value).strip()) if str(value).strip() else default
            except (ValueError, TypeError):
                return default

    def run(self):
        """Main execution method for the sync process (incremental)."""
        print("\n--- Starting Legacy Delivery Sync ---")
        try:
            # --- Step 0: Get the maximum DR_NO already synced ---
            with engine.connect() as conn:
                # Get the maximum numeric DR_NO from product_delivery_primary
                # using a regex check to ensure only valid numbers are cast
                max_synced_dr_no = conn.execute(text("""
                    SELECT COALESCE(MAX(CAST(dr_no AS INTEGER)), 0)
                    FROM product_delivery_primary
                    WHERE dr_no ~ '^[0-9]+$';
                """)).scalar()
            print(f"Max synced DR_NO in PostgreSQL: {max_synced_dr_no}")

            # --- Step 1: Process Primary Delivery Headers (tbl_del01.dbf) ---
            primary_recs = []
            print(f"Step 1: Reading headers from '{os.path.basename(DELIVERY_DBF_PATH)}'")

            with dbfread.DBF(DELIVERY_DBF_PATH, load=True, encoding='latin1') as dbf_primary:
                for r in dbf_primary:
                    dr_num_raw = r.get('T_DRNUM')
                    dr_num = self._get_safe_dr_num(dr_num_raw)

                    # Skip if DR_NUM is invalid or not purely numeric
                    if not dr_num or not dr_num.isdigit():
                        continue

                    # Convert to integer for comparison
                    dr_num_int = int(dr_num)

                    # ✅ Only sync records with DR_NO > max_synced_dr_no
                    if dr_num_int <= max_synced_dr_no:
                        continue

                    address = (str(r.get('T_ADD1', '')).strip() + ' ' +
                               str(r.get('T_ADD2', '')).strip()).strip()

                    primary_recs.append({
                        "dr_no": dr_num,
                        "delivery_date": r.get('T_DRDATE'),
                        "customer_name": str(r.get('T_CUSTOMER', '')).strip(),
                        "po_no": str(r.get('T_CPONUM', '')).strip()
                    })

            print(f"-> Found {len(primary_recs)} new primary records to sync.")

            if not primary_recs:
                self.finished.emit(True, f"Sync Info: No new delivery records (DR_NO > {max_synced_dr_no}) found.")
                return

            # --- Step 2: Process Delivery Items (tbl_del02.dbf) ---
            new_dr_numbers = {rec['dr_no'] for rec in primary_recs}
            items_by_dr = {}
            item_count = 0
            print(f"Step 2: Reading items from '{os.path.basename(DELIVERY_ITEMS_DBF_PATH)}'")

            with dbfread.DBF(DELIVERY_ITEMS_DBF_PATH, load=True, encoding='latin1') as dbf_items:
                for item_rec in dbf_items:
                    dr_num = self._get_safe_dr_num(item_rec.get('T_DRNUM'))
                    if dr_num in new_dr_numbers:  # Only pick items for the newly identified DR_NOs
                        item_count += 1
                        attachments = "\n".join(
                            filter(None, [str(item_rec.get(f'T_DESC{i}', '')).strip() for i in range(1, 5)]))

                        if dr_num not in items_by_dr:
                            items_by_dr[dr_num] = []
                        items_by_dr[dr_num].append({
                            "dr_no": dr_num,
                            "product_code": str(item_rec.get('T_PRODCODE', '')).strip(),
                            "product_color": str(item_rec.get('T_PRODCOLO', '')).strip(),
                            "lot_numbers": "",
                            "attachments": attachments
                        })

            print(f"-> Found {item_count} new item records for the new deliveries.")

            # --- Step 3: Insert New Records ---
            print("Step 3: Writing new data to PostgreSQL...")
            with engine.connect() as conn:
                with conn.begin():
                    # Insert/Update headers
                    # Keep ON CONFLICT for robustness, even though we filter by MAX(DR_NO),
                    # it handles any edge cases or non-sequential DR_NOs
                    conn.execute(text("""
                        INSERT INTO product_delivery_primary (
                            dr_no, delivery_date, customer_name, po_no
                        ) VALUES (
                            :dr_no, :delivery_date, :customer_name, :po_no
                        ) ON CONFLICT (dr_no) DO UPDATE SET
                            delivery_date = EXCLUDED.delivery_date,
                            customer_name = EXCLUDED.customer_name,
                            po_no = EXCLUDED.po_no
                    """), primary_recs)

                    # Insert items
                    all_items_to_insert = [
                        item for dr_num in new_dr_numbers for item in items_by_dr.get(dr_num, [])
                    ]
                    if all_items_to_insert:
                        conn.execute(text("""
                            INSERT INTO product_delivery_items (
                                dr_no, product_code, product_color,
                                lot_numbers, attachments
                            ) VALUES (
                                :dr_no, :product_code, :product_color,
                                :lot_numbers, :attachments
                            )
                        """), all_items_to_insert)

            print("-> Database transaction committed successfully.")
            msg = (f"Delivery sync complete.\n"
                   f"{len(primary_recs)} new primary records and "
                   f"{item_count} new items processed.")
            self.finished.emit(True, msg)

        except dbfread.DBFNotFound as e:
            self.finished.emit(False, f"File Not Found: Missing DBF file.\nDetails: {e}")
        except Exception as e:
            trace_info = traceback.format_exc()
            print(f"DELIVERY SYNC ERROR: {e}\n{trace_info}")
            self.finished.emit(False, f"Unexpected error:\n{e}\n\nCheck logs for details.")


def handle_sync_finish(success, message):
    print("\n--- Sync Process Finished ---")
    print("Status:", "SUCCESS" if success else "FAILED")
    print("Message:", message)
    if QCoreApplication.instance():
        QCoreApplication.instance().quit()


if __name__ == "__main__":
    app = QCoreApplication(sys.argv)
    print("--- Running Delivery Table Setup ---")
    create_delivery_legacy_tables()
    worker = SyncDeliveryWorker()
    worker.finished.connect(handle_sync_finish)
    worker.run()
    sys.exit()