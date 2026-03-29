import os
from supabase import create_client, Client

# This will look for your keys in the environment variables (which we will set up in Render later)
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Error: Supabase URL or Key not found in environment variables.")

supabase: Client = create_client(url, key)
