import os
import traceback
from supabase import create_client, Client

_supabase_instance: Client = None
_last_error = None

def get_supabase() -> Client:
    global _supabase_instance, _last_error
    if _supabase_instance is not None: return _supabase_instance

    url = (os.environ.get("SUPABASE_URL") or "").strip()
    key = (os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY") or "").strip()

    if not url or not key:
        _last_error = f"Missing vars: URL={bool(url)}, KEY={bool(key)}"
        return None

    try:
        _supabase_instance = create_client(url, key)
        return _supabase_instance
    except Exception as e:
        _last_error = str(e)
        return None

def get_last_error(): return _last_error
