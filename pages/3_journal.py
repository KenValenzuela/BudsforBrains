# === pages/3_journal.py (Strain Journal UI + Supabase Logging) ===

import streamlit as st
import pandas as pd
from datetime import datetime
from memory.journal import log_entry, get_user_id
from utils.supabase_client import supabase

st.set_page_config("📓 Strain Journal", layout="wide")
st.title("📓 Strain Journal")
st.markdown("Use this page to **log your cannabis experiences**, track how you feel, and refine your personal profile.")

# === Require Auth ===
if "user" not in st.session_state:
    st.error("🔐 Please log in first from the Login page.")
    st.stop()

user_email = st.session_state["user"].user.email

# === Load Existing Entries ===
def load_journal(email):
    user_id = get_user_id(email)
    if not user_id:
        return []
    response = supabase.table("journals").select("entry").eq("user_id", user_id).order("created_at", desc=True).execute()
    return [item["entry"] for item in response.data] if response.data else []

journal_entries = load_journal(user_email)

# === Entry Form ===
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

    submitted = st.form_submit_button("📘 Save Entry")

    if submitted and strain.strip():
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

        log_entry(new_entry, email=user_email)
        journal_entries.insert(0, new_entry)
        st.success(f"✅ Entry added for **{strain}** on {new_entry['date']}")

# === Journal Log Viewer ===
if journal_entries:
    st.markdown("### 📘 Logged Entries")
    df = pd.DataFrame(journal_entries)
    df["effects_felt"] = df["effects_felt"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    df_sorted = df.sort_values("timestamp", ascending=False).reset_index(drop=True)

    st.dataframe(df_sorted, use_container_width=True)

    st.download_button(
        label="⬇️ Download CSV",
        data=df_sorted.to_csv(index=False),
        file_name="strain_journal.csv",
        mime="text/csv"
    )
else:
    st.info("No entries yet. Use the form above to log your first experience.")

st.markdown("---")
st.markdown(
    "This journaling system was built to help people track what works for them. "
    "If it helped you, [buy me a coffee](https://coff.ee/kenvalenzuela). ☕",
    unsafe_allow_html=True,
)
