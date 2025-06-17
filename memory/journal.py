# === memory/journal.py (Supabase Native Journal + Profile Sync) ===

from datetime import datetime
from utils.supabase_client import supabase
from supabase_profile_utils import fetch_or_create_user_profile, update_user_profile_supabase

DEFAULT_EMAIL = "default_user@example.com"

def get_user_id(email):
    """Fetch the user's ID from Supabase based on their email."""
    resp = supabase.table("user_profiles").select("id").eq("email", email).execute()
    return resp.data[0]["id"] if resp.data else None

def log_entry(entry, email=DEFAULT_EMAIL):
    """Log a cannabis experience entry and update the user's Supabase profile."""
    entry.setdefault("timestamp", datetime.utcnow().isoformat())
    user_id = get_user_id(email)
    if not user_id:
        return

    # Store the journal entry
    supabase.table("journals").insert({
        "entry": entry,
        "user_id": user_id
    }).execute()

    # Update user profile with strains and effects
    profile = fetch_or_create_user_profile(email)
    strain = entry.get("strain", "").strip()
    if strain:
        profile.setdefault("past_strains", [])
        if strain not in profile["past_strains"]:
            profile["past_strains"].append(strain)

    for effect in entry.get("effects_felt", []):
        profile.setdefault("logged_effects", [])
        if effect and effect not in profile["logged_effects"]:
            profile["logged_effects"].append(effect)

    update_user_profile_supabase(email, profile)

    # Signal refresh if running in Streamlit context
    try:
        import streamlit as st
        st.session_state["refresh_profile"] = True
    except:
        pass

def get_reinforcement_boost(strain, profile):
    return float(profile.get("reinforcement", {}).get(strain, 0.0))

def adjust_reinforcement_score(profile, strain, feedback):
    profile.setdefault("reinforcement", {})
    delta = 1.0 if feedback == "positive" else -1.0
    current = profile["reinforcement"].get(strain, 0.0)
    profile["reinforcement"][strain] = round(current + delta, 2)
    update_user_profile_supabase(profile.get("email", DEFAULT_EMAIL), profile)
