# === pages/3_journal.py (Supabase + Auth) ===
import streamlit as st
import pandas as pd
from datetime import datetime
from memory.user_profile import load_user_profile, update_user_profile
from utils.supabase_client import supabase

st.set_page_config("📓 Strain Journal", layout="wide")
st.title("📓 Strain Journal")
st.markdown("Use this page to **log your cannabis experiences**, track how you feel, and refine your personal profile.")

# === Require Auth ===
if "user" not in st.session_state:
    st.error("🔐 Please log in first from the Login page.")
    st.stop()

user_email = st.session_state["user"].user.email

# === Get user ID safely ===
def get_user_id(email):
    resp = supabase.table("user_profiles").select("id").eq("email", email).execute()
    return resp.data[0]["id"] if resp.data else None

# === Load journal entries from Supabase ===
def load_journal(email):
    user_id = get_user_id(email)
    if user_id is None:
        return []
    response = supabase.table("journals").select("entry").eq("user_id", user_id).order("created_at", desc=True).execute()
    return [item["entry"] for item in response.data] if response.data else []

# === Recompute profile from journal ===
def recompute_profile(entries):
    effects = set()
    strains = set()
    for entry in entries:
        for e in entry.get("effects_felt", []):
            effects.add(e.strip())
        strains.add(entry.get("strain", "").strip())
    return {
        "logged_effects": sorted(effects),
        "past_strains": sorted(strains)
    }

journal_entries = load_journal(user_email)
profile = load_user_profile(user_email)

# === Manual Entry Form ===
st.markdown("### ➕ Add New Experience")
with st.form("manual_entry_form"):
    col1, col2, col3 = st.columns([3, 1.5, 1.5])
    with col1:
        strain = st.text_input("Strain Name", placeholder="e.g., Blue Dream")
    with col2:
        date_used = st.date_input("Date Used", value=datetime.today())
    with col3:
        time_used = st.time_input("Time Used", value=datetime.now().time())

    effects_felt = st.text_area("Effects Felt (comma-separated)", placeholder="Relaxed, Euphoric, Talkative")
    dosage = st.text_input("Dosage", placeholder="e.g., 0.25g, 5mg edible")
    notes = st.text_area("Additional Notes", placeholder="Describe the setting, activities, or other observations...")

    submit = st.form_submit_button("📘 Save Entry")
    if submit and strain.strip():
        parsed_effects = [e.strip() for e in effects_felt.split(",") if e.strip()]
        new_entry = {
            "strain": strain.strip(),
            "date": date_used.strftime("%Y-%m-%d"),
            "time": time_used.strftime("%H:%M"),
            "effects_felt": parsed_effects,
            "dosage": dosage.strip(),
            "notes": notes.strip(),
            "timestamp": datetime.utcnow().isoformat()
        }

        user_id = get_user_id(user_email)
        if user_id:
            supabase.table("journals").insert({"user_id": user_id, "entry": new_entry}).execute()
            journal_entries.insert(0, new_entry)
            updated_profile = recompute_profile(journal_entries)
            profile.update(updated_profile)
            update_user_profile(profile, email=user_email)
            st.success(f"✅ Entry added for **{strain}** on {new_entry['date']}")
        else:
            st.error("❌ Could not find a valid user ID. Please make sure the profile exists.")

# === Display and Edit Log Entries (read-only for now) ===
if journal_entries:
    st.markdown("### 📘 Logged Entries")
    df = pd.DataFrame(journal_entries)
    df_display = df.copy()
    df_display["effects_felt"] = df_display["effects_felt"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

    st.dataframe(df_display.sort_values("timestamp", ascending=False).reset_index(drop=True), use_container_width=True)

    st.download_button(
        "⬇️ Download CSV", df_display.to_csv(index=False),
        file_name="strain_journal.csv", mime="text/csv"
    )
else:
    st.info("No entries yet. Use the form above to log your first experience.")