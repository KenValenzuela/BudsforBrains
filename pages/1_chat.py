# === pages/1_chat.py (Supabase + Auth Integrated, Fixed) ===
import os, sys, json
import streamlit as st
import faiss
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

# === Local Imports ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from memory.journal import log_entry, get_reinforcement_boost, adjust_reinforcement_score
from scripts.strain_scraper import scrape_all_sources
from supabase_profile_utils import fetch_or_create_user_profile, update_user_profile_supabase

try:
    from chat_guard import should_answer, explain_restriction
except ImportError:
    def should_answer(text):
        keywords = ["cannabis", "weed", "strain", "terpene", "indica", "sativa", "thc", "cbd", "hybrid", "effects", "entourage"]
        return any(kw in text.lower() for kw in keywords)

    def explain_restriction():
        return (
            "🚫 This assistant only answers cannabis-related questions.\n"
            "Try asking things like:\n"
            "- What is the difference between indica and sativa?\n"
            "- What strain helps with focus?\n"
            "- How does myrcene affect the high?"
        )

# === Require Auth ===
if "user" not in st.session_state:
    st.error("🔐 Please log in first from the Login page.")
    st.stop()

user_email = st.session_state["user"].user.email

# === Environment ===
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
index = faiss.read_index(os.path.join(ROOT, "vector_store/index.faiss"))
metadata = pd.read_pickle(os.path.join(ROOT, "vector_store/docs_metadata.pkl"))

with open(os.path.join(ROOT, "data/terpene_info.json"), encoding="utf-8") as f:
    terpene_info = json.load(f)
with open(os.path.join(ROOT, "data/cannabinoid_info.json"), encoding="utf-8") as f:
    cannabinoid_info = json.load(f)

# === Load user profile ===
profile = fetch_or_create_user_profile(user_email)

# === Utility ===
def build_fallback_urls(name):
    slug = name.lower().replace(" ", "-")
    return {
        "leafly_url": f"https://www.leafly.com/strains/{slug}",
        "allbud_url": f"https://www.allbud.com/marijuana-strains/indica-dominant-hybrid/{slug}",
        "weedmaps_url": f"https://weedmaps.com/strains/{slug}"
    }

# === Page Setup ===
st.set_page_config("Cannabis Assistant", layout="wide")
st.title("🌿 Cannabis Chat Assistant")

# === Session State ===
session_name = st.sidebar.text_input("Session Name", value=st.session_state.get("current_session", "default"))
if st.sidebar.button("Start New Session"):
    st.session_state["current_session"] = session_name
    st.session_state[f"session_{session_name}"] = {"history": [], "user_profile": profile}

session_key = f"session_{session_name}"
if session_key not in st.session_state:
    st.session_state[session_key] = {"history": [], "user_profile": profile}
memory = st.session_state[session_key]
st.session_state.setdefault("last_question", "")
st.session_state.setdefault("last_answer", "")

# === Embedding and Search ===
@st.cache_data(show_spinner=False)
def get_embedding(text, model="text-embedding-3-small"):
    try:
        rsp = client.embeddings.create(input=[text], model=model)
        return np.array(rsp.data[0].embedding).astype("float32")
    except Exception as e:
        st.error(f"Embedding error: {e}")
        return None

def search_index(emb, k=5):
    D, I = index.search(np.array([emb]), k)
    results = pd.DataFrame([metadata[i] for i in I[0]])
    results["score"] = D[0]

    effs = set(memory["user_profile"].get("desired_effects", []))
    aromas = set(memory["user_profile"].get("preferred_aromas", []))

    def boost(row):
        desc = row.get("content", "").lower()
        base = sum(e.lower() in desc for e in effs) * 0.5 + sum(a.lower() in desc for a in aromas) * 0.3
        reinforce = get_reinforcement_boost(row.get("strain_name"), memory["user_profile"])
        return base + reinforce

    results["adjusted_score"] = results.apply(boost, axis=1)
    return results.sort_values("adjusted_score", ascending=False)

# === Prompt Builder ===
def build_prompt(history, question, context, profile, warn=None):
    memory_log = "\n".join([f"User: {q}\nBot: {a}" for q, a in history[-3:]])
    return f"""You are a helpful cannabis assistant.

Chat History:
{memory_log}

User Profile:
{json.dumps(profile, indent=2)}

Context:
{context}

User Question:
{question}

Explain your reasoning based on terpene and cannabinoid profiles.{f'\nNote: {warn}' if warn else ''}
Answer:"""

@st.cache_data(show_spinner=False)
def generate_response(prompt):
    rsp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return rsp.choices[0].message.content.strip()

# === Starter Prompts ===
st.markdown("#### 🧠 Get Started")
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

# === Chat Input ===
user_input = st.text_area("💬 Ask your question:", value=st.session_state.pop("pending_input", ""), height=100)

if user_input and not should_answer(user_input):
    st.warning(explain_restriction())
    st.stop()

# === Generate Response ===
if user_input:
    with st.spinner("🔎 Thinking..."):
        emb = get_embedding(user_input)
        if emb is not None:
            results = search_index(emb)
            context = "\n".join(results["content"].tolist())
            tried = memory["user_profile"].get("past_strains", [])
            new_strains = [r["strain_name"] for _, r in results.iterrows() if r["strain_name"] not in tried]
            warn = ", ".join(new_strains) if new_strains else None

            prompt = build_prompt(memory["history"], user_input, context, memory["user_profile"], warn)
            reply = generate_response(prompt)

            st.session_state["last_question"] = user_input
            st.session_state["last_answer"] = reply

# === Response Display ===
if st.session_state["last_question"] and st.session_state["last_answer"]:
    st.subheader("🧠 Assistant Response")
    st.markdown(f"**You:** {st.session_state['last_question']}")
    st.markdown(f"**Assistant:** {st.session_state['last_answer']}")
    st.divider()

    st.subheader("🌿 Recommended Strains")
    emb = get_embedding(st.session_state["last_question"])
    results = search_index(emb)

    for i, row in results.iterrows():
        name = row["strain_name"]
        scraped = scrape_all_sources(
            row.get("leafly_url"),
            row.get("allbud_url"),
            row.get("weedmaps_url")
        )
        top_terps = scraped.get("terpenes", []) or [row.get("dominant_terpene", "Unknown")]

        urls = {
            "leafly_url": row.get("leafly_url"),
            "allbud_url": row.get("allbud_url"),
            "weedmaps_url": row.get("weedmaps_url")
        }
        if not any(urls.values()):
            urls = build_fallback_urls(name)

        source_links = " | ".join(filter(None, [
            f"[Leafly]({urls['leafly_url']})" if urls.get("leafly_url") else "",
            f"[AllBud]({urls['allbud_url']})" if urls.get("allbud_url") else "",
            f"[Weedmaps]({urls['weedmaps_url']})" if urls.get("weedmaps_url") else ""
        ]))

        with st.container():
            st.markdown(f"**{name}** — Dominant Terpene: {top_terps[0]}")
            if source_links:
                st.markdown(f"🔗 Sources: {source_links}")

            cols = st.columns(4)
            cols[0].markdown("**Top Terpenes:**\n" + "\n".join(top_terps))
            cols[1].markdown("**Feelings:**\n" + "\n".join(scraped.get("feelings", [])))
            cols[2].markdown("**Helps With:**\n" + "\n".join(scraped.get("helps_with", [])))
            cols[3].markdown("**Negatives:**\n" + "\n".join(scraped.get("negatives", [])))

            with st.form(key=f"feedback_form_{name}_{i}", clear_on_submit=False):
                feedback = st.radio(
                    "How was this recommendation?",
                    ["None", "👍", "👎"],
                    index=0,
                    horizontal=True,
                    key=f"radio_{name}_{i}"
                )
                submitted = st.form_submit_button("📘 Log This")
                if submitted and feedback != "None":
                    log_entry({
                        "timestamp": datetime.utcnow().isoformat(),
                        "strain": name,
                        "question": st.session_state["last_question"],
                        "answer": st.session_state["last_answer"],
                        "feedback": "positive" if feedback == "👍" else "negative",
                        "effects_felt": scraped.get("feelings", [])
                    }, email=user_email)
                    adjust_reinforcement_score(memory["user_profile"], name, "positive" if feedback == "👍" else "negative")
                    st.success(f"✅ Logged feedback and updated score for {name}.")

    if (st.session_state["last_question"], st.session_state["last_answer"]) not in memory["history"]:
        memory["history"].append((st.session_state["last_question"], st.session_state["last_answer"]))

# === Update Profile in Supabase ===
update_user_profile_supabase(user_email, memory["user_profile"])

# === Sidebar ===
st.sidebar.title("📂 Session Overview")
st.sidebar.page_link("pages/3_journal.py", label="📘 Journal")
st.sidebar.page_link("pages/5_profile.py", label="🧬 Profile Dashboard")

st.sidebar.subheader("📜 Recent Q&A")
for q, a in memory["history"][-5:]:
    st.sidebar.markdown(f"**Q:** {q}\n*A:** {a[:80]}...")

st.sidebar.subheader("🧬 Profile")
st.sidebar.code(json.dumps(memory["user_profile"], indent=2))

st.markdown("---")
st.markdown(
    "If the assistant helped you learn something today, [buy me a coffee](https://coff.ee/kenvalenzuela) so I can keep improving it. ☕",
    unsafe_allow_html=True,
)
