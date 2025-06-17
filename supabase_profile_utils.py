# === supabase_profile_utils.py (Fixed & Compatible) ===
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# === Load Credentials ===
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# === User Profile: Fetch or Create ===
def fetch_or_create_user_profile(email: str) -> dict:
    try:
        response = supabase.table("user_profiles").select("*").eq("email", email).execute()
        if response.data:
            return response.data[0]

        default_profile = {
            "email": email,
            "desired_effects": [],
            "preferred_aromas": [],
            "tolerance": "unknown",
            "past_strains": [],
            "reinforcement_scores": {},
            "created_at": datetime.utcnow().isoformat()
        }
        supabase.table("user_profiles").insert(default_profile).execute()
        return default_profile

    except Exception as e:
        print(f"❌ Supabase profile error: {e}")
        return {
            "email": email,
            "desired_effects": [],
            "preferred_aromas": [],
            "tolerance": "unknown",
            "past_strains": [],
            "reinforcement_scores": {},
        }

# === User Profile: Update ===
def update_user_profile_supabase(email: str, profile: dict):
    try:
        supabase.table("user_profiles").update(profile).eq("email", email).execute()
    except Exception as e:
        print(f"❌ Failed to update profile in Supabase: {e}")
