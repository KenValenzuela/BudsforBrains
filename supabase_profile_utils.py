# === supabase_profile_utils.py (Fully Fixed & Compatible with Supabase JSON) ===

import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# === Load Credentials ===
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# === Fetch or Create a Supabase-Stored User Profile ===
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
            "notes": "",
            "past_strains": [],
            "logged_effects": [],
            "reinforcement": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        supabase.table("user_profiles").insert(default_profile).execute()
        return default_profile

    except Exception as e:
        print(f"❌ Supabase profile fetch/create error: {e}")
        return {
            "email": email,
            "desired_effects": [],
            "preferred_aromas": [],
            "tolerance": "unknown",
            "notes": "",
            "past_strains": [],
            "logged_effects": [],
            "reinforcement": {},
        }

# === Update Profile and Ensure JSON-Safe Format ===
def update_user_profile_supabase(email: str, profile: dict):
    try:
        # Clean & sanitize fields
        profile["updated_at"] = datetime.utcnow().isoformat()

        for key in ["past_strains", "desired_effects", "preferred_aromas", "logged_effects"]:
            profile[key] = list(set(profile.get(key, [])))  # Ensure list type

        profile["reinforcement"] = dict(profile.get("reinforcement", {}))  # Ensure dict type

        supabase.table("user_profiles").update(profile).eq("email", email).execute()

    except Exception as e:
        print(f"❌ Failed to update profile in Supabase: {e}")
