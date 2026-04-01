import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Inicialización Estricta (Según instrucciones de Hazael)
url = os.getenv("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")

if not url or not key:
    print(f"❌ ERROR: Faltan variables de entorno de Supabase. URL: {url}, Key: {key[:5] if key else 'None'}")
    # Nota: No lanzamos Exception fatal aquí para que el servidor responda 503 en lugar de crash total
    supabase = None
else:
    try:
        supabase: Client = create_client(url, key)
        print("✅ Supabase Client Initialized (v3.7.10)")
    except Exception as e:
        print(f"❌ Error initializing Supabase: {e}")
        supabase = None

# Verificación de IA
google_key = os.getenv("GOOGLE_API_KEY")
if not google_key:
    print("⚠️ Warning: GOOGLE_API_KEY missing. Ian AI might be offline.")

def get_supabase():
    return supabase

def init_storage():
    if not supabase: return
    try:
        buckets = supabase.storage.list_buckets()
        if not any(b.name == 'comprobantes' for b in buckets):
            supabase.storage.create_bucket('comprobantes', options={'public': True})
    except: pass
