import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
# Búsqueda robusta de la llave (Service Role Key / Service Key / Supabase Key)
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")

# Initialize client with safety check
if not url or not key:
    print(f"❌ CRITICAL: Missing Supabase Credentials. URL: {url}, KEY found: {'Yes' if key else 'No'}")
    supabase = None
else:
    try:
        print(f"Connecting to Supabase at: {url}")
        from supabase import create_client, Client
        supabase: Client = create_client(url, key)
    except Exception as e:
        print(f"❌ Error al inicializar cliente Supabase: {e}")
        supabase = None

def get_supabase():
    return supabase

def init_storage():
    """
    Ensure the 'comprobantes' bucket exists and is public.
    """
    if not supabase:
        print("⚠️ Skipped init_storage: Supabase client not initialized.")
        return
    try:
        # Check if already exists
        buckets = supabase.storage.list_buckets()
        if not any(b.name == 'comprobantes' for b in buckets):
            supabase.storage.create_bucket('comprobantes', options={'public': True})
            print("✅ Supabase Bucket 'comprobantes' created.")
        else:
            print("ℹ️ Supabase Bucket 'comprobantes' already exists.")
    except Exception as e:
        print(f"⚠️ Error initializing storage: {e}")

if __name__ == "__main__":
    init_storage()
