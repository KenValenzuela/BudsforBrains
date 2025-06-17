# === memory/journal.py (Supabase version) ===
from utils.supabase_client import supabase
from datetime import datetime
from .user_profile import load_user_profile, update_user_profile

DEFAULT_EMAIL = "default_user@example.com"

def get_user_id(email):
    resp = supabase.table("user_profiles").select("id").eq("email", email).execute()
    return resp.data[0]["id"] if resp.data else None

def log_entry(entry, email=DEFAULT_EMAIL):
    entry.setdefault("timestamp", datetime.utcnow().isoformat())
    supabase.table("journals").insert({
        "entry": entry,
        "user_id": get_user_id(email)
    }).execute()

    profile = load_user_profile(email)
    strain = entry.get("strain")
    profile.setdefault("past_strains", [])
    if strain and strain not in profile["past_strains"]:
        profile["past_strains"].append(strain)

    for effect in entry.get("effects_felt", []):
        profile.setdefault("logged_effects", [])
        if effect and effect not in profile["logged_effects"]:
            profile["logged_effects"].append(effect)

    update_user_profile(profile, email=email)

def get_reinforcement_boost(strain, profile):
    return float(profile.get("reinforcement", {}).get(strain, 0.0))

def adjust_reinforcement_score(profile, strain, feedback):
    profile.setdefault("reinforcement", {})
    delta = 1.0 if feedback == "positive" else -1.0
    current = profile["reinforcement"].get(strain, 0.0)
    profile["reinforcement"][strain] = round(current + delta, 2)
    update_user_profile(profile)
