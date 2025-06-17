# === pages/5_profile.py (Refactored with Auto Refresh + Supabase Integration) ===
import streamlit as st
import pandas as pd
from supabase_profile_utils import fetch_or_create_user_profile, update_user_profile_supabase

st.set_page_config(page_title="🧬 Profile Dashboard", layout="wide")
st.title("🧬 Your Personal Cannabis Profile")

# === Require Auth ===
if "user" not in st.session_state:
    st.error("🔐 Please log in first from the Login page.")
    st.stop()

user_email = st.session_state["user"].user.email

# === Refresh Logic ===
if "refresh_profile" not in st.session_state:
    st.session_state["refresh_profile"] = True

if st.session_state["refresh_profile"]:
    profile = fetch_or_create_user_profile(user_email)
    st.session_state["cached_profile"] = profile
    st.session_state["refresh_profile"] = False
else:
    profile = st.session_state.get("cached_profile", fetch_or_create_user_profile(user_email))

# === Manual Refresh Button ===
if st.button("🔄 Refresh Dashboard"):
    st.session_state["refresh_profile"] = True
    st.experimental_rerun()

# === Profile Edit Form ===
st.markdown("## 🎯 Personal Preferences")
with st.form("update_profile"):
    col1, col2 = st.columns(2)

    with col1:
        desired_options = [
            "Relaxed", "Energetic", "Uplifted", "Euphoric", "Focused",
            "Creative", "Happy", "Sleepy", "Hungry", "Talkative"
        ]
        desired_effects = st.multiselect(
            "What effects are you looking for?",
            options=desired_options,
            default=[x for x in profile.get("desired_effects", []) if x in desired_options]
        )

    with col2:
        aroma_options = [
            "Citrus", "Earthy", "Berry", "Pine", "Sweet",
            "Herbal", "Skunky", "Spicy", "Tropical", "Diesel"
        ]
        preferred_aromas = st.multiselect(
            "What aromas or flavors do you enjoy?",
            options=aroma_options,
            default=[x for x in profile.get("preferred_aromas", []) if x in aroma_options]
        )

    notes = st.text_area("📝 Additional Notes", value=profile.get("notes", ""))

    submitted = st.form_submit_button("💾 Save Preferences")
    if submitted:
        profile["desired_effects"] = desired_effects
        profile["preferred_aromas"] = preferred_aromas
        profile["notes"] = notes
        update_user_profile_supabase(user_email, profile)
        st.success("✅ Profile saved.")
        st.session_state["refresh_profile"] = True
        st.experimental_rerun()

# === Profile Dashboard ===
st.markdown("---")
st.header("📊 Profile Dashboard")

logged_effects = profile.get("logged_effects", [])
past_strains = profile.get("past_strains", [])

if logged_effects or past_strains:
    total_strains = len(set(past_strains))
    total_effects = len(set(logged_effects))

    cols = st.columns(3)
    cols[0].metric("🧬 Effects Logged", total_effects)
    cols[1].metric("🌿 Unique Strains", total_strains)
    cols[2].metric("📘 Journal Entries", len(past_strains))

    if logged_effects:
        st.markdown("### 📈 Effects Frequency")
        st.bar_chart(pd.Series(logged_effects).value_counts().sort_values(ascending=True))

    if past_strains:
        st.markdown("### 🌿 Most Tried Strains")
        df = pd.Series(past_strains).value_counts().reset_index()
        df.columns = ["Strain", "Times Used"]
        st.dataframe(df, use_container_width=True)
else:
    st.info("Your journal will populate this dashboard over time.")

st.caption("🔄 This dashboard updates automatically after journal or survey edits.")
