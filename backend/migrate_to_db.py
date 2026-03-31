import json
import os
from datetime import datetime
from database import SessionLocal, Transaction, init_db

# Files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANUAL_EXPENSES_FILE = os.path.join(BASE_DIR, "data", "expenses_manual.json")

def migrate_json_to_sqlite():
    if not os.path.exists(MANUAL_EXPENSES_FILE):
        print(f"File {MANUAL_EXPENSES_FILE} not found.")
        return

    print("--- 🏗️ Initializing DB Models ---")
    init_db()
    db = SessionLocal()

    print(f"--- 📂 Loading: {MANUAL_EXPENSES_FILE} ---")
    with open(MANUAL_EXPENSES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Manual mapping for older data: treat all as 'EXPENSE' because it was primarily an expense tracker
    transaction_count = 0
    
    for month_key, entries in data.items():
        print(f"Migrating month: {month_key} ({len(entries)} entries)")
        for entry in entries:
            # Parse date
            try:
                date_val = datetime.strptime(entry.get("fecha", "2026-03-31"), "%Y-%m-%d")
            except:
                date_val = datetime.utcnow()

            # Create Transaction
            new_tx = Transaction(
                uuid=entry.get("id"),
                monto=float(entry.get("monto", 0)),
                tipo="EXPENSE", # JSON was primarily for manual expenses
                categoria=entry.get("categoria", "otros"),
                descripcion=entry.get("concepto", ""),
                entidad="BUSINESS" if entry.get("is_business", True) else "PERSONAL",
                fecha=date_val,
                iva_monto=0.0 # Default for legacy data
            )
            db.add(new_tx)
            transaction_count += 1

    try:
        db.commit()
        print(f"--- ✅ Successfully migrated {transaction_count} transactions! ---")
    except Exception as e:
        db.rollback()
        print(f"--- ❌ Migration Failed: {e} ---")
    finally:
        db.close()

if __name__ == "__main__":
    migrate_json_to_sqlite()
