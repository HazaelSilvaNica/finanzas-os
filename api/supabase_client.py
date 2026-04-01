import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Singleton para el cliente de Supabase
_supabase_instance: Client = None

def get_supabase() -> Client:
    """
    Retorna el cliente de Supabase con inicialización dinámica (Lazy).
    Esto fuerza a leer las variables de entorno en tiempo de ejecución.
    """
    global _supabase_instance
    if _supabase_instance is not None:
        return _supabase_instance

    load_dotenv()
    url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or 
        os.environ.get("SUPABASE_SERVICE_KEY") or 
        os.environ.get("SUPABASE_KEY") or 
        os.environ.get("SUPABASE_ANON_KEY")
    )

    if not url or not key:
        print(f"❌ SUPABASE OFFLINE: URL {'Presente' if url else 'Faltante'}, KEY {'Presente' if key else 'Faltante'}")
        return None

    try:
        _supabase_instance = create_client(url, key)
        print(f"✅ Supabase Dynamically Connected (v3.7.11) to: {url[:15]}...")
        return _supabase_instance
    except Exception as e:
        print(f"❌ Error al conectar dinámicamente a Supabase: {e}")
        return None

# Mantenemos 'supabase' para compatibilidad, pero DEBE usarse get_supabase() para asegurar frescura
supabase = get_supabase()

def init_storage():
    sb = get_supabase()
    if not sb: return
    try:
        buckets = sb.storage.list_buckets()
        if not any(b.name == 'comprobantes' for b in buckets):
            sb.storage.create_bucket('comprobantes', options={'public': True})
    except: pass
