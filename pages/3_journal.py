# pages/3_Journal.py
import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

# === Setup Paths ===
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
JOURNAL_PATH = os.path.join(ROOT_DIR, "memory", "journal.json")

# === Load or Initialize Journal ===
if os.path.exists(JOURNAL_PATH):
    with open(JOURNAL_PATH, "r", encoding="utf-8") as f:
        journal_entries = json.load(f)
else:
    journal_entries = []

# === Page Setup ===
st.title("Strain Journal")
st.markdown("Log your experiences with different strains to track what works for you.")

# === Log Form ===
with st.form("log_form"):
    strain = st.text_input("Strain Name")
    date_used = st.date_input("Date Used", value=datetime.today())
    time_used = st.time_input("Time Used", value=datetime.now().time())
    effects_felt = st.text_area("Effects Felt (comma-separated)")
    dosage = st.text_input("Dosage (e.g., 0.25g, 5mg edible)")
    notes = st.text_area("Additional Notes")
    submitted = st.form_submit_button("Add Entry")

    if submitted and strain:
        entry = {
            "strain": strain,
            "date": date_used.strftime("%Y-%m-%d"),
            "time": time_used.strftime("%H:%M"),
            "effects_felt": [e.strip() for e in effects_felt.split(",") if e.strip()],
            "dosage": dosage,
            "notes": notes
        }
        journal_entries.append(entry)
        with open(JOURNAL_PATH, "w", encoding="utf-8") as f:
            json.dump(journal_entries, f, indent=2)
        st.success(f"Added entry for {strain} on {entry['date']}.")

# === Display Entries ===
if journal_entries:
    df = pd.DataFrame(journal_entries)
    st.markdown("### Logged Entries")
    st.dataframe(df, use_container_width=True)

    st.download_button("Download Journal as CSV", df.to_csv(index=False), file_name="strain_journal.csv",
                       mime="text/csv")
else:
    st.info("No journal entries yet. Use the form above to log your first experience.")
