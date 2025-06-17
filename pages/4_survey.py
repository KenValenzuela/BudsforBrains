# === pages/4_survey.py (Supabase-Integrated & Stable Survey) ===

import streamlit as st
import os
import numpy as np
import pandas as pd
import faiss
from dotenv import load_dotenv
from openai import OpenAI
from supabase_profile_utils import fetch_or_create_user_profile, update_user_profile_supabase

# === Path Setup ===
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FAISS_INDEX_PATH = os.path.join(ROOT_DIR, "vector_store", "index.faiss")
DOCS_METADATA_PATH = os.path.join(ROOT_DIR, "vector_store", "docs_metadata.pkl")

# === Load environment and OpenAI ===
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Load Metadata + FAISS Index ===
metadata = pd.read_pickle(DOCS_METADATA_PATH)
if isinstance(metadata, list):
    metadata = pd.DataFrame(metadata)
index = faiss.read_index(FAISS_INDEX_PATH)

# === Embedding + Search ===
def get_embedding(text, model="text-embedding-3-small"):
    try:
        response = client.embeddings.create(input=[text], model=model)
        return np.array(response.data[0].embedding).astype("float32")
    except Exception as e:
        st.error(f"Embedding failed: {e}")
        return None

def search_index(query_embedding, top_k=5):
    D, I = index.search(np.array([query_embedding]), top_k)
    results = metadata.iloc[I[0]].copy()
    results["score"] = D[0]
    return results

# === UI Config ===
st.set_page_config(page_title="Find Your Strain", page_icon="🌿")
st.title("🌿 Budtender Survey")

# === Require Auth ===
if "user" not in st.session_state:
    st.error("🔐 Please log in first from the Login page.")
    st.stop()

user_email = st.session_state["user"].user.email
profile = fetch_or_create_user_profile(user_email)
if not profile:
    st.error("❌ Could not load your profile.")
    st.stop()

# === Survey UI ===
st.caption("Answer a few quick questions to help personalize your strain recommendations.")

with st.form("budtender_survey"):
    desired_effects = st.multiselect("What effects are you hoping for?", [
        "Relaxed", "Euphoric", "Focused", "Creative", "Uplifted", "Sleepy", "Energetic"
    ], default=profile.get("desired_effects", []))

    avoid_effects = st.multiselect("Any effects you'd like to avoid?", [
        "Anxiety", "Dry Mouth", "Couch-lock", "Paranoia", "Grogginess", "None"
    ], default=profile.get("avoid_effects", []))

    preferred_aromas = st.multiselect("Preferred flavors or aromas?", [
        "Fruity", "Earthy", "Citrus", "Sweet", "Herbal", "Spicy", "No Preference"
    ], default=[x for x in profile.get("preferred_aromas", []) if x in [
        "Fruity", "Earthy", "Citrus", "Sweet", "Herbal", "Spicy", "No Preference"]])

    usage_context = st.radio("What are you using it for?", [
        "Sleep", "Socializing", "Focus/Work", "Creativity", "Chronic Pain", "Anxiety Relief", "General Enjoyment"
    ], index=0)

    experience = st.radio("What's your cannabis experience level?", [
        "Beginner", "Intermediate", "Experienced"
    ], index=0)

    time_of_day = st.selectbox("When do you usually consume?", [
        "Morning", "Afternoon", "Evening", "Late Night"
    ], index=2)

    cannabinoid_pref = st.radio("Do you have a cannabinoid preference?", [
        "High THC", "High CBD", "Balanced", "No Preference"
    ], index=0)

    medical_goals = st.multiselect("Are you trying to address any of the following?", [
        "Stress", "Insomnia", "Chronic Pain", "Appetite Loss", "Migraines", "Muscle Spasms", "None"
    ], default=profile.get("medical_goals", []))

    custom_note = st.text_area("Anything else you'd like us to consider?",
        placeholder="e.g. 'Prefer something calming but functional for work'",
        value=profile.get("custom_notes", "")
    )

    submitted = st.form_submit_button("Get My Recommendations")

# === Save + Embed + Search ===
if submitted:
    profile_text = (
        f"I'm a {experience.lower()} user usually consuming in the {time_of_day.lower()}.\n"
        f"Looking for effects like: {', '.join(desired_effects) or 'none specified'}.\n"
        f"Avoiding: {', '.join(avoid_effects) or 'nothing specific'}.\n"
        f"Preferred aromas/flavors: {', '.join(preferred_aromas) or 'no strong preference'}.\n"
        f"My cannabinoid preference is: {cannabinoid_pref}.\n"
        f"My medical goals are: {', '.join(medical_goals) or 'none'}.\n"
        f"Use case: {usage_context.lower()}.\n"
        f"Additional notes: {custom_note.strip() if custom_note else 'none'}."
    )

    profile.update({
        "summary": profile_text,
        "desired_effects": desired_effects,
        "avoid_effects": avoid_effects,
        "preferred_aromas": preferred_aromas,
        "use_case": usage_context,
        "experience": experience,
        "time_of_day": time_of_day,
        "cannabinoid_preference": cannabinoid_pref,
        "medical_goals": medical_goals,
        "custom_notes": custom_note.strip()
    })

    update_user_profile_supabase(user_email, profile)
    st.session_state["refresh_profile"] = True

    st.markdown("#### ✅ Profile Summary")
    st.code(profile_text)

    embedding = get_embedding(profile_text)
    if embedding is not None:
        results = search_index(embedding)
        st.markdown("---")
        st.markdown("### 🔍 Top Strain Matches")
        for _, row in results.iterrows():
            name = row.get("strain_name", "Unnamed Strain")
            description = row.get("content", "")[:300]
            st.markdown(f"**{name}**\n\n{description}...")

            leafly = row.get("leafly_url")
            allbud = row.get("allbud_url")
            weedmaps = row.get("weedmaps_url")

            links = []
            if leafly: links.append(f"[Leafly]({leafly})")
            if allbud: links.append(f"[AllBud]({allbud})")
            if weedmaps: links.append(f"[Weedmaps]({weedmaps})")

            if links:
                st.markdown("🔗 " + " | ".join(links))
            else:
                st.markdown("_No external links available._")

elif profile:
    st.markdown("### 👤 Current Saved Profile")
    st.json(profile)
else:
    st.info("No profile yet. Fill out the survey to get started.")

st.markdown("---")
st.markdown(
    "Thanks for sharing your preferences. Want to support this kind of personalized cannabis education? [Buy me a coffee](https://coff.ee/kenvalenzuela). ☕",
    unsafe_allow_html=True,
)
