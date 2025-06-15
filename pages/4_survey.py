# pages/4_Survey.py
import streamlit as st
import os
import json
import numpy as np
import pandas as pd
import faiss
from dotenv import load_dotenv
from openai import OpenAI

# === Path Setup ===
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROFILE_PATH = os.path.join(ROOT_DIR, "memory", "user_profile.json")
FAISS_INDEX_PATH = os.path.join(ROOT_DIR, "vector_store", "index.faiss")
DOCS_METADATA_PATH = os.path.join(ROOT_DIR, "vector_store", "docs_metadata.pkl")

# === Load environment and OpenAI ===
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Load Metadata + FAISS Index ===
metadata = pd.read_pickle(DOCS_METADATA_PATH)
if isinstance(metadata, list):  # Convert to DataFrame if needed
    metadata = pd.DataFrame(metadata)

index = faiss.read_index(FAISS_INDEX_PATH)

# === Load or Save Profile JSON ===
def load_profile():
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r") as f:
            return json.load(f)
    return {}

def save_profile(profile):
    with open(PROFILE_PATH, "w") as f:
        json.dump(profile, f, indent=2)

# === Embedding Function ===
def get_embedding(text, model="text-embedding-3-small"):
    try:
        response = client.embeddings.create(input=[text], model=model)
        return np.array(response.data[0].embedding).astype("float32")
    except Exception as e:
        st.error(f"Embedding failed: {e}")
        return None

# === FAISS Search ===
def search_index(query_embedding, top_k=5):
    D, I = index.search(np.array([query_embedding]), top_k)
    idx_list = I[0].tolist()
    results = metadata.iloc[idx_list].copy()
    results["score"] = D[0]
    return results

# === Streamlit Page Config ===
st.set_page_config(page_title="Find Your Strain", page_icon="🌿")
st.title("🌿 Budtender Survey")
st.caption("Answer a few quick questions to help personalize your strain recommendations.")

# === Survey ===
profile = load_profile()

with st.form("budtender_survey"):
    desired_effects = st.multiselect(
        "What effects are you hoping for?",
        ["Relaxed", "Euphoric", "Focused", "Creative", "Uplifted", "Sleepy", "Energetic"]
    )

    avoid_effects = st.multiselect(
        "Any effects you'd like to avoid?",
        ["Anxiety", "Dry Mouth", "Couch-lock", "Paranoia", "Grogginess", "None"]
    )

    preferred_aromas = st.multiselect(
        "Preferred flavors or aromas?",
        ["Fruity", "Earthy", "Citrus", "Sweet", "Herbal", "Spicy", "No Preference"]
    )

    usage_context = st.radio(
        "What are you using it for?",
        ["Sleep", "Socializing", "Focus/Work", "Creativity", "Chronic Pain", "Anxiety Relief", "General Enjoyment"]
    )

    experience = st.radio("What's your cannabis experience level?", ["Beginner", "Intermediate", "Experienced"])
    time_of_day = st.selectbox("When do you usually consume?", ["Morning", "Afternoon", "Evening", "Late Night"])

    submitted = st.form_submit_button("Get My Recommendations")

# === If Submitted ===
if submitted:
    # Build natural language summary
    profile_text = (
        f"I'm a {experience.lower()} user usually consuming in the {time_of_day.lower()}.\n"
        f"I'm looking for effects like {', '.join(desired_effects) or 'none specified'}.\n"
        f"I want to avoid {', '.join(avoid_effects) if avoid_effects else 'nothing in particular'}.\n"
        f"I prefer aromas/flavors like {', '.join(preferred_aromas) if preferred_aromas else 'no specific preference'}.\n"
        f"My primary use case is {usage_context.lower()}."
    )

    # Save profile
    profile.update({
        "summary": profile_text,
        "desired_effects": desired_effects,
        "avoid_effects": avoid_effects,
        "preferred_aromas": preferred_aromas,
        "use_case": usage_context,
        "experience": experience,
        "time_of_day": time_of_day
    })
    save_profile(profile)

    # Show summary
    st.markdown("#### ✅ Profile Summary")
    st.code(profile_text)

    # Get embedding and search for matches
    embedding = get_embedding(profile_text)
    if embedding is not None:
        results = search_index(embedding, top_k=5)
        st.markdown("---")
        st.markdown("### 🔍 Top Strain Matches")
        for _, row in results.iterrows():
            st.markdown(f"""
**{row.get("strain_name", "Unnamed Strain")}**  
{row.get("content", "")[:300]}...  
[Read more]({row.get("url", "#")})
""")

# === Load existing profile for review ===
elif profile:
    st.markdown("### 👤 Current Saved Profile")
    st.json(profile)
else:
    st.info("No profile yet. Fill out the survey to get started.")
