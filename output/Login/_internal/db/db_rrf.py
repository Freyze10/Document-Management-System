import os
import sys
import traceback
import dbfread
from PyQt6.QtCore import QObject, pyqtSignal, QCoreApplication
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from datetime import datetime

# --- CONFIGURATION ---
DB_CONFIG = {
    "host": "192.168.1.13",
    "port": 5432,
    "dbname": "db_msds",
    "user": "postgres",
    "password": "mbpi"
}
DBF_BASE_PATH = r'\\system-server\SYSTEM-NEW-OLD'

# --- RRF PATHS ---
RRF_DBF_PATH = os.path.join(DBF_BASE_PATH, 'RRF')
RRF_PRIMARY_DBF_PATH = os.path.join(RRF_DBF_PATH, 'tbl_del01.dbf')  # Assuming similar naming convention as Delivery
RRF_ITEMS_DBF_PATH = os.path.join(RRF_DBF_PATH, 'tbl_del02.dbf')  # Assuming similar naming convention as Delivery

# --- DATABASE ENGINE SETUP ---
db_url = (
    f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
)
try:
    engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=3600)
except Exception as e:
    print(f"FATAL: Could not create database engine. Error: {e}")
    sys.exit(1)  # Use sys.exit(1) for fatal errors in main script


def create_rrf_legacy_tables():
    """Creates the necessary PostgreSQL tables for storing the legacy RRF data."""
    try:
        with engine.connect() as connection:
            with connection.begin():
                # Primary table for RRF headers
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS rrf_primary (
                        id SERIAL PRIMARY KEY,
                        rrf_no TEXT NOT NULL UNIQUE,
                        rrf_date DATE,
                        customer_name TEXT,
                        material_type TEXT,
                        prepared_by TEXT,
                        is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                        encoded_by TEXT,
                        encoded_on TIMESTAMP,
                        edited_by TEXT,
                        edited_on TIMESTAMP
                    );
                """))

                # Items table for RRF details.
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS rrf_items (
                        id SERIAL PRIMARY KEY,
                        rrf_no TEXT NOT NULL,
                        quantity NUMERIC(15, 6),
                        unit TEXT,
                        product_code TEXT,
                        lot_number TEXT,
                        reference_number TEXT,
                        remarks TEXT,
                        FOREIGN KEY (rrf_no) REFERENCES rrf_primary (rrf_no) ON DELETE CASCADE
                    );
                """))
        print("RRF legacy tables checked/created successfully.")
    except Exception as e:
        print(f"FATAL: Could not initialize RRF database tables: {e}")
        raise


class SyncRRFWorker(QObject):
    """
    A worker class that runs in a separate thread to sync data from legacy
    RRF (Return/Request Form) DBF files into the PostgreSQL database.
    It reads the primary RRF data and its associated items, then upserts
    them into the `rrf_primary` and `rrf_items` tables using an incremental
    sync strategy based on the maximum rrf_no.
    """
    finished = pyqtSignal(bool, str)

    def _get_safe_rrf_num(self, rrf_num_raw):
        """
        Safely converts a raw RRF number (which might be float, int, or string)
        into a clean string representation. Handles None and conversion errors.
        Returns None if not convertible to a clean integer string.
        """
        if rrf_num_raw is None:
            return None
        try:
            # First attempt to convert to float (handles scientific notation, decimals)
            # then to int (truncates), then to string
            return str(int(float(rrf_num_raw)))
        except (ValueError, TypeError):
            # Fallback for strings that are not directly numeric but might contain numbers
            s_rrf_num = str(rrf_num_raw).strip()
            if s_rrf_num.isdigit():  # Check if it's purely digits
                return s_rrf_num
            return None  # Not a valid RRF number for comparison

    def _to_float(self, value, default=0.0):
        """
        Safely converts a value to a float, returning a default on failure.
        Handles None, empty strings, and values with extra whitespace.
        """
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            try:
                cleaned_value = str(value).strip()
                return float(cleaned_value) if cleaned_value else default
            except (ValueError, TypeError):
                return default

    def run(self):
        """
        The main execution method for the worker. Reads DBF files, processes
        records, and performs database operations. Emits `finished` signal
        upon completion or error.
        """
        print("\n--- Starting Legacy RRF Sync (Incremental) ---")
        try:
            # --- Step 0: Get the maximum RRF_NO already synced ---
            with engine.connect() as conn:
                # Get the maximum numeric RRF_NO from rrf_primary
                # using a regex check to ensure only valid numbers are cast
                max_synced_rrf_no = conn.execute(text("""
                    SELECT COALESCE(MAX(CAST(rrf_no AS INTEGER)), 0)
                    FROM rrf_primary
                    WHERE rrf_no ~ '^[0-9]+$';
                """)).scalar()
            print(f"Max synced RRF_NO in PostgreSQL: {max_synced_rrf_no}")

            # 1. Process Primary RRF Records (tbl_del01.dbf)
            primary_recs = []
            print(f"Step 1: Reading RRF headers from '{os.path.basename(RRF_PRIMARY_DBF_PATH)}'")
            with dbfread.DBF(RRF_PRIMARY_DBF_PATH, load=True, encoding='latin1') as dbf_primary:
                for r in dbf_primary.records:
                    rrf_num_raw = r.get('T_DRNUM')  # Assuming T_DRNUM is the RRF number field
                    rrf_num = self._get_safe_rrf_num(rrf_num_raw)

                    # Skip if rrf_num is invalid or not purely numeric
                    if not rrf_num or not rrf_num.isdigit():
                        continue

                    # Convert to integer for comparison
                    rrf_num_int = int(rrf_num)

                    # Only sync records with RRF_NO > max_synced_rrf_no
                    if rrf_num_int <= max_synced_rrf_no:
                        continue

                    primary_recs.append({
                        "rrf_no": rrf_num,
                        "rrf_date": r.get('T_DRDATE'),  # Assuming T_DRDATE is the RRF date field
                        "customer_name": str(r.get('T_CUSTOMER', '')).strip(),  # Assuming T_CUSTOMER
                        "material_type": str(r.get('T_DELTO', '')).strip(),  # Re-using T_DELTO for material_type
                        "prepared_by": str(r.get('T_USERID', '')).strip(),  # Assuming T_USERID
                        "is_deleted": bool(r.get('T_DELETED', False))  # Assuming T_DELETED
                    })
            print(f"-> Found {len(primary_recs)} new primary RRF records to sync.")

            if not primary_recs:
                self.finished.emit(True,
                                   f"Sync Info: No new RRF records (RRF_NO > {max_synced_rrf_no}) found to sync.");
                return

            # 2. Process Item Records (tbl_del02.dbf) for *new* RRF numbers
            new_rrf_numbers = {rec['rrf_no'] for rec in primary_recs}
            items_by_rrf = {}
            item_count = 0
            print(f"Step 2: Reading RRF items from '{os.path.basename(RRF_ITEMS_DBF_PATH)}'")
            with dbfread.DBF(RRF_ITEMS_DBF_PATH, load=True, encoding='latin1') as dbf_items:
                for item_rec in dbf_items.records:
                    rrf_num = self._get_safe_rrf_num(item_rec.get('T_DRNUM'))  # Assuming T_DRNUM for item linkage
                    if rrf_num in new_rrf_numbers:  # Only pick items for the newly identified RRF_NOs
                        item_count += 1
                        if rrf_num not in items_by_rrf:
                            items_by_rrf[rrf_num] = []

                        # Combine multiple description fields into a single 'remarks' field
                        # Adjusted to match `attachments` logic in Delivery for flexibility
                        remarks = "\n".join(
                            filter(None, [str(item_rec.get(f'T_DESC{i}', '')).strip() for i in
                                          range(1, 5)]))  # Using 1-4 for DESC fields

                        items_by_rrf[rrf_num].append({
                            "rrf_no": rrf_num,
                            "quantity": self._to_float(item_rec.get('T_TOTALWT')),  # Assuming T_TOTALWT
                            "unit": str(item_rec.get('T_TOTALWTU', '')).strip(),  # Assuming T_TOTALWTU
                            "product_code": str(item_rec.get('T_PRODCODE', '')).strip(),  # Assuming T_PRODCODE
                            "lot_number": str(item_rec.get('T_LOTNUM', '')).strip(),
                            # Using T_LOTNUM directly for lot_number
                            "reference_number": str(item_rec.get('T_REFNUM', '')).strip(),
                            # Placeholder for a ref num, might need adjustment
                            "remarks": remarks
                        })
            print(f"-> Found {item_count} new item records for the new RRFs.")

            # 3. Perform Database Operations
            print("Step 3: Writing new data to PostgreSQL...")
            with engine.connect() as conn:
                with conn.begin():  # Start a transaction

                    # Upsert primary RRF records
                    # ON CONFLICT will ensure new records are inserted and existing ones (if any match) are updated.
                    # Given our filtering by max_synced_rrf_no, primarily inserts will occur here.
                    conn.execute(text("""
                        INSERT INTO rrf_primary (rrf_no, rrf_date, customer_name, material_type, prepared_by, is_deleted, encoded_by, encoded_on, edited_by, edited_on)
                        VALUES (:rrf_no, :rrf_date, :customer_name, :material_type, :prepared_by, :is_deleted, 'DBF_SYNC', NOW(), 'DBF_SYNC', NOW())
                        ON CONFLICT (rrf_no) DO UPDATE SET
                            rrf_date = EXCLUDED.rrf_date,
                            customer_name = EXCLUDED.customer_name,
                            material_type = EXCLUDED.material_type,
                            prepared_by = EXCLUDED.prepared_by,
                            is_deleted = EXCLUDED.is_deleted,
                            edited_by = 'DBF_SYNC',
                            edited_on = NOW()
                    """), primary_recs)

                    # Gather all items to be inserted (only for new RRF_NOs)
                    all_items_to_insert = [item for rrf_num in new_rrf_numbers for item in
                                           items_by_rrf.get(rrf_num, [])]

                    # Insert all new items in a single operation
                    if all_items_to_insert:
                        # For items, we simply insert, assuming that for a new RRF_NO, all its items are new.
                        # If an RRF_NO could exist but have *new* items, this logic would need further refinement
                        # (e.g., check for item existence based on product_code/lot_number or delete-then-insert per RRF_NO).
                        # For now, we follow the SyncDeliveryWorker pattern for items, which is to only add items for new headers.
                        conn.execute(text("""
                            INSERT INTO rrf_items (rrf_no, quantity, unit, product_code, lot_number, reference_number, remarks)
                            VALUES (:rrf_no, :quantity, :unit, :product_code, :lot_number, :reference_number, :remarks)
                        """), all_items_to_insert)

            print("-> Database transaction committed successfully.")
            msg = (f"RRF sync complete.\n"
                   f"{len(primary_recs)} new primary records and "
                   f"{item_count} new items processed.")
            self.finished.emit(True, msg)

        except dbfread.DBFNotFound as e:
            self.finished.emit(False, f"File Not Found: A required RRF DBF file is missing.\nDetails: {e}")
        except Exception as e:
            trace_info = traceback.format_exc()
            print(f"RRF SYNC CRITICAL ERROR: {e}\n{trace_info}")
            self.finished.emit(False,
                               f"An unexpected error occurred during RRF sync:\n{e}\n\nCheck console/logs for technical details.")


# --- Example Usage (similar to SyncDeliveryWorker's __main__ block) ---
def handle_rrf_sync_finish(success, message):
    print("\n--- RRF Sync Process Finished ---")
    print("Status:", "SUCCESS" if success else "FAILED")
    print("Message:", message)
    if QCoreApplication.instance():
        QCoreApplication.instance().quit()


if __name__ == "__main__":
    app = QCoreApplication(sys.argv)
    print("--- Running RRF Table Setup ---")
    create_rrf_legacy_tables()

    worker = SyncRRFWorker()
    worker.finished.connect(handle_rrf_sync_finish)
    # For direct execution without QThread, just call run()
    worker.run()

    sys.exit(app.exec())  # Use app.exec() to keep the event loop running if using QThread