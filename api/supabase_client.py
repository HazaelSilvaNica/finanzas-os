import os
from supabase import create_client, Client

# Singleton para el cliente de Supabase
_supabase_instance: Client = None

def get_supabase() -> Client:
    """
    Retorna el cliente de Supabase con sanitización estricta.
    Removido load_dotenv() para permitir que Vercel use su propio ambiente.
    """
    global _supabase_instance
    if _supabase_instance is not None:
        return _supabase_instance

    # Leemos y limpiamos espacios en blanco
    raw_url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    raw_key = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or 
        os.environ.get("SUPABASE_SERVICE_KEY") or 
        os.environ.get("SUPABASE_KEY") or 
        os.environ.get("SUPABASE_ANON_KEY")
    )

    url = raw_url.strip() if raw_url else None
    key = raw_key.strip() if raw_key else None

    if not url or not key:
        return None

    try:
        _supabase_instance = create_client(url, key)
        return _supabase_instance
    except:
        return None

# Compatibilidad
supabase = get_supabase()

def init_storage():
    sb = get_supabase()
    if not sb: return
    try:
        buckets = sb.storage.list_buckets()
        if not any(b.name == 'comprobantes' for b in buckets):
            sb.storage.create_bucket('comprobantes', options={'public': True})
    except: pass
