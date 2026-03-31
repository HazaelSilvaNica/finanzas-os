import sqlite3
import os
from datetime import datetime
from supabase_client import supabase, init_storage

# Path to SQLite
SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'finanzas_os.db')

def migrate():
    # 1. Initialize Storage
    init_storage()

    # 2. Connect to SQLite
    if not os.path.exists(SQLITE_PATH):
        print(f"❌ SQLite database not found at {SQLITE_PATH}")
        return

    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    
    # Get all transactions
    try:
        cursor.execute("SELECT uuid, monto, tipo, categoria, descripcion, entidad, fecha, file_url, iva_monto FROM transactions")
        rows = cursor.fetchall()
    except Exception as e:
        print(f"❌ Error reading SQLite: {e}")
        return

    print(f"📝 Found {len(rows)} transactions to migrate.")

    # 3. Insert into Supabase
    success_count = 0
    error_count = 0

    for row in rows:
        tx_data = {
            "id": row[0], # Using the original UUID as ID in Supabase
            "monto": row[1],
            "tipo": row[2],
            "categoria": row[3],
            "descripcion": row[4],
            "entidad": row[5],
            "fecha": row[6],
            "evidence_url": row[7],
            "iva_monto": row[8]
        }
        
        try:
            # Use 'upsert' to avoid duplicates
            res = supabase.table('transactions').upsert(tx_data).execute()
            success_count += 1
            if success_count % 10 == 0:
                print(f"✅ Progress: {success_count} records migrated.")
        except Exception as e:
            error_count += 1
            print(f"⚠️ Error migrating record {row[0]}: {e}")

    print("\n--- Migration Summary ---")
    print(f"🚀 Success: {success_count}")
    print(f"❌ Errors: {error_count}")
    print("--------------------------")

    conn.close()

if __name__ == "__main__":
    migrate()
