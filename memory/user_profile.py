# === memory/user_profile.py (Supabase version) ===
from utils.supabase_client import supabase

DEFAULT_EMAIL = "default_user@example.com"

def load_user_profile(email=DEFAULT_EMAIL):
    response = supabase.table("user_profiles").select("data").eq("email", email).execute()
    if response.data:
        return response.data[0]["data"]
    return {}

def save_profile(profile_data, email=DEFAULT_EMAIL):
    existing = supabase.table("user_profiles").select("id").eq("email", email).execute()
    if existing.data:
        supabase.table("user_profiles").update({"data": profile_data}).eq("email", email).execute()
    else:
        supabase.table("user_profiles").insert({"email": email, "data": profile_data}).execute()

def update_user_profile(updates, merge=True, email=DEFAULT_EMAIL):
    profile = load_user_profile(email)
    if merge:
        profile.update(updates)
    else:
        profile = updates
    save_profile(profile, email)
    return profile

