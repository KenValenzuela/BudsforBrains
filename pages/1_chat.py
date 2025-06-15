# app/1_chat.py
import os, sys, json
import streamlit as st
import faiss
import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI

# === Setup ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from memory.user_profile import load_user_profile, update_user_profile

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INDEX_PATH = os.path.join(ROOT_DIR, "vector_store", "index.faiss")
METADATA_PATH = os.path.join(ROOT_DIR, "vector_store", "docs_metadata.pkl")
TERPENE_INFO_PATH = os.path.join(ROOT_DIR, "data", "terpene_info.json")
CANNABINOID_INFO_PATH = os.path.join(ROOT_DIR, "data", "cannabinoid_info.json")

index = faiss.read_index(INDEX_PATH)
metadata = pd.read_pickle(METADATA_PATH)
with open(TERPENE_INFO_PATH, encoding='utf-8') as f:
    terpene_info = json.load(f)
with open(CANNABINOID_INFO_PATH, encoding='utf-8') as f:
    cannabinoid_info = json.load(f)

# === Streamlit UI ===
st.set_page_config("Cannabis Assistant", layout="wide")
st.title("Cannabis Chat Assistant")

# === Sessions ===
session_list = st.session_state.get("saved_sessions", [])
session_name = st.sidebar.text_input("Session Name", value=st.session_state.get("current_session", "default"))

if st.sidebar.button("Start New Session"):
    st.session_state.current_session = session_name
    st.session_state.history = []
    st.session_state.favorites = []
    st.session_state.user_profile = load_user_profile()
    if session_name not in session_list:
        session_list.append(session_name)
        st.session_state.saved_sessions = session_list

session_key = f"session_{session_name}"
if session_key not in st.session_state:
    st.session_state[session_key] = {
        "history": [],
        "favorites": [],
        "user_profile": load_user_profile()
    }
memory = st.session_state[session_key]

# === Utility ===
@st.cache_data(show_spinner=False)
def get_embedding(text, model="text-embedding-3-small"):
    try:
        response = client.embeddings.create(input=[text], model=model)
        return np.array(response.data[0].embedding).astype("float32")
    except:
        return None

def search_index(embedding, k=5):
    D, I = index.search(np.array([embedding]), k)
    results = pd.DataFrame([metadata[i] for i in I[0]])
    results["score"] = D[0]
    return results

@st.cache_data(show_spinner=False, ttl=86400)
def scrape_leafly(url: str) -> dict:
    import re

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        box = soup.find("ul", class_="flex flex-col gap-sm")
        if not box:
            return {}

        data = {"feelings": [], "helps_with": [], "negatives": [], "terpenes": []}

        for li in box.find_all("li"):
            raw = li.get_text(separator=" ", strip=True)  # <- THE FIX
            if ":" not in raw:
                continue

            label, raw_values = raw.split(":", 1)
            label = label.strip().lower()
            raw_values = raw_values.strip()

            # Split on common separators
            values = re.split(r"[·•,;]|\\s{2,}", raw_values)
            values = [v.strip() for v in values if len(v.strip()) > 1]

            if "feelings" in label:
                data["feelings"] = values
            elif "helps with" in label:
                data["helps_with"] = values
            elif "negatives" in label:
                data["negatives"] = values
            elif "terpenes" in label:
                data["terpenes"] = values

        return data
    except Exception as e:
        return {"error": str(e)}

def build_prompt(history, question, context, profile=None, warn=None):
    memory = "\n".join([f"User: {q}\nBot: {a}" for q, a in history[-3:]])
    profile_txt = json.dumps(profile, indent=2) if profile else ""
    warning = f"\nNote: {warn}" if warn else ""
    return f"""You are a helpful cannabis assistant.

Chat History:
{memory}

User Profile:
{profile_txt}

Context:
{context}

User Question:
{question}

Explain your reasoning based on terpene and cannabinoid profiles.{warning}
Answer:"""

@st.cache_data(show_spinner=False)
def generate_response(prompt):
    try:
        chat = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return chat.choices[0].message.content.strip()
    except Exception as e:
        return f"OpenAI error: {e}"

# === Starters ===
st.markdown("#### Get Started")
st.caption("Choose a guided question or ask your own.")
starters = [
    "What’s the difference between indica and sativa?",
    "What strain would help me sleep but not leave me groggy?",
    "Explain the entourage effect with examples.",
    "Are there strains that reduce anxiety without couchlock?",
]
cols = st.columns(len(starters))
for i, q in enumerate(starters):
    if cols[i].button(q):
        st.session_state["pending_input"] = q

# === Main Chat ===
user_input = st.text_area("Ask your question:", value=st.session_state.pop("pending_input", ""), height=100)
if user_input:
    with st.spinner("Generating response..."):
        emb = get_embedding(user_input)
        if emb is None:
            st.error("❌ Could not generate embedding.")
        else:
            results = search_index(emb)
            context = "\n".join(results["content"].tolist())
            tried = memory["user_profile"].get("past_strains", [])
            new_strains = [r["strain_name"] for _, r in results.iterrows() if r["strain_name"] not in tried]
            warn = f"You haven't tried: {', '.join(new_strains)}." if new_strains else None

            prompt = build_prompt(memory["history"], user_input, context, memory["user_profile"], warn)
            reply = generate_response(prompt)

            st.subheader("Assistant Response")
            st.write(reply)
            st.divider()

            st.subheader("Recommended Strains")
            for i, row in results.iterrows():
                name = row["strain_name"]
                url = row.get("leafly_url")
                scraped_data = scrape_leafly(url) if url else {}

                top_terpenes = scraped_data.get("terpenes", [])
                top_terp = (top_terpenes[0] if top_terpenes else row.get("dominant_terpene", "🧪 Not available yet")).strip()
                if top_terp.lower() in ("", "unknown", "not available yet"):
                    top_terp = "🧪 Not available yet"

                display = f"[{name}]({url})" if url else name

                with st.container():
                    st.markdown(f"**{display}**")
                    cols = st.columns(4)
                    cols[0].markdown("**Top Terpenes:**\n" + "\n".join([f"🧪 {x}" for x in top_terpenes]) if top_terpenes else "**Top Terpenes:**\n_Unknown_")
                    cols[1].markdown("**Feelings:**\n" + "\n".join([f"😊 {x}" for x in scraped_data.get("feelings", [])]))
                    cols[2].markdown("**Helps With:**\n" + "\n".join([f"💊 {x}" for x in scraped_data.get("helps_with", [])]))
                    cols[3].markdown("**Negatives:**\n" + "\n".join([f"⚠️ {x}" for x in scraped_data.get("negatives", [])]))

                with st.expander("Read more"):
                    st.caption(row["content"])
                    if st.button(f"Favorite {name}", key=f"fav_{i}"):
                        if name not in memory["favorites"]:
                            memory["favorites"].append(name)
                        if name not in tried:
                            tried.append(name)
                            memory["user_profile"]["past_strains"] = tried
                            update_user_profile(memory["user_profile"])
                        st.success(f"{name} added to favorites.")

            memory["history"].append((user_input, reply))

# === Sidebar ===
st.sidebar.title("Session Overview")

st.sidebar.subheader("Survey & Tools")
st.sidebar.page_link("pages/4_survey.py", label="Go to Survey Page")

st.sidebar.subheader("Favorites")
if memory["favorites"]:
    st.sidebar.write(memory["favorites"])
else:
    st.sidebar.caption("No favorites yet.")

st.sidebar.subheader("Recent Q&A")
for q, a in memory["history"][-5:]:
    st.sidebar.markdown(f"**Q:** {q}\n*A:** {a[:80]}...")

st.sidebar.subheader("User Profile")
if memory["user_profile"]:
    st.sidebar.code(json.dumps(memory["user_profile"], indent=2))

if st.sidebar.button("Reset Profile + Session"):
    update_user_profile({}, merge=False)
    memory.update({"history": [], "favorites": [], "user_profile": {}})
    st.rerun()

st.sidebar.subheader("Glossary")
with st.sidebar.expander("Terpenes"):
    for k, v in terpene_info.items():
        st.markdown(f"**{k}** — {', '.join(v.get('effects', []))}")
with st.sidebar.expander("Cannabinoids"):
    for k, v in cannabinoid_info.items():
        st.markdown(f"**{k}** — {'Psychoactive' if v.get('psychoactive') else 'Non-psychoactive'}")
