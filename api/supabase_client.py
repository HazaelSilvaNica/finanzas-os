import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Búsqueda agresiva de URL (Vercel usa a veces NEXT_PUBLIC_)
url: str = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")

# Búsqueda agresiva de la llave (Service Role > Anon)
key: str = (
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or 
    os.environ.get("SUPABASE_SERVICE_KEY") or 
    os.environ.get("SUPABASE_KEY") or 
    os.environ.get("SUPABASE_ANON_KEY") or 
    os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
)

# Initialize client with safety check
if not url or not key:
    print(f"❌ CRITICAL: Missing Supabase Credentials. URL: {'Found' if url else 'Missing'}, KEY: {'Found' if key else 'Missing'}")
    supabase = None
else:
    try:
        # Diagnostic (Masked)
        masked_url = f"{url[:12]}..." if url else "None"
        masked_key = f"{key[:8]}...{key[-4:]}" if key else "None"
        print(f"Connecting to Supabase at: {masked_url} | Key: {masked_key}")
        
        supabase: Client = create_client(url, key)
        print("✅ Supabase Client Initialized.")
    except Exception as e:
        print(f"❌ Error al inicializar cliente Supabase: {e}")
        supabase = None

def get_supabase():
    return supabase

def init_storage():
    if not supabase: return
    try:
        buckets = supabase.storage.list_buckets()
        if not any(b.name == 'comprobantes' for b in buckets):
            supabase.storage.create_bucket('comprobantes', options={'public': True})
    except: pass

if __name__ == "__main__":
    init_storage()
