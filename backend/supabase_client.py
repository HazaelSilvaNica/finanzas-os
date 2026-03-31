import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# Initialize client
supabase: Client = create_client(url, key)

def get_supabase():
    return supabase

def init_storage():
    """
    Ensure the 'comprobantes' bucket exists and is public.
    """
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
