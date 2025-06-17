# === memory/journal.py (Final Fixed Supabase Sync Version) ===

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

    # Pull existing profile
    profile = fetch_or_create_user_profile(email)

    # === Update strain + effect history
    strain = entry.get("strain", "").strip()
    profile.setdefault("past_strains", [])
    if strain and strain not in profile["past_strains"]:
        profile["past_strains"].append(strain)

    for effect in entry.get("effects_felt", []):
        profile.setdefault("logged_effects", [])
        if effect and effect not in profile["logged_effects"]:
            profile["logged_effects"].append(effect)

    # === Force valid JSON types
    profile["past_strains"] = list(set(profile.get("past_strains", [])))
    profile["logged_effects"] = list(set(profile.get("logged_effects", [])))

    update_user_profile_supabase(email, profile)

    # Signal Streamlit to refresh profile if running interactively
    try:
        import streamlit as st
        st.session_state["refresh_profile"] = True
    except:
        pass

def get_reinforcement_boost(strain, profile):
    return float(profile.get("reinforcement", {}).get(strain, 0.0))

def adjust_reinforcement_score(profile, strain, feedback, email=DEFAULT_EMAIL):
    profile.setdefault("reinforcement", {})
    delta = 1.0 if feedback == "positive" else -1.0
    current = profile["reinforcement"].get(strain, 0.0)
    profile["reinforcement"][strain] = round(current + delta, 2)

    # Make sure reinforcement and other fields are saved properly
    profile["reinforcement"] = dict(profile.get("reinforcement", {}))
    update_user_profile_supabase(email, profile)
